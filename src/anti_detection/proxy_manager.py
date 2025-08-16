"""
Proxy Manager for Facebook Video Crawler System
Provides proxy IP pool management, health checking, and rotation strategies
"""

import asyncio
import aiohttp
import time
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger
from ..utils.config_manager import config


class ProxyType(Enum):
    """Proxy types"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class ProxyRotationStrategy(Enum):
    """Proxy rotation strategies"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    FAILOVER = "failover"
    WEIGHTED = "weighted"


@dataclass
class ProxyInfo:
    """Proxy information container"""
    url: str
    proxy_type: ProxyType
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    speed: Optional[float] = None
    uptime: Optional[float] = None
    last_check: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    is_active: bool = True
    is_working: bool = True
    response_time: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def score(self) -> float:
        """Calculate proxy score based on performance"""
        if not self.is_working:
            return 0.0
        
        score = self.success_rate * 0.4  # 40% weight for success rate
        
        if self.response_time:
            # Lower response time = higher score
            response_score = max(0, 1 - (self.response_time / 10.0))  # Normalize to 0-1
            score += response_score * 0.3  # 30% weight for response time
        
        if self.uptime:
            # Higher uptime = higher score
            uptime_score = min(1.0, self.uptime / 100.0)  # Normalize to 0-1
            score += uptime_score * 0.2  # 20% weight for uptime
        
        if self.speed:
            # Higher speed = higher score
            speed_score = min(1.0, self.speed / 100.0)  # Normalize to 0-1
            score += speed_score * 0.1  # 10% weight for speed
        
        return score


class ProxyManager:
    """Manages proxy IP pool and rotation"""
    
    def __init__(self):
        """Initialize proxy manager"""
        self.logger = get_logger("proxy_manager")
        self.config = config.get_anti_detection_config().get("proxy", {})
        
        # Proxy pool
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self.rotation_strategy = ProxyRotationStrategy(
            self.config.get("rotation_strategy", "round_robin")
        )
        
        # Health check settings
        self.test_url = self.config.get("test_url", "https://httpbin.org/ip")
        self.test_interval = self.config.get("test_interval", 300)  # 5 minutes
        self.health_check_timeout = 10
        
        # Load proxies
        self._load_proxies()
        
        # Start health check loop
        self._start_health_check_loop()
        
        self.logger.info("Proxy manager initialized", extra_fields={
            "proxy_count": len(self.proxies),
            "rotation_strategy": self.rotation_strategy.value
        })
    
    def _load_proxies(self) -> None:
        """Load proxies from configuration"""
        proxy_list = config.get_proxy_list()
        
        for proxy_url in proxy_list:
            try:
                proxy_info = self._parse_proxy_url(proxy_url)
                if proxy_info:
                    self.proxies.append(proxy_info)
            except Exception as e:
                self.logger.warning(f"Failed to parse proxy URL {proxy_url}: {e}")
        
        if not self.proxies:
            self.logger.warning("No proxies loaded from configuration")
    
    def _parse_proxy_url(self, proxy_url: str) -> Optional[ProxyInfo]:
        """Parse proxy URL and extract information"""
        try:
            if proxy_url.startswith("http://"):
                proxy_type = ProxyType.HTTP
                url = proxy_url
            elif proxy_url.startswith("https://"):
                proxy_type = ProxyType.HTTPS
                url = proxy_url
            elif proxy_url.startswith("socks4://"):
                proxy_type = ProxyType.SOCKS4
                url = proxy_url
            elif proxy_url.startswith("socks5://"):
                proxy_type = ProxyType.SOCKS5
                url = proxy_url
            else:
                # Assume HTTP proxy
                proxy_type = ProxyType.HTTP
                url = f"http://{proxy_url}"
            
            # Extract username and password if present
            username = None
            password = None
            
            if "@" in url:
                auth_part, server_part = url.split("@", 1)
                protocol_part = url.split("://")[0] + "://"
                auth_info = auth_part.replace(protocol_part, "")
                if ":" in auth_info:
                    username, password = auth_info.split(":", 1)
                url = f"{protocol_part}{server_part}"
            
            return ProxyInfo(
                url=url,
                proxy_type=proxy_type,
                username=username,
                password=password
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse proxy URL {proxy_url}: {e}")
            return None
    
    def _start_health_check_loop(self) -> None:
        """Start background health check loop"""
        async def health_check_loop():
            while True:
                try:
                    await asyncio.sleep(self.test_interval)
                    await self._check_all_proxies()
                except Exception as e:
                    self.logger.error(f"Health check loop error: {e}")
        
        # Start health check loop in background
        asyncio.create_task(health_check_loop())
    
    async def _check_all_proxies(self) -> None:
        """Check health of all proxies"""
        self.logger.info("Starting proxy health check")
        
        tasks = []
        for proxy in self.proxies:
            if proxy.is_active:
                task = asyncio.create_task(self._check_proxy_health(proxy))
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update proxy scores
        self._update_proxy_scores()
        
        self.logger.info("Proxy health check completed")
    
    async def _check_proxy_health(self, proxy: ProxyInfo) -> None:
        """Check health of a single proxy"""
        start_time = time.time()
        
        try:
            # Prepare proxy configuration
            proxy_config = {
                "proxy": proxy.url
            }
            
            if proxy.username and proxy.password:
                proxy_config["proxy_auth"] = aiohttp.BasicAuth(
                    proxy.username, proxy.password
                )
            
            # Test proxy
            timeout = aiohttp.ClientTimeout(total=self.health_check_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.test_url, proxy=proxy.url) as response:
                    if response.status == 200:
                        # Success
                        response_time = time.time() - start_time
                        proxy.response_time = response_time
                        proxy.success_count += 1
                        proxy.is_working = True
                        proxy.last_check = datetime.now()
                        
                        # Try to extract IP information from response
                        try:
                            data = await response.json()
                            if "origin" in data:
                                self.logger.debug(f"Proxy {proxy.url} working, IP: {data['origin']}")
                        except:
                            pass
                    else:
                        # Failure
                        proxy.failure_count += 1
                        proxy.is_working = False
                        proxy.last_check = datetime.now()
                        self.logger.debug(f"Proxy {proxy.url} failed with status {response.status}")
            
        except asyncio.TimeoutError:
            proxy.failure_count += 1
            proxy.is_working = False
            proxy.last_check = datetime.now()
            self.logger.debug(f"Proxy {proxy.url} timeout")
            
        except Exception as e:
            proxy.failure_count += 1
            proxy.is_working = False
            proxy.last_check = datetime.now()
            self.logger.debug(f"Proxy {proxy.url} error: {e}")
    
    def _update_proxy_scores(self) -> None:
        """Update proxy scores and sort by performance"""
        # Sort proxies by score (descending)
        self.proxies.sort(key=lambda p: p.score, reverse=True)
        
        # Log top performing proxies
        top_proxies = [p for p in self.proxies[:3] if p.is_working]
        if top_proxies:
            self.logger.debug("Top performing proxies", extra_fields={
                "top_proxies": [{"url": p.url, "score": p.score, "success_rate": p.success_rate} for p in top_proxies]
            })
    
    def get_proxy(self, region: Optional[str] = None) -> Optional[ProxyInfo]:
        """
        Get next proxy based on rotation strategy
        
        Args:
            region: Optional region filter
            
        Returns:
            ProxyInfo or None if no working proxy available
        """
        working_proxies = [p for p in self.proxies if p.is_working and p.is_active]
        
        if not working_proxies:
            self.logger.warning("No working proxies available")
            return None
        
        # Filter by region if specified
        if region:
            region_proxies = [p for p in working_proxies if p.country == region]
            if region_proxies:
                working_proxies = region_proxies
            else:
                self.logger.warning(f"No proxies available for region {region}")
        
        if not working_proxies:
            return None
        
        # Select proxy based on rotation strategy
        if self.rotation_strategy == ProxyRotationStrategy.ROUND_ROBIN:
            proxy = working_proxies[self.current_index % len(working_proxies)]
            self.current_index += 1
            
        elif self.rotation_strategy == ProxyRotationStrategy.RANDOM:
            proxy = random.choice(working_proxies)
            
        elif self.rotation_strategy == ProxyRotationStrategy.FAILOVER:
            # Use first working proxy (already sorted by score)
            proxy = working_proxies[0]
            
        elif self.rotation_strategy == ProxyRotationStrategy.WEIGHTED:
            # Weighted random selection based on score
            total_score = sum(p.score for p in working_proxies)
            if total_score > 0:
                weights = [p.score / total_score for p in working_proxies]
                proxy = random.choices(working_proxies, weights=weights)[0]
            else:
                proxy = random.choice(working_proxies)
        
        else:
            proxy = working_proxies[0]
        
        self.logger.debug(f"Selected proxy: {proxy.url} (score: {proxy.score:.3f})")
        return proxy
    
    def get_proxy_dict(self, proxy: ProxyInfo) -> Dict[str, str]:
        """
        Convert ProxyInfo to dictionary format for requests
        
        Args:
            proxy: ProxyInfo instance
            
        Returns:
            Dictionary with proxy configuration
        """
        proxy_dict = {"server": proxy.url}
        
        if proxy.username and proxy.password:
            proxy_dict["username"] = proxy.username
            proxy_dict["password"] = proxy.password
        
        return proxy_dict
    
    def add_proxy(self, proxy_url: str, country: Optional[str] = None, 
                  city: Optional[str] = None, isp: Optional[str] = None) -> bool:
        """
        Add new proxy to the pool
        
        Args:
            proxy_url: Proxy URL
            country: Country code
            city: City name
            isp: ISP name
            
        Returns:
            True if proxy added successfully
        """
        try:
            proxy_info = self._parse_proxy_url(proxy_url)
            if proxy_info:
                proxy_info.country = country
                proxy_info.city = city
                proxy_info.isp = isp
                self.proxies.append(proxy_info)
                self.logger.info(f"Added proxy: {proxy_url}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to add proxy {proxy_url}: {e}")
            return False
    
    def remove_proxy(self, proxy_url: str) -> bool:
        """
        Remove proxy from the pool
        
        Args:
            proxy_url: Proxy URL to remove
            
        Returns:
            True if proxy removed successfully
        """
        for i, proxy in enumerate(self.proxies):
            if proxy.url == proxy_url:
                removed_proxy = self.proxies.pop(i)
                self.logger.info(f"Removed proxy: {removed_proxy.url}")
                return True
        return False
    
    def disable_proxy(self, proxy_url: str) -> bool:
        """
        Disable proxy without removing it
        
        Args:
            proxy_url: Proxy URL to disable
            
        Returns:
            True if proxy disabled successfully
        """
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                proxy.is_active = False
                self.logger.info(f"Disabled proxy: {proxy.url}")
                return True
        return False
    
    def enable_proxy(self, proxy_url: str) -> bool:
        """
        Enable previously disabled proxy
        
        Args:
            proxy_url: Proxy URL to enable
            
        Returns:
            True if proxy enabled successfully
        """
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                proxy.is_active = True
                self.logger.info(f"Enabled proxy: {proxy.url}")
                return True
        return False
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy pool statistics"""
        total_proxies = len(self.proxies)
        working_proxies = len([p for p in self.proxies if p.is_working])
        active_proxies = len([p for p in self.proxies if p.is_active])
        
        # Calculate average success rate
        total_success = sum(p.success_count for p in self.proxies)
        total_attempts = sum(p.success_count + p.failure_count for p in self.proxies)
        avg_success_rate = total_success / total_attempts if total_attempts > 0 else 0.0
        
        # Calculate average response time
        response_times = [p.response_time for p in self.proxies if p.response_time]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        return {
            "total_proxies": total_proxies,
            "working_proxies": working_proxies,
            "active_proxies": active_proxies,
            "working_ratio": working_proxies / total_proxies if total_proxies > 0 else 0.0,
            "average_success_rate": avg_success_rate,
            "average_response_time": avg_response_time,
            "rotation_strategy": self.rotation_strategy.value,
            "last_health_check": max([p.last_check for p in self.proxies if p.last_check], default=None)
        }
    
    def get_proxy_by_region(self, region: str) -> List[ProxyInfo]:
        """
        Get all proxies for a specific region
        
        Args:
            region: Country code or region name
            
        Returns:
            List of ProxyInfo for the region
        """
        return [p for p in self.proxies if p.country == region and p.is_working]
    
    def set_rotation_strategy(self, strategy: str) -> bool:
        """
        Change proxy rotation strategy
        
        Args:
            strategy: New rotation strategy
            
        Returns:
            True if strategy changed successfully
        """
        try:
            self.rotation_strategy = ProxyRotationStrategy(strategy)
            self.logger.info(f"Proxy rotation strategy changed to: {strategy}")
            return True
        except ValueError:
            self.logger.error(f"Invalid rotation strategy: {strategy}")
            return False
    
    def force_health_check(self) -> None:
        """Force immediate health check of all proxies"""
        self.logger.info("Forcing proxy health check")
        asyncio.create_task(self._check_all_proxies())
    
    def export_proxy_list(self, filepath: str) -> bool:
        """
        Export proxy list to file
        
        Args:
            filepath: Output file path
            
        Returns:
            True if export successful
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for proxy in self.proxies:
                    f.write(f"{proxy.url}\n")
            self.logger.info(f"Proxy list exported to: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export proxy list: {e}")
            return False
    
    def import_proxy_list(self, filepath: str) -> bool:
        """
        Import proxy list from file
        
        Args:
            filepath: Input file path
            
        Returns:
            True if import successful
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.add_proxy(line)
            self.logger.info(f"Proxy list imported from: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import proxy list: {e}")
            return False
