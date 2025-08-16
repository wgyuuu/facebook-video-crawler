"""
Configuration Manager for Facebook Video Crawler System
Handles configuration loading, validation, and management
"""

import os
import yaml
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging


class ConfigManager:
    """Configuration manager for the crawler system"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger(__name__)

        if config_path is None:
            # Try to find config file relative to the project root
            current_dir = Path(__file__).parent.parent.parent
            self.config_path = current_dir / "config" / "config.yaml"
        else:
            self.config_path = Path(config_path)
        
        self.logger.info(f"Config path: {self.config_path}")
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file and environment variables"""
        try:
            # Load base configuration from file
            if self.config_path and self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self.config = yaml.safe_load(file) or {}
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                self.config = self._get_default_config()
            
            # Override with environment variables
            self._load_environment_overrides()
            
            # Validate configuration
            self._validate_config()
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            "crawler": {
                "engine": "playwright",
                "headless": False,
                "timeout": 30000,
                "max_retries": 3,
                "concurrent_browsers": 1
            },
            "anti_detection": {
                "proxy": {
                    "enabled": False,
                    "pool_size": 10,
                    "rotation_strategy": "round_robin"
                },
                "fingerprint": {
                    "canvas_randomization": True,
                    "webgl_spoofing": True,
                    "font_randomization": True
                },
                "behavior": {
                    "mouse_simulation": True,
                    "scroll_simulation": True
                }
            },
            "facebook": {
                "search": {
                    "max_results": 50,
                    "delay_between_searches": [2000, 5000]
                },
                "regions": ["US"],
                "login": {
                    "enabled": False
                }
            },
            "storage": {
                "video_path": "./data/videos",
                "database": {
                    "type": "sqlite",
                    "connection_string": "sqlite:///./data/database/crawler.db"
                },
                "logging": {
                    "level": "INFO",
                    "file_path": "./data/logs/crawler.log"
                }
            }
        }
    
    def _load_environment_overrides(self) -> None:
        """Load configuration overrides from environment variables"""
        env_mappings = {
            "CRAWLER_ENGINE": ["crawler", "engine"],
            "CRAWLER_HEADLESS": ["crawler", "headless"],
            "CRAWLER_TIMEOUT": ["crawler", "timeout"],
            "PROXY_ENABLED": ["anti_detection", "proxy", "enabled"],
            "PROXY_POOL_SIZE": ["anti_detection", "proxy", "pool_size"],
            "FACEBOOK_MAX_RESULTS": ["facebook", "search", "max_results"],
            "STORAGE_VIDEO_PATH": ["storage", "video_path"],
            "LOG_LEVEL": ["storage", "logging", "level"]
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_path, env_value)
                self.logger.debug(f"Environment override: {env_var} = {env_value}")
    
    def _set_nested_value(self, path: List[str], value: Any) -> None:
        """Set a nested configuration value"""
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert value type based on expected type
        if isinstance(value, str):
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
        
        current[path[-1]] = value
    
    def _validate_config(self) -> None:
        """Validate configuration values"""
        # Ensure required directories exist
        self._ensure_directories()
        
        # Validate crawler settings
        if self.get("crawler.engine") not in ["playwright", "selenium"]:
            self.logger.warning("Invalid crawler engine, using playwright")
            self.set("crawler.engine", "playwright")
        
        # Validate timeout values
        timeout = self.get("crawler.timeout")
        if not isinstance(timeout, int) or timeout < 1000:
            self.logger.warning("Invalid timeout value, using 30000ms")
            self.set("crawler.timeout", 30000)
        
        # Validate proxy settings
        if self.get("anti_detection.proxy.enabled"):
            pool_size = self.get("anti_detection.proxy.pool_size")
            if not isinstance(pool_size, int) or pool_size < 1:
                self.logger.warning("Invalid proxy pool size, using 10")
                self.set("anti_detection.proxy.pool_size", 10)
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist"""
        directories = []
        
        # Add video path
        video_path = self.get("storage.video_path")
        if video_path:
            directories.append(video_path)
        
        # Add database directory
        db_connection = self.get("storage.database.connection_string")
        if db_connection and isinstance(db_connection, str):
            if db_connection.startswith("sqlite:///"):
                db_path = db_connection.replace("sqlite:///", "")
                if db_path:
                    directories.append(Path(db_path).parent)
        
        # Add logging directory
        log_path = self.get("storage.logging.file_path")
        if log_path:
            directories.append(Path(log_path).parent)
        
        for directory in directories:
            if directory:
                try:
                    Path(directory).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.logger.warning(f"Failed to create directory {directory}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot notation key
        
        Args:
            key: Configuration key in dot notation (e.g., "crawler.engine")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        current = self.config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot notation key
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config.copy()
    
    def reload(self) -> None:
        """Reload configuration from file"""
        self._load_config()
    
    def save(self, config_path: Optional[str] = None) -> None:
        """
        Save current configuration to file
        
        Args:
            config_path: Path to save configuration (uses current path if None)
        """
        save_path = config_path or self.config_path
        
        try:
            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'w', encoding='utf-8') as file:
                    yaml.dump(self.config, file, default_flow_style=False, allow_unicode=True)
                self.logger.info(f"Configuration saved to {save_path}")
            else:
                self.logger.error("No valid save path specified")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def get_proxy_list(self) -> List[str]:
        """Get list of proxy servers from proxies.txt file"""
        proxy_file = Path(__file__).parent.parent.parent / "config" / "proxies.txt"
        proxies = []
        
        try:
            if proxy_file.exists():
                with open(proxy_file, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            proxies.append(line)
        except Exception as e:
            self.logger.error(f"Failed to load proxy list: {e}")
        
        return proxies
    
    def get_user_agents(self) -> List[str]:
        """Get list of user agents from user_agents.txt file"""
        ua_file = Path(__file__).parent.parent.parent / "config" / "user_agents.txt"
        user_agents = []
        
        try:
            if ua_file.exists():
                with open(ua_file, 'r', encoding='utf-8') as file:
                    for line in file:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            user_agents.append(line)
        except Exception as e:
            self.logger.error(f"Failed to load user agents: {e}")
        
        # Fallback to default user agents if file is empty
        if not user_agents:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_0.0 Safari/537.36"
            ]
        
        return user_agents
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with multiple values
        
        Args:
            updates: Dictionary of configuration updates
        """
        for key, value in updates.items():
            self.set(key, value)
        
        self.logger.info("Configuration updated")
    
    def get_crawler_config(self) -> Dict[str, Any]:
        """Get crawler-specific configuration"""
        return {
            "engine": self.get("crawler.engine"),
            "headless": self.get("crawler.headless"),
            "timeout": self.get("crawler.timeout"),
            "max_retries": self.get("crawler.max_retries"),
            "concurrent_browsers": self.get("crawler.concurrent_browsers")
        }
    
    def get_anti_detection_config(self) -> Dict[str, Any]:
        """Get anti-detection configuration"""
        return {
            "proxy": self.get("anti_detection.proxy"),
            "fingerprint": self.get("anti_detection.fingerprint"),
            "behavior": self.get("anti_detection.behavior"),
            "request_disguise": self.get("anti_detection.request_disguise")
        }
    
    def get_facebook_config(self) -> Dict[str, Any]:
        """Get Facebook-specific configuration"""
        return {
            "search": self.get("facebook.search"),
            "regions": self.get("facebook.regions"),
            "login": self.get("facebook.login"),
            "video": self.get("facebook.video")
        }
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration"""
        return {
            "video_path": self.get("storage.video_path"),
            "database": self.get("storage.database"),
            "logging": self.get("storage.logging")
        }


# Global configuration instance
config = ConfigManager()
