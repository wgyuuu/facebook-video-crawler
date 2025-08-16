"""
Advanced Fingerprint Manager for Facebook Video Crawler System
Provides deep fingerprint spoofing and real device profile simulation
"""

import random
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.config_manager import config


class AdvancedFingerprintManager:
    """Advanced fingerprint manager with deep spoofing capabilities"""
    
    def __init__(self):
        """Initialize advanced fingerprint manager"""
        self.logger = get_logger("advanced_fingerprint_manager")
        self.config = config.get_anti_detection_config().get("advanced_fingerprint", {})
        
        # Load real device profiles
        self.real_device_profiles = self._load_real_device_profiles()
        self.current_profile = None
        
        # Fingerprint storage
        self.current_fingerprint: Dict[str, Any] = {}
        self.fingerprint_history: List[Dict[str, Any]] = []
        
        # Initialize fingerprint
        self._generate_advanced_fingerprint()
        
        self.logger.info("Advanced fingerprint manager initialized")
    
    def _load_real_device_profiles(self) -> Dict[str, Any]:
        """Load real device configuration profiles"""
        return {
            "iphone_14": {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                "screen": {"width": 390, "height": 844, "dpr": 3},
                "viewport": {"width": 390, "height": 844},
                "touch_points": 5,
                "max_touch_points": 5,
                "platform": "iPhone",
                "vendor": "Apple Inc.",
                "language": "en-US",
                "timezone": "America/New_York"
            },
            "samsung_galaxy_s23": {
                "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
                "screen": {"width": 412, "height": 915, "dpr": 2.625},
                "viewport": {"width": 412, "height": 915},
                "touch_points": 5,
                "max_touch_points": 5,
                "platform": "Android",
                "vendor": "Samsung",
                "language": "en-US",
                "timezone": "America/Los_Angeles"
            },
            "macbook_pro": {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
                "screen": {"width": 1440, "height": 900, "dpr": 2},
                "viewport": {"width": 1440, "height": 900},
                "touch_points": 0,
                "max_touch_points": 0,
                "platform": "MacIntel",
                "vendor": "Apple Inc.",
                "language": "en-US",
                "timezone": "America/Chicago"
            },
            "windows_desktop": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
                "screen": {"width": 1920, "height": 1080, "dpr": 1},
                "viewport": {"width": 1920, "height": 1080},
                "touch_points": 0,
                "max_touch_points": 0,
                "platform": "Win32",
                "vendor": "Google Inc.",
                "language": "en-US",
                "timezone": "America/New_York"
            }
        }
    
    def _generate_advanced_fingerprint(self) -> None:
        """Generate a new advanced fingerprint"""
        # Select a random device profile
        profile_name = random.choice(list(self.real_device_profiles.keys()))
        self.current_profile = self.real_device_profiles[profile_name]
        
        self.current_fingerprint = {
            "device_profile": profile_name,
            "canvas": self._generate_advanced_canvas_fingerprint(),
            "webgl": self._generate_advanced_webgl_fingerprint(),
            "fonts": self._generate_advanced_font_fingerprint(),
            "screen": self.current_profile["screen"],
            "viewport": self.current_profile["viewport"],
            "timezone": self.current_profile["timezone"],
            "language": self.current_profile["language"],
            "platform": self.current_profile["platform"],
            "vendor": self.current_profile["vendor"],
            "touch_capabilities": {
                "max_touch_points": self.current_profile["max_touch_points"],
                "touch_support": self.current_profile["max_touch_points"] > 0
            },
            "hardware": self._generate_hardware_fingerprint(),
            "generated_at": datetime.now().isoformat()
        }
        
        # Store in history
        self.fingerprint_history.append(self.current_fingerprint.copy())
        
        # Keep only last 10 fingerprints
        if len(self.fingerprint_history) > 10:
            self.fingerprint_history.pop(0)
        
        self.logger.debug("New advanced fingerprint generated", 
                         extra_fields={"profile": profile_name, "fingerprint": self.current_fingerprint})
    
    def _generate_advanced_canvas_fingerprint(self) -> Dict[str, Any]:
        """Generate advanced canvas fingerprint with noise"""
        if not self.config.get("canvas_randomization", True):
            return {}
        
        # Use profile screen dimensions
        width = self.current_profile["screen"]["width"]
        height = self.current_profile["screen"]["height"]
        
        return {
            "width": width,
            "height": height,
            "color_depth": random.choice([24, 32]),
            "pixel_depth": random.choice([24, 32]),
            "noise_factor": random.uniform(0.1, 0.5),
            "compression_quality": random.uniform(0.7, 0.95),
            "antialiasing": random.choice([True, False])
        }
    
    def _generate_advanced_webgl_fingerprint(self) -> Dict[str, Any]:
        """Generate advanced WebGL fingerprint"""
        if not self.config.get("webgl_spoofing", True):
            return {}
        
        # GPU profiles based on device type
        if "iPhone" in self.current_profile["platform"]:
            gpu_vendors = ["Apple Inc.", "Imagination Technologies"]
            gpu_renderers = ["Apple A16 Bionic GPU", "Apple M1 Pro GPU", "PowerVR GT7600"]
        elif "Android" in self.current_profile["platform"]:
            gpu_vendors = ["Qualcomm", "ARM", "Mali", "Adreno"]
            gpu_renderers = ["Adreno 740", "Mali-G710 MC10", "ARM Mali-G78 MP14"]
        else:
            gpu_vendors = ["Intel Inc.", "NVIDIA Corporation", "AMD", "Apple Inc."]
            gpu_renderers = ["Intel Iris OpenGL Engine", "NVIDIA GeForce RTX 4090", "AMD Radeon RX 7900 XT"]
        
        return {
            "vendor": random.choice(gpu_vendors),
            "renderer": random.choice(gpu_renderers),
            "version": f"{random.randint(1, 4)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "shading_language_version": f"{random.randint(1, 4)}.{random.randint(0, 9)}0",
            "max_texture_size": random.choice([2048, 4096, 8192, 16384]),
            "max_viewport_dims": [random.randint(2048, 8192), random.randint(2048, 8192)],
            "max_anisotropy": random.choice([8, 16]),
            "max_samples": random.choice([4, 8, 16])
        }
    
    def _generate_advanced_font_fingerprint(self) -> Dict[str, Any]:
        """Generate advanced font fingerprint"""
        if not self.config.get("font_randomization", True):
            return {}
        
        # Font lists based on platform
        if "Mac" in self.current_profile["platform"]:
            available_fonts = [
                "Arial", "Helvetica", "Times", "Times New Roman", "Courier", "Courier New",
                "Verdana", "Georgia", "Palatino", "Garamond", "Bookman", "Comic Sans MS",
                "Trebuchet MS", "Arial Black", "Impact", "Lucida Console", "Lucida Sans Unicode"
            ]
        elif "Windows" in self.current_profile["platform"]:
            available_fonts = [
                "Arial", "Calibri", "Cambria", "Comic Sans MS", "Courier New", "Georgia",
                "Helvetica", "Impact", "Times New Roman", "Trebuchet MS", "Verdana", "Segoe UI"
            ]
        else:
            available_fonts = [
                "Arial", "Helvetica", "Times", "Times New Roman", "Courier", "Courier New",
                "Verdana", "Georgia", "DejaVu Sans", "DejaVu Serif", "Liberation Sans"
            ]
        
        # Select random subset of fonts
        num_fonts = random.randint(8, min(15, len(available_fonts)))
        selected_fonts = random.sample(available_fonts, num_fonts)
        
        return {
            "available_fonts": selected_fonts,
            "font_count": len(selected_fonts),
            "font_rendering": random.choice(["subpixel", "antialiased", "bitmap"]),
            "font_smoothing": random.choice([True, False])
        }
    
    def _generate_hardware_fingerprint(self) -> Dict[str, Any]:
        """Generate hardware fingerprint"""
        return {
            "cpu_cores": random.randint(2, 16),
            "memory_gb": random.choice([4, 8, 16, 32, 64]),
            "battery_level": random.uniform(0.1, 1.0) if self.current_profile["max_touch_points"] > 0 else None,
            "connection_type": random.choice(["4g", "3g", "2g", "wifi", "ethernet"]),
            "downlink": random.uniform(1.0, 100.0),
            "rtt": random.randint(20, 200)
        }
    
    async def apply_device_profile(self, page, profile_name: str = None) -> bool:
        """Apply a specific device profile to the page"""
        try:
            if profile_name is None:
                profile_name = self.current_profile["device_profile"]
            
            if profile_name not in self.real_device_profiles:
                self.logger.error(f"Unknown device profile: {profile_name}")
                return False
            
            profile = self.real_device_profiles[profile_name]
            self.current_profile = profile
            
            # Set viewport size
            await page.set_viewport_size(profile["viewport"])
            
            # Set user agent
            await page.set_extra_http_headers({
                "User-Agent": profile["user_agent"]
            })
            
            # Inject device capabilities
            await self._inject_device_capabilities(page, profile)
            
            # Inject fingerprint spoofing scripts
            await self._inject_fingerprint_scripts(page)
            
            self.logger.info(f"Applied device profile: {profile_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply device profile: {e}")
            return False
    
    async def _inject_device_capabilities(self, page, profile: Dict[str, Any]) -> None:
        """Inject device capabilities into the page"""
        script = f"""
        // Override navigator properties
        Object.defineProperty(navigator, 'maxTouchPoints', {{
            get: () => {profile['max_touch_points']},
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {random.randint(4, 16)},
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {random.choice([2, 4, 8, 16, 32])},
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{profile['platform']}',
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'vendor', {{
            get: () => '{profile['vendor']}',
            configurable: true
        }});
        
        Object.defineProperty(navigator, 'language', {{
            get: () => '{profile['language']}',
            configurable: true
        }});
        
        // Override screen properties
        Object.defineProperty(screen, 'width', {{
            get: () => {profile['screen']['width']},
            configurable: true
        }});
        
        Object.defineProperty(screen, 'height', {{
            get: () => {profile['screen']['height']},
            configurable: true
        }});
        
        Object.defineProperty(screen, 'availWidth', {{
            get: () => {profile['screen']['width']},
            configurable: true
        }});
        
        Object.defineProperty(screen, 'availHeight', {{
            get: () => {profile['screen']['height']},
            configurable: true
        }});
        """
        
        await page.add_init_script(script)
    
    async def _inject_fingerprint_scripts(self, page) -> None:
        """Inject fingerprint spoofing scripts"""
        script = """
        // Hide automation indicators
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
            configurable: true
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
            configurable: true
        });
        """
        
        await page.add_init_script(script)
    
    def get_current_fingerprint(self) -> Dict[str, Any]:
        """Get current fingerprint"""
        return self.current_fingerprint.copy()
    
    def get_current_profile(self) -> Dict[str, Any]:
        """Get current device profile"""
        return self.current_profile.copy()
    
    async def rotate_fingerprint(self) -> None:
        """Rotate to a new fingerprint"""
        self._generate_advanced_fingerprint()
        self.logger.info("Fingerprint rotated")


# Global advanced fingerprint manager instance
advanced_fingerprint_manager = AdvancedFingerprintManager()
