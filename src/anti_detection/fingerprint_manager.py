"""
Browser Fingerprint Manager for Facebook Video Crawler System
Provides fingerprint randomization and spoofing capabilities
"""

import random
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..utils.logger import get_logger
from ..utils.config_manager import config


class FingerprintManager:
    """Manages browser fingerprint randomization and spoofing"""
    
    def __init__(self):
        """Initialize fingerprint manager"""
        self.logger = get_logger("fingerprint_manager")
        self.config = config.get_anti_detection_config().get("fingerprint", {})
        
        # Fingerprint storage
        self.current_fingerprint: Dict[str, Any] = {}
        self.fingerprint_history: List[Dict[str, Any]] = []
        
        # Initialize fingerprint
        self._generate_fingerprint()
        
        self.logger.info("Fingerprint manager initialized")
    
    def _generate_fingerprint(self) -> None:
        """Generate a new random fingerprint"""
        self.current_fingerprint = {
            "canvas": self._generate_canvas_fingerprint(),
            "webgl": self._generate_webgl_fingerprint(),
            "fonts": self._generate_font_fingerprint(),
            "screen": self._generate_screen_fingerprint(),
            "timezone": self._generate_timezone_fingerprint(),
            "language": self._generate_language_fingerprint(),
            "platform": self._generate_platform_fingerprint(),
            "generated_at": datetime.now().isoformat()
        }
        
        # Store in history
        self.fingerprint_history.append(self.current_fingerprint.copy())
        
        # Keep only last 10 fingerprints
        if len(self.fingerprint_history) > 10:
            self.fingerprint_history.pop(0)
        
        self.logger.debug("New fingerprint generated", extra_fields={"fingerprint": self.current_fingerprint})
    
    def _generate_canvas_fingerprint(self) -> Dict[str, Any]:
        """Generate random canvas fingerprint"""
        if not self.config.get("canvas_randomization", True):
            return {}
        
        # Common canvas sizes
        canvas_sizes = [
            (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
            (1280, 720), (1600, 900), (1024, 768), (800, 600)
        ]
        
        width, height = random.choice(canvas_sizes)
        
        return {
            "width": width,
            "height": height,
            "color_depth": random.choice([24, 32]),
            "pixel_depth": random.choice([24, 32]),
            "noise_factor": random.uniform(0.1, 0.5)
        }
    
    def _generate_webgl_fingerprint(self) -> Dict[str, Any]:
        """Generate random WebGL fingerprint"""
        if not self.config.get("webgl_spoofing", True):
            return {}
        
        # Common GPU vendors and renderers
        gpu_vendors = [
            "Intel Inc.", "NVIDIA Corporation", "AMD", "Apple Inc.",
            "Microsoft", "VMware, Inc.", "Parallels"
        ]
        
        gpu_renderers = [
            "Intel Iris OpenGL Engine", "NVIDIA GeForce GTX 1060",
            "AMD Radeon RX 580", "Apple M1 Pro", "Microsoft Basic Render Driver",
            "VMware SVGA 3D", "Parallels Display Adapter"
        ]
        
        return {
            "vendor": random.choice(gpu_vendors),
            "renderer": random.choice(gpu_renderers),
            "version": f"{random.randint(1, 4)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "shading_language_version": f"{random.randint(1, 4)}.{random.randint(0, 9)}0",
            "max_texture_size": random.choice([2048, 4096, 8192, 16384]),
            "max_viewport_dims": [random.randint(2048, 8192), random.randint(2048, 8192)]
        }
    
    def _generate_font_fingerprint(self) -> Dict[str, Any]:
        """Generate random font fingerprint"""
        if not self.config.get("font_randomization", True):
            return {}
        
        # Common font families
        font_families = [
            "Arial", "Helvetica", "Times New Roman", "Georgia", "Verdana",
            "Tahoma", "Trebuchet MS", "Impact", "Comic Sans MS", "Courier New"
        ]
        
        # Randomly select 5-8 fonts
        num_fonts = random.randint(5, 8)
        selected_fonts = random.sample(font_families, num_fonts)
        
        return {
            "available_fonts": selected_fonts,
            "font_count": num_fonts,
            "font_loading_strategy": random.choice(["eager", "lazy", "auto"])
        }
    
    def _generate_screen_fingerprint(self) -> Dict[str, Any]:
        """Generate random screen fingerprint"""
        if not self.config.get("screen_resolution_randomization", True):
            return {}
        
        # Common screen resolutions
        screen_resolutions = [
            (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
            (1280, 720), (1600, 900), (1024, 768), (2560, 1440),
            (3840, 2160), (1680, 1050)
        ]
        
        width, height = random.choice(screen_resolutions)
        
        return {
            "width": width,
            "height": height,
            "avail_width": width,
            "avail_height": height,
            "color_depth": random.choice([24, 32]),
            "pixel_depth": random.choice([24, 32]),
            "device_pixel_ratio": random.choice([1, 1.25, 1.5, 2, 2.5, 3])
        }
    
    def _generate_timezone_fingerprint(self) -> Dict[str, Any]:
        """Generate random timezone fingerprint"""
        if not self.config.get("timezone_randomization", True):
            return {}
        
        # Common timezones
        timezones = [
            "America/New_York", "America/Los_Angeles", "America/Chicago",
            "America/Denver", "Europe/London", "Europe/Paris", "Europe/Berlin",
            "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney"
        ]
        
        selected_timezone = random.choice(timezones)
        
        # Generate random offset
        offset_hours = random.randint(-12, 14)
        offset_minutes = random.choice([0, 15, 30, 45])
        
        return {
            "timezone": selected_timezone,
            "offset_hours": offset_hours,
            "offset_minutes": offset_minutes,
            "dst_enabled": random.choice([True, False])
        }
    
    def _generate_language_fingerprint(self) -> Dict[str, Any]:
        """Generate random language fingerprint"""
        if not self.config.get("language_randomization", True):
            return {}
        
        # Common language combinations
        language_combinations = [
            ["en-US", "en", "en-GB"],
            ["en-GB", "en", "en-US"],
            ["de-DE", "de", "en"],
            ["fr-FR", "fr", "en"],
            ["es-ES", "es", "en"],
            ["it-IT", "it", "en"],
            ["pt-BR", "pt", "en"],
            ["ru-RU", "ru", "en"],
            ["ja-JP", "ja", "en"],
            ["ko-KR", "ko", "en"]
        ]
        
        selected_languages = random.choice(language_combinations)
        
        return {
            "languages": selected_languages,
            "primary_language": selected_languages[0],
            "accept_language": ", ".join(selected_languages)
        }
    
    def _generate_platform_fingerprint(self) -> Dict[str, Any]:
        """Generate random platform fingerprint"""
        platforms = [
            "Win32", "MacIntel", "Linux x86_64", "Linux armv7l",
            "Linux aarch64", "FreeBSD x86_64"
        ]
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36"
        ]
        
        return {
            "platform": random.choice(platforms),
            "user_agent": random.choice(user_agents),
            "cookie_enabled": True,
            "do_not_track": random.choice([None, "1", "0"]),
            "hardware_concurrency": random.choice([2, 4, 8, 16, 32])
        }
    
    def get_current_fingerprint(self) -> Dict[str, Any]:
        """Get current fingerprint"""
        return self.current_fingerprint.copy()
    
    def get_fingerprint_script(self) -> str:
        """Generate JavaScript code to apply current fingerprint"""
        script_parts = []
        
        # Canvas fingerprint
        if self.current_fingerprint.get("canvas"):
            canvas = self.current_fingerprint["canvas"]
            script_parts.append(f"""
                // Canvas fingerprint randomization
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type, quality) {{
                    const ctx = this.getContext('2d');
                    if (ctx) {{
                        const imageData = ctx.getImageData(0, 0, this.width, this.height);
                        const data = imageData.data;
                        const noiseFactor = {canvas.get('noise_factor', 0.3)};
                        
                        for (let i = 0; i < data.length; i += 4) {{
                            data[i] = Math.max(0, Math.min(255, data[i] + (Math.random() - 0.5) * noiseFactor * 10));
                            data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + (Math.random() - 0.5) * noiseFactor * 10));
                            data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + (Math.random() - 0.5) * noiseFactor * 10));
                        }}
                        ctx.putImageData(imageData, 0, 0);
                    }}
                    return originalToDataURL.call(this, type, quality);
                }};
            """)
        
        # WebGL fingerprint
        if self.current_fingerprint.get("webgl"):
            webgl = self.current_fingerprint["webgl"]
            script_parts.append(f"""
                // WebGL fingerprint spoofing
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                        return '{webgl.get("vendor", "Intel Inc.")}';
                    }}
                    if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
                        return '{webgl.get("renderer", "Intel Iris OpenGL Engine")}';
                    }}
                    if (parameter === 37447) {{ // UNMASKED_VERSION_WEBGL
                        return '{webgl.get("version", "4.6.0")}';
                    }}
                    return getParameter.call(this, parameter);
                }};
            """)
        
        # Font fingerprint
        if self.current_fingerprint.get("fonts"):
            fonts = self.current_fingerprint["fonts"]
            available_fonts = fonts.get("available_fonts", [])
            script_parts.append(f"""
                // Font fingerprint randomization
                if (!document.fonts) {{
                    Object.defineProperty(document, 'fonts', {{
                        get: function() {{
                            return {{
                                ready: Promise.resolve(),
                                check: function(font) {{ 
                                    return {json.dumps(available_fonts)}.includes(font); 
                                }},
                                load: function(font) {{ 
                                    return Promise.resolve(); 
                                }}
                            }};
                        }}
                    }});
                }}
            """)
        
        # Screen fingerprint
        if self.current_fingerprint.get("screen"):
            screen = self.current_fingerprint["screen"]
            script_parts.append(f"""
                // Screen fingerprint spoofing
                if (!screen.width) {{
                    Object.defineProperty(screen, 'width', {{
                        get: function() {{ return {screen.get("width", 1920)}; }}
                    }});
                }}
                if (!screen.height) {{
                    Object.defineProperty(screen, 'height', {{
                        get: function() {{ return {screen.get("height", 1080)}; }}
                    }});
                }}
                if (!screen.availWidth) {{
                    Object.defineProperty(screen, 'availWidth', {{
                        get: function() {{ return {screen.get("avail_width", 1920)}; }}
                    }});
                }}
                if (!screen.availHeight) {{
                    Object.defineProperty(screen, 'availHeight', {{
                        get: function() {{ return {screen.get("avail_height", 1080)}; }}
                    }});
                }}
                if (!screen.colorDepth) {{
                    Object.defineProperty(screen, 'colorDepth', {{
                        get: function() {{ return {screen.get("color_depth", 24)}; }}
                    }});
                }}
                if (!screen.pixelDepth) {{
                    Object.defineProperty(screen, 'pixelDepth', {{
                        get: function() {{ return {screen.get("pixel_depth", 24)}; }}
                    }});
                }}
            """)
        
        # Timezone fingerprint
        if self.current_fingerprint.get("timezone"):
            timezone = self.current_fingerprint["timezone"]
            script_parts.append(f"""
                // Timezone fingerprint spoofing
                if (!Intl.DateTimeFormat) {{
                    Object.defineProperty(Intl, 'DateTimeFormat', {{
                        get: function() {{
                            return function(locale, options) {{
                                if (options && options.timeZone) {{
                                    options.timeZone = '{timezone.get("timezone", "America/New_York")}';
                                }}
                                return new Intl.DateTimeFormat(locale, options);
                            }};
                        }}
                    }});
                }}
            """)
        
        # Language fingerprint
        if self.current_fingerprint.get("language"):
            language = self.current_fingerprint["language"]
            script_parts.append(f"""
                // Language fingerprint spoofing
                if (!navigator.languages) {{
                    Object.defineProperty(navigator, 'languages', {{
                        get: function() {{ return {json.dumps(language.get("languages", ["en-US", "en"]))}; }}
                    }});
                }}
                if (!navigator.language) {{
                    Object.defineProperty(navigator, 'language', {{
                        get: function() {{ return '{language.get("primary_language", "en-US")}'; }}
                    }});
                }}
            """)
        
        # Platform fingerprint
        if self.current_fingerprint.get("platform"):
            platform = self.current_fingerprint["platform"]
            script_parts.append(f"""
                // Platform fingerprint spoofing
                if (!navigator.platform) {{
                    Object.defineProperty(navigator, 'platform', {{
                        get: function() {{ return '{platform.get("platform", "Win32")}'; }}
                    }});
                }}
                if (!navigator.hardwareConcurrency) {{
                    Object.defineProperty(navigator, 'hardwareConcurrency', {{
                        get: function() {{ return {platform.get("hardware_concurrency", 8)}; }}
                    }});
                }}
                if (!navigator.cookieEnabled) {{
                    Object.defineProperty(navigator, 'cookieEnabled', {{
                        get: function() {{ return {str(platform.get("cookie_enabled", True)).lower()}; }}
                    }});
                }}
            """)
        
        return "\n".join(script_parts)
    
    def rotate_fingerprint(self) -> Dict[str, Any]:
        """Generate a new fingerprint and return it"""
        self.logger.info("Rotating browser fingerprint")
        self._generate_fingerprint()
        return self.current_fingerprint.copy()
    
    def get_fingerprint_stats(self) -> Dict[str, Any]:
        """Get fingerprint statistics"""
        return {
            "total_fingerprints": len(self.fingerprint_history),
            "current_fingerprint_age": (
                datetime.now() - datetime.fromisoformat(self.current_fingerprint["generated_at"])
            ).total_seconds(),
            "last_rotation": self.current_fingerprint["generated_at"]
        }
    
    def validate_fingerprint(self, fingerprint: Dict[str, Any]) -> bool:
        """Validate if fingerprint is realistic"""
        try:
            # Check required fields
            required_fields = ["canvas", "webgl", "fonts", "screen", "timezone", "language", "platform"]
            for field in required_fields:
                if field not in fingerprint:
                    return False
            
            # Validate screen resolution
            screen = fingerprint.get("screen", {})
            if screen.get("width", 0) <= 0 or screen.get("height", 0) <= 0:
                return False
            
            # Validate timezone
            timezone = fingerprint.get("timezone", {})
            if not timezone.get("timezone"):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fingerprint validation failed: {e}")
            return False
    
    def export_fingerprint(self, filepath: str) -> bool:
        """Export current fingerprint to file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_fingerprint, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Fingerprint exported to: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export fingerprint: {e}")
            return False
    
    def import_fingerprint(self, filepath: str) -> bool:
        """Import fingerprint from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_fingerprint = json.load(f)
            
            if self.validate_fingerprint(imported_fingerprint):
                self.current_fingerprint = imported_fingerprint
                self.fingerprint_history.append(self.current_fingerprint.copy())
                self.logger.info(f"Fingerprint imported from: {filepath}")
                return True
            else:
                self.logger.error("Imported fingerprint validation failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to import fingerprint: {e}")
            return False
    
    def get_fingerprint_hash(self) -> str:
        """Get hash of current fingerprint for comparison"""
        import hashlib
        fingerprint_str = json.dumps(self.current_fingerprint, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()
