"""
Crawler Engine for Facebook Video Crawler System
Provides browser management, page navigation, and core crawling functionality
"""

import asyncio
import time
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import random

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    print("Playwright not installed. Please run: pip install playwright")
    print("Then run: playwright install")
    raise

from ..utils.logger import get_logger
from ..utils.config_manager import config


class CrawlerEngine:
    """Main crawler engine using Playwright"""
    
    def __init__(self, config_overrides: Optional[Dict[str, Any]] = None):
        """
        Initialize crawler engine
        
        Args:
            config_overrides: Optional configuration overrides
        """
        self.logger = get_logger("crawler_engine")
        self.config = config.get_crawler_config()
        
        # Override config if provided
        if config_overrides:
            for key, value in config_overrides.items():
                if key in self.config:
                    self.config[key] = value
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_running = False
        
        # Performance tracking
        self.start_time = None
        self.operation_count = 0
        
        self.logger.info("Crawler engine initialized", extra_fields={"config": self.config})
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
    
    async def start(self) -> None:
        """Start the crawler engine"""
        if self.is_running:
            self.logger.warning("Crawler engine is already running")
            return
        
        try:
            self.logger.info("Starting crawler engine")
            self.start_time = time.time()
            
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser
            await self._launch_browser()
            
            # Create browser context
            await self._create_context()
            
            # Create page
            await self._create_page()
            
            self.is_running = True
            self.logger.info("Crawler engine started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start crawler engine: {e}")
            await self.cleanup()
            raise
    
    async def _launch_browser(self) -> None:
        """Launch browser instance"""
        browser_type = self.config.get("engine", "chromium")
        
        if browser_type == "chromium":
            browser_launcher = self.playwright.chromium
        elif browser_type == "firefox":
            browser_launcher = self.playwright.firefox
        elif browser_type == "webkit":
            browser_launcher = self.playwright.webkit
        else:
            self.logger.warning(f"Unknown browser type: {browser_type}, using chromium")
            browser_launcher = self.playwright.chromium
        
        launch_options = {
            "headless": self.config.get("headless", False),
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu"
            ]
        }
        
        self.browser = await browser_launcher.launch(**launch_options)
        self.logger.info(f"Browser launched: {browser_type}")
    
    async def _create_context(self) -> None:
        """Create browser context with anti-detection settings"""
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": self._get_random_user_agent(),
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "permissions": ["geolocation"],
            "extra_http_headers": {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        }
        
        # Add proxy if enabled
        if config.get("anti_detection.proxy.enabled"):
            proxy = self._get_proxy()
            if proxy:
                context_options["proxy"] = proxy
                self.logger.info(f"Using proxy: {proxy['server']}")
        
        self.context = await self.browser.new_context(**context_options)
        
        # Add anti-detection scripts
        await self._inject_anti_detection_scripts()
        
        self.logger.info("Browser context created with anti-detection settings")
    
    async def _create_page(self) -> None:
        """Create new page with additional settings"""
        self.page = await self.context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(self.config.get("timeout", 30000))
        
        # Set default navigation timeout
        self.page.set_default_navigation_timeout(self.config.get("timeout", 30000))
        
        # Add event listeners
        self.page.on("pageerror", self._on_page_error)
        self.page.on("requestfailed", self._on_request_failed)
        
        self.logger.info("Page created successfully")
    
    async def _inject_anti_detection_scripts(self) -> None:
        """Inject anti-detection JavaScript scripts"""
        try:
            # Canvas fingerprint randomization
            if config.get("anti_detection.fingerprint.canvas_randomization"):
                await self.context.add_init_script("""
                    // Override canvas toDataURL method
                    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    HTMLCanvasElement.prototype.toDataURL = function(type, quality) {
                        // Add random noise to canvas data
                        const ctx = this.getContext('2d');
                        if (ctx) {
                            const imageData = ctx.getImageData(0, 0, this.width, this.height);
                            const data = imageData.data;
                            for (let i = 0; i < data.length; i += 4) {
                                // Add minimal random noise
                                data[i] = Math.max(0, Math.min(255, data[i] + (Math.random() - 0.5) * 2));
                                data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + (Math.random() - 0.5) * 2));
                                data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + (Math.random() - 0.5) * 2));
                            }
                            ctx.putImageData(imageData, 0, 0);
                        }
                        return originalToDataURL.call(this, type, quality);
                    };
                """)
            
            # WebGL fingerprint spoofing
            if config.get("anti_detection.fingerprint.webgl_spoofing"):
                await self.context.add_init_script("""
                    // Override WebGL getParameter method
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        // Spoof vendor and renderer
                        if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter.call(this, parameter);
                    };
                """)
            
            # Font fingerprint randomization
            if config.get("anti_detection.fingerprint.font_randomization"):
                await self.context.add_init_script("""
                    // Override font detection
                    Object.defineProperty(document, 'fonts', {
                        get: function() {
                            return {
                                ready: Promise.resolve(),
                                check: function() { return true; },
                                load: function() { return Promise.resolve(); }
                            };
                        }
                    });
                """)
            
            self.logger.info("Anti-detection scripts injected successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to inject some anti-detection scripts: {e}")
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent from configuration"""
        user_agents = config.get_user_agents()
        return random.choice(user_agents) if user_agents else ""
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration"""
        proxies = config.get_proxy_list()
        if not proxies:
            return None
        
        proxy = random.choice(proxies)
        
        # Parse proxy string
        if proxy.startswith("http://"):
            return {"server": proxy}
        elif proxy.startswith("https://"):
            return {"server": proxy}
        elif proxy.startswith("socks5://"):
            return {"server": proxy}
        else:
            # Assume HTTP proxy
            return {"server": f"http://{proxy}"}
    
    async def navigate_to(self, url: str, wait_for: Optional[str] = None) -> bool:
        """
        Navigate to URL with anti-detection measures
        
        Args:
            url: Target URL
            wait_for: Optional selector to wait for
            
        Returns:
            True if navigation successful
        """
        if not self.is_running or not self.page:
            raise RuntimeError("Crawler engine not running")
        
        try:
            self.operation_count += 1
            self.logger.info(f"Navigating to: {url}")
            
            # Add random delay before navigation
            await self._random_delay(1000, 3000)
            
            # Navigate to page
            response = await self.page.goto(url, wait_until="networkidle")
            
            if not response or response.status >= 400:
                self.logger.error(f"Navigation failed: {response.status if response else 'No response'}")
                return False
            
            # Wait for specific element if specified
            if wait_for:
                try:
                    await self.page.wait_for_selector(wait_for, timeout=10000)
                except Exception as e:
                    self.logger.warning(f"Timeout waiting for selector {wait_for}: {e}")
            
            # Simulate human behavior
            await self._simulate_human_behavior()
            
            self.logger.info(f"Successfully navigated to: {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False
    
    async def _simulate_human_behavior(self) -> None:
        """Simulate human-like behavior on the page"""
        if not config.get("anti_detection.behavior.mouse_simulation"):
            return
        
        try:
            # Random mouse movement
            await self.page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
            
            # Random scroll
            if config.get("anti_detection.behavior.scroll_simulation"):
                scroll_amount = random.randint(-300, 300)
                await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                
                # Random delay after scroll
                await self._random_delay(500, 1500)
            
        except Exception as e:
            self.logger.debug(f"Human behavior simulation failed: {e}")
    
    async def _random_delay(self, min_ms: int, max_ms: int) -> None:
        """Add random delay between operations"""
        delay = random.randint(min_ms, max_ms) / 1000.0
        await asyncio.sleep(delay)
    
    async def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Wait for element to appear on page
        
        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            
        Returns:
            True if element found
        """
        if not self.page:
            return False
        
        try:
            timeout = timeout or self.config.get("timeout", 30000)
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            self.logger.debug(f"Element not found: {selector} - {e}")
            return False
    
    async def click_element(self, selector: str, wait_for: Optional[str] = None) -> bool:
        """
        Click element with human-like behavior
        
        Args:
            selector: CSS selector
            wait_for: Optional selector to wait for after click
            
        Returns:
            True if click successful
        """
        if not self.page:
            return False
        
        try:
            # Wait for element to be visible
            if not await self.wait_for_element(selector, 5000):
                return False
            
            # Hover over element first
            await self.page.hover(selector)
            await self._random_delay(100, 300)
            
            # Click with random delay
            await self.page.click(selector)
            
            # Wait for specified element if provided
            if wait_for:
                await self.wait_for_element(wait_for, 10000)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False
    
    async def get_page_content(self) -> str:
        """Get current page HTML content"""
        if not self.page:
            return ""
        
        try:
            return await self.page.content()
        except Exception as e:
            self.logger.error(f"Failed to get page content: {e}")
            return ""
    
    async def get_element_text(self, selector: str) -> str:
        """Get text content of element"""
        if not self.page:
            return ""
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content() or ""
            return ""
        except Exception as e:
            self.logger.debug(f"Failed to get element text: {e}")
            return ""
    
    async def get_element_attribute(self, selector: str, attribute: str) -> str:
        """Get attribute value of element"""
        if not self.page:
            return ""
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute) or ""
            return ""
        except Exception as e:
            self.logger.debug(f"Failed to get element attribute: {e}")
            return ""
    
    async def take_screenshot(self, path: str) -> bool:
        """Take screenshot of current page"""
        if not self.page:
            return False
        
        try:
            await self.page.screenshot(path=path)
            self.logger.info(f"Screenshot saved: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return False
    
    def _on_page_error(self, error: Exception) -> None:
        """Handle page errors"""
        # Filter out common Facebook JavaScript errors that don't affect functionality
        error_str = str(error)
        if "requireLazy is not defined" in error_str:
            # This is a common Facebook error that doesn't break functionality
            self.logger.debug(f"Facebook JavaScript error (non-critical): {error}")
        elif "Cannot redefine property" in error_str:
            # This is a fingerprint conflict error
            self.logger.debug(f"Property redefinition error (non-critical): {error}")
        else:
            self.logger.error(f"Page error: {error}")
    
    def _on_request_failed(self, request) -> None:
        """Handle failed requests"""
        self.logger.debug(f"Request failed: {request.url} - {request.failure}")
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            self.is_running = False
            
            if self.start_time:
                duration = time.time() - self.start_time
                self.logger.info(
                    f"Crawler engine stopped. Operations: {self.operation_count}, Duration: {duration:.2f}s"
                )
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            "is_running": self.is_running,
            "operation_count": self.operation_count,
            "start_time": self.start_time,
            "browser_type": self.config.get("engine"),
            "headless": self.config.get("headless"),
            "timeout": self.config.get("timeout")
        }
    
    async def restart(self) -> None:
        """Restart the crawler engine"""
        self.logger.info("Restarting crawler engine")
        await self.cleanup()
        await self.start()
    
    def is_healthy(self) -> bool:
        """Check if engine is healthy"""
        return (
            self.is_running and
            self.browser is not None and
            self.context is not None and
            self.page is not None
        )
