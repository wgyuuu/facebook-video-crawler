"""
Request Disguiser for Facebook Video Crawler System
Provides request header and timing disguise for anti-detection
"""

import random
import time
from typing import Dict, List, Optional

from ..utils.logger import get_logger
from ..utils.config_manager import config


class RequestDisguiser:
    """Disguises HTTP requests to appear more human-like"""
    
    def __init__(self):
        """Initialize request disguiser"""
        self.logger = get_logger("request_disguiser")
        self.config = config.get_anti_detection_config().get("request_disguise", {})
        
        # Load User-Agents
        self.user_agents = self._load_user_agents()
        
        self.logger.info("Request disguiser initialized")
    
    def _load_user_agents(self) -> List[str]:
        """Load User-Agent strings from configuration"""
        try:
            # Try to load from file first
            user_agents_file = config.get("paths.user_agents_file")
            if user_agents_file:
                with open(user_agents_file, 'r') as f:
                    agents = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    if agents:
                        return agents
        except:
            pass
        
        # Fallback to default User-Agents
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
    
    def get_random_user_agent(self) -> str:
        """Get a random User-Agent string"""
        if self.user_agents:
            return random.choice(self.user_agents)
        return self.user_agents[0] if self.user_agents else ""
    
    def get_disguised_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Generate disguised HTTP headers
        
        Args:
            custom_headers: Additional custom headers
            
        Returns:
            Dictionary of disguised headers
        """
        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
        
        # Add custom headers if provided
        if custom_headers:
            headers.update(custom_headers)
        
        # Randomize Accept-Language occasionally
        if random.random() < 0.3:
            languages = [
                "en-US,en;q=0.9",
                "en-GB,en;q=0.9",
                "en-CA,en;q=0.9",
                "en-AU,en;q=0.9"
            ]
            headers["Accept-Language"] = random.choice(languages)
        
        return headers
    
    def add_request_delay(self) -> None:
        """Add random delay between requests"""
        if not self.config.get("request_delay_range"):
            return
        
        delay_range = self.config["request_delay_range"]
        if isinstance(delay_range, list) and len(delay_range) >= 2:
            min_delay, max_delay = delay_range[0], delay_range[1]
            delay = random.uniform(min_delay / 1000, max_delay / 1000)  # Convert to seconds
            time.sleep(delay)
            self.logger.debug(f"Request delay: {delay:.3f}s")
    
    def get_random_referer(self) -> str:
        """Get a random referer URL"""
        referers = [
            "https://www.google.com/",
            "https://www.facebook.com/",
            "https://www.youtube.com/",
            "https://www.twitter.com/",
            "https://www.instagram.com/",
            "https://www.linkedin.com/"
        ]
        return random.choice(referers)
    
    def disguise_browser_context(self, context) -> None:
        """
        Apply disguise settings to browser context
        
        Args:
            context: Playwright browser context
        """
        try:
            # Set User-Agent
            user_agent = self.get_random_user_agent()
            context.set_extra_http_headers({
                "User-Agent": user_agent
            })
            
            # Set viewport size randomly
            viewports = [
                {"width": 1920, "height": 1080},
                {"width": 1366, "height": 768},
                {"width": 1440, "height": 900},
                {"width": 1536, "height": 864}
            ]
            viewport = random.choice(viewports)
            context.set_viewport_size(viewport["width"], viewport["height"])
            
            self.logger.debug(f"Browser context disguised: {user_agent[:50]}..., {viewport}")
            
        except Exception as e:
            self.logger.warning(f"Failed to disguise browser context: {e}")


# Global request disguiser instance
request_disguiser = RequestDisguiser()


def get_disguised_headers(custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Global function to get disguised headers"""
    return request_disguiser.get_disguised_headers(custom_headers)


def add_request_delay() -> None:
    """Global function to add request delay"""
    request_disguiser.add_request_delay()


def disguise_browser_context(context) -> None:
    """Global function to disguise browser context"""
    request_disguiser.disguise_browser_context(context)
