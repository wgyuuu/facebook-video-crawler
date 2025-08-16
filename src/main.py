"""
Main entry point for Facebook Video Crawler System
Integrates all modules to provide complete crawling functionality
"""

import asyncio
import time
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import random
from urllib.parse import quote
import re

from .core.crawler_engine import CrawlerEngine
from .anti_detection.fingerprint_manager import FingerprintManager
from .anti_detection.advanced_fingerprint_manager import advanced_fingerprint_manager
from .anti_detection.proxy_manager import ProxyManager
from .anti_detection.advanced_behavior_simulator import advanced_behavior_simulator
from .anti_detection.session_manager import session_manager
from .anti_detection.network_fingerprint_spoofer import network_fingerprint_spoofer
from .data.video_extractor import VideoExtractor, VideoMetadata
from .utils.logger import get_logger, setup_logging
from .utils.config_manager import config


class FacebookVideoCrawler:
    """Main Facebook video crawler class"""
    
    def __init__(self, config_overrides: Optional[Dict[str, Any]] = None):
        """
        Initialize Facebook video crawler
        
        Args:
            config_overrides: Optional configuration overrides
        """
        # Setup logging
        storage_config = config.get_storage_config()
        self.logger = setup_logging(storage_config.get("logging", {}))
        
        # Initialize components
        self.fingerprint_manager = FingerprintManager()
        self.advanced_fingerprint_manager = advanced_fingerprint_manager
        self.proxy_manager = ProxyManager()
        self.advanced_behavior_simulator = advanced_behavior_simulator
        self.session_manager = session_manager
        self.network_fingerprint_spoofer = network_fingerprint_spoofer
        self.crawler_engine = None
        self.video_extractor = None
        
        # Configuration
        self.config = config.get_facebook_config()
        if config_overrides:
            for key, value in config_overrides.items():
                if key in self.config:
                    self.config[key] = value
        
        # Statistics
        self.stats = {
            "start_time": None,
            "total_videos_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "total_downloads": 0,
            "failed_downloads": 0,
            "current_session_duration": 0
        }
        
        self.logger.info("Facebook Video Crawler initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    async def start(self) -> None:
        """Start the crawler system"""
        try:
            self.logger.info("Starting Facebook Video Crawler")
            self.stats["start_time"] = time.time()
            
            # Initialize crawler engine
            self.crawler_engine = CrawlerEngine()
            await self.crawler_engine.start()
            
            # Initialize video extractor
            self.video_extractor = VideoExtractor(self.crawler_engine)
            
            # Apply advanced fingerprint and anti-detection measures
            await self._apply_advanced_anti_detection()
            
            self.logger.info("Facebook Video Crawler started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start crawler: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the crawler system"""
        try:
            self.logger.info("Stopping Facebook Video Crawler")
            
            if self.crawler_engine:
                await self.crawler_engine.cleanup()
                self.crawler_engine = None
            
            # Calculate session duration
            if self.stats["start_time"]:
                self.stats["current_session_duration"] = time.time() - self.stats["start_time"]
            
            self.logger.info("Facebook Video Crawler stopped", extra_fields={
                "session_stats": self.stats
            })
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    async def _apply_fingerprint(self) -> None:
        """Apply browser fingerprint to crawler engine"""
        try:
            if self.crawler_engine and self.crawler_engine.context:
                fingerprint_script = self.fingerprint_manager.get_fingerprint_script()
                if fingerprint_script:
                    await self.crawler_engine.context.add_init_script(fingerprint_script)
                    self.logger.info("Browser fingerprint applied successfully")
                else:
                    self.logger.warning("No fingerprint script available")
        except Exception as e:
            self.logger.warning(f"Failed to apply fingerprint: {e}")
    
    async def _apply_advanced_anti_detection(self) -> None:
        """Apply advanced anti-detection measures to crawler engine"""
        try:
            if self.crawler_engine and self.crawler_engine.page:
                # Apply basic fingerprint
                await self.fingerprint_manager.apply_fingerprint(self.crawler_engine.page)
                
                # Apply advanced fingerprint with device profile
                if self.config.get("anti_detection", {}).get("advanced_fingerprint", {}).get("enabled", True):
                    await self.advanced_fingerprint_manager.apply_device_profile(
                        self.crawler_engine.page
                    )
                
                # Apply network fingerprint spoofing
                if self.config.get("anti_detection", {}).get("network_spoofing", {}).get("enabled", True):
                    await self.network_fingerprint_spoofer.apply_network_profile(
                        self.crawler_engine.page
                    )
                
                # Initialize session management
                if self.config.get("anti_detection", {}).get("session_management", {}).get("enabled", True):
                    self.logger.info("Session management enabled")
                
                self.logger.info("Advanced anti-detection measures applied successfully")
        except Exception as e:
            self.logger.error(f"Failed to apply advanced anti-detection measures: {e}")
    
    async def search_videos(self, keyword: str, max_results: Optional[int] = None, 
                           region: Optional[str] = None) -> List[VideoMetadata]:
        """
        Search for videos by keyword
        
        Args:
            keyword: Search keyword
            max_results: Maximum number of results to return
            region: Target region for search
            
        Returns:
            List of VideoMetadata objects
        """
        if not self.crawler_engine:
            raise RuntimeError("Crawler not started")
        
        max_results = max_results or self.config.get("search", {}).get("max_results", 50)
        
        try:
            self.logger.info(f"Searching for videos with keyword: '{keyword}'", extra_fields={
                "max_results": max_results,
                "region": region
            })
            
            # Construct search URL
            search_url = self._build_search_url(keyword, region)
            
            # Try direct search first
            search_success = False
            max_retries = 2
            
            for attempt in range(max_retries):
                try:
                    if await self.crawler_engine.navigate_to(search_url):
                        self.logger.info(f"Successfully navigated to search page on attempt {attempt + 1}")
                        search_success = True
                        break
                    else:
                        self.logger.warning(f"Direct search failed on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2)
                            continue
                except Exception as e:
                    self.logger.error(f"Direct search error on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
            
            # If direct search fails, try alternative approach: go to Facebook homepage and search
            if not search_success:
                self.logger.info("Direct search failed, trying alternative approach via Facebook homepage...")
                try:
                    # Navigate to Facebook homepage first
                    if await self.crawler_engine.navigate_to("https://www.facebook.com/"):
                        self.logger.info("Successfully navigated to Facebook homepage")
                        await asyncio.sleep(3)
                        
                        # Check if login is required
                        login_indicators = [
                            "input[name='email']",
                            "input[name='pass']",
                            "button[name='login']",
                            "[data-testid='royal_login_button']"
                        ]
                        
                        login_required = False
                        for indicator in login_indicators:
                            try:
                                if await self.crawler_engine.page.query_selector(indicator):
                                    login_required = True
                                    self.logger.warning("Login required to access Facebook search functionality")
                                    break
                            except Exception:
                                continue
                        
                        if not login_required:
                            # Try to find and use the search box
                            search_box_selectors = [
                                "input[placeholder*='Search']",
                                "input[name='q']",
                                "input[aria-label*='Search']",
                                "[data-testid='search_input']",
                                "input[type='search']"
                            ]
                        
                            search_box = None
                            for selector in search_box_selectors:
                                try:
                                    search_box = await self.crawler_engine.page.query_selector(selector)
                                    if search_box:
                                        self.logger.info(f"Found search box with selector: {selector}")
                                        break
                                except Exception as e:
                                    self.logger.debug(f"Selector {selector} failed: {e}")
                                    continue
                            
                            if search_box:
                                # Clear and fill search box
                                await search_box.click()
                                await search_box.fill(keyword)
                                await asyncio.sleep(1)
                                
                                # Press Enter to search
                                await search_box.press("Enter")
                                await asyncio.sleep(5)
                                
                                self.logger.info("Search performed via homepage search box")
                                search_success = True
                            else:
                                self.logger.warning("Could not find search box on homepage")
                        else:
                            self.logger.error("Facebook requires login for search functionality")
                    else:
                        self.logger.error("Failed to navigate to Facebook homepage")
                        
                except Exception as e:
                    self.logger.error(f"Alternative search approach failed: {e}")
            
            if not search_success:
                self.logger.error("All search methods failed")
                
                # Check if login is enabled in config
                if self.config.get("login", {}).get("enabled", False):
                    self.logger.info("Login is enabled, attempting to authenticate...")
                    login_result = await self._attempt_login()
                    if login_result["success"]:
                        self.logger.info("Login successful, retrying search...")
                        # Retry search after login
                        search_url = self._build_search_url(keyword, region)
                        if await self.crawler_engine.navigate_to(search_url):
                            search_success = True
                            self.logger.info("Search successful after login")
                        else:
                            self.logger.error("Search still failed after login")
                    else:
                        # Login failed, return error with reason
                        error_message = f"Login failed: {login_result['reason']}"
                        self.logger.error(error_message)
                        # Create a VideoMetadata object with error information
                        error_video = VideoMetadata()
                        error_video.status = "failed"
                        error_video.error_message = error_message
                        error_video.extracted_at = time.strftime("%Y-%m-%d %H:%M:%S")
                        # Return list with error information instead of trying fallback
                        return [error_video]
                
                # No fallback approach needed - if login fails, we return error
                # If login is not enabled, we also return empty results
            
            # Wait for search results to load with better error handling
            try:
                await asyncio.sleep(5)
                # Check if page loaded successfully
                page_title = await self.crawler_engine.page.title()
                self.logger.info(f"Page title: {page_title}")
            except Exception as e:
                self.logger.warning(f"Error getting page title: {e}")
            
            # Extract video URLs from search results
            video_urls = await self._extract_search_results(max_results)
            
            if not video_urls:
                self.logger.warning("No video URLs found in search results")
                return []
            
            self.logger.info(f"Found {len(video_urls)} video URLs in search results")
            
            # Extract metadata for each video
            videos = await self.video_extractor.extract_multiple_videos(video_urls)
            
            # Update statistics
            self.stats["total_videos_processed"] += len(videos)
            self.stats["successful_extractions"] += len([v for v in videos if v.status == "extracted"])
            self.stats["failed_extractions"] += len([v for v in videos if v.status == "failed"])
            
            return videos
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            # Create error metadata object
            error_video = VideoMetadata()
            error_video.status = "failed"
            error_video.error_message = f"Search operation failed: {str(e)}"
            error_video.extracted_at = time.strftime("%Y-%m-%d %H:%M:%S")
            return [error_video]
    
    def _build_search_url(self, keyword: str, region: Optional[str] = None) -> str:
        """Build Facebook search URL"""
        # Facebook search URL format - using the most common and stable format
        # Try different search endpoints that are more likely to work
        base_url = "https://www.facebook.com/search"
        
        # Add query parameters
        params = {
            "q": quote(keyword)  # URL encode the keyword to handle spaces and special characters
        }
        
        # Add region if specified
        if region:
            params["region"] = region
        
        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        return f"{base_url}?{query_string}"
    
    async def _attempt_login(self) -> dict:
        """Attempt to log in to Facebook using configured credentials"""
        try:
            self.logger.info("Attempting Facebook login...")
            
            # Navigate to Facebook login page
            if not await self.crawler_engine.navigate_to("https://www.facebook.com/login"):
                error_msg = "Failed to navigate to login page"
                self.logger.error(error_msg)
                return {"success": False, "reason": error_msg}
            
            await asyncio.sleep(2)
            
            # Get credentials from config
            credentials = self.config.get("login", {})
            email = credentials.get("email")
            password = credentials.get("password")
            
            if not email or not password:
                error_msg = "Login credentials not configured"
                self.logger.error(error_msg)
                return {"success": False, "reason": error_msg}
            
            # Find and fill email field
            email_field = await self.crawler_engine.page.query_selector("input[name='email']")
            if not email_field:
                error_msg = "Email field not found on login page"
                self.logger.error(error_msg)
                return {"success": False, "reason": error_msg}
            
            # Use advanced behavior simulation for email input
            if self.config.get("anti_detection", {}).get("advanced_behavior", {}).get("enabled", True):
                await self.advanced_behavior_simulator.simulate_human_typing(
                    self.crawler_engine.page, email_field, email, speed="normal"
                )
            else:
                await email_field.click()
                await email_field.fill(email)
                await asyncio.sleep(1)
            
            # Find and fill password field
            password_field = await self.crawler_engine.page.query_selector("input[name='pass']")
            if not password_field:
                error_msg = "Password field not found on login page"
                self.logger.error(error_msg)
                return {"success": False, "reason": error_msg}
            
            # Use advanced behavior simulation for password input
            if self.config.get("anti_detection", {}).get("advanced_behavior", {}).get("enabled", True):
                await self.advanced_behavior_simulator.simulate_human_typing(
                    self.crawler_engine.page, password_field, password, speed="fast"
                )
            else:
                await password_field.click()
                await password_field.fill(password)
                await asyncio.sleep(1)
            
            # Click login button
            login_button = await self.crawler_engine.page.query_selector("button[name='login']")
            if not login_button:
                error_msg = "Login button not found on login page"
                self.logger.error(error_msg)
                return {"success": False, "reason": error_msg}
            
            # Use advanced behavior simulation for login button click
            if self.config.get("anti_detection", {}).get("advanced_behavior", {}).get("enabled", True):
                await self.advanced_behavior_simulator.simulate_mouse_trail(
                    self.crawler_engine.page, "button[name='login']"
                )
                await self.advanced_behavior_simulator.simulate_human_click(
                    self.crawler_engine.page, "button[name='login']"
                )
            else:
                await login_button.click()
            
            await asyncio.sleep(5)
            
            # Check for security checkpoint and handle it
            checkpoint_result = await self._handle_security_checkpoint()
            if checkpoint_result["handled"]:
                if checkpoint_result["success"]:
                    self.logger.info("Security checkpoint handled successfully")
                    return {"success": True, "reason": "Login successful after security checkpoint"}
                else:
                    return {"success": False, "reason": checkpoint_result["reason"]}
            
            # Check if login was successful
            try:
                # Look for elements that indicate successful login
                success_indicators = [
                    "div[data-testid='pagelet_bluebar']",
                    "div[data-testid='blue_bar_profile_link']",
                    "div[aria-label='Your profile']",
                    "div[data-testid='blue_bar_profile_link']",
                    "a[data-testid='blue_bar_profile_link']"
                ]
                
                # Store session data if login successful
                if self.config.get("anti_detection", {}).get("session_management", {}).get("enabled", True):
                    try:
                        session_data = await self.session_manager.extract_session_data(
                            self.crawler_engine.page
                        )
                        if session_data:
                            self.session_manager.store_session(email, session_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to store session data: {e}")
                
                for indicator in success_indicators:
                    if await self.crawler_engine.page.query_selector(indicator):
                        self.logger.info("Login successful")
                        return {"success": True, "reason": "Login successful"}
                
                # Check for login errors
                error_indicators = [
                    "div[data-testid='error_box']",
                    "div[data-testid='error_message']",
                    "div[class*='error']",
                    "div[class*='alert']",
                    "div[class*='_50f4']"  # Facebook error class
                ]
                
                for indicator in error_indicators:
                    error_element = await self.crawler_engine.page.query_selector(indicator)
                    if error_element:
                        error_text = await error_element.text_content()
                        if error_text and error_text.strip():
                            error_msg = f"Facebook login error: {error_text.strip()}"
                            self.logger.error(error_msg)
                            return {"success": False, "reason": error_msg}
                
                # Check for specific Facebook error messages
                page_content = await self.crawler_engine.page.content()
                if "incorrect password" in page_content.lower() or "wrong password" in page_content.lower():
                    error_msg = "Incorrect password"
                    self.logger.error(error_msg)
                    return {"success": False, "reason": error_msg}
                elif "account not found" in page_content.lower() or "no account found" in page_content.lower():
                    error_msg = "Account not found"
                    self.logger.error(error_msg)
                    return {"success": False, "reason": error_msg}
                
                # If we can't determine the specific error, check if we're still on login page
                current_url = self.crawler_engine.page.url
                if "login" in current_url.lower() or "checkpoint" in current_url.lower():
                    error_msg = "Still on login page after attempt - login may have failed"
                    self.logger.error(error_msg)
                    return {"success": False, "reason": error_msg}
                
                self.logger.warning("Login status unclear, assuming failed")
                return {"success": False, "reason": "Login status unclear - unable to determine success or failure"}
                
            except Exception as e:
                error_msg = f"Error checking login status: {str(e)}"
                self.logger.error(error_msg)
                return {"success": False, "reason": error_msg}
                
        except Exception as e:
            error_msg = f"Login attempt failed: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "reason": error_msg}
    
    async def _handle_security_checkpoint(self) -> dict:
        """Handle Facebook security checkpoint challenges"""
        try:
            self.logger.info("Checking for security checkpoint...")
            await asyncio.sleep(3)
            
            # Check if we're on a security checkpoint page
            current_url = self.crawler_engine.page.url
            page_content = await self.crawler_engine.page.content()
            
            # Common security checkpoint indicators
            checkpoint_indicators = [
                "checkpoint",
                "security check",
                "verify your identity",
                "confirm your identity",
                "help us keep your account secure",
                "unusual login activity",
                "suspicious login attempt",
                "security verification",
                "account verification"
            ]
            
            is_checkpoint = any(indicator in page_content.lower() for indicator in checkpoint_indicators)
            
            if not is_checkpoint:
                return {"handled": False, "success": False, "reason": "No checkpoint detected"}
            
            self.logger.info("Security checkpoint detected, attempting to handle...")
            
            # Get checkpoint configuration
            checkpoint_config = self.config.get("login", {}).get("security_checkpoint", {})
            max_attempts = checkpoint_config.get("max_attempts", 3)
            timeout = checkpoint_config.get("timeout", 60)
            
            # Try to resolve checkpoint with retries
            for attempt in range(max_attempts):
                self.logger.info(f"Checkpoint resolution attempt {attempt + 1}/{max_attempts}")
                
                # Try to identify the type of checkpoint
                checkpoint_type = await self._identify_checkpoint_type()
                self.logger.info(f"Checkpoint type: {checkpoint_type}")
                
                # Handle different types of checkpoints
                if checkpoint_type == "verification_code":
                    result = await self._handle_verification_code_checkpoint()
                elif checkpoint_type == "security_questions":
                    result = await self._handle_security_questions_checkpoint()
                elif checkpoint_type == "device_confirmation":
                    result = await self._handle_device_confirmation_checkpoint()
                elif checkpoint_type == "captcha":
                    result = await self._handle_captcha_checkpoint()
                else:
                    result = await self._handle_generic_checkpoint()
                
                if result["success"]:
                    self.logger.info("Security checkpoint resolved successfully")
                    return result
                
                # If not successful and we have more attempts, wait and retry
                if attempt < max_attempts - 1:
                    self.logger.info(f"Checkpoint resolution failed, retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    
                    # Refresh page content for next attempt
                    try:
                        await self.crawler_engine.page.reload()
                        await asyncio.sleep(3)
                    except Exception as e:
                        self.logger.warning(f"Failed to refresh page: {e}")
                
            # All attempts failed
            self.logger.error(f"Failed to resolve security checkpoint after {max_attempts} attempts")
            return {"handled": True, "success": False, "reason": f"Checkpoint resolution failed after {max_attempts} attempts"}
                
        except Exception as e:
            error_msg = f"Error handling security checkpoint: {str(e)}"
            self.logger.error(error_msg)
            return {"handled": True, "success": False, "reason": error_msg}
    
    async def _identify_checkpoint_type(self) -> str:
        """Identify the type of security checkpoint"""
        try:
            page_content = await self.crawler_engine.page.content()
            
            # Check for verification code input
            if any(phrase in page_content.lower() for phrase in ["verification code", "security code", "enter code"]):
                return "verification_code"
            
            # Check for security questions
            if any(phrase in page_content.lower() for phrase in ["security question", "answer question", "memorable question"]):
                return "security_questions"
            
            # Check for device confirmation
            if any(phrase in page_content.lower() for phrase in ["confirm device", "trust device", "recognize device"]):
                return "device_confirmation"
            
            # Check for captcha
            if any(phrase in page_content.lower() for phrase in ["captcha", "prove you're human", "verify you're human"]):
                return "captcha"
            
            return "unknown"
            
        except Exception as e:
            self.logger.error(f"Error identifying checkpoint type: {e}")
            return "unknown"
    
    async def _handle_verification_code_checkpoint(self) -> dict:
        """Handle verification code checkpoint"""
        try:
            self.logger.info("Handling verification code checkpoint...")
            
            # Look for verification code input field
            code_input = await self.crawler_engine.page.query_selector("input[name='code'], input[placeholder*='code'], input[type='text']")
            if not code_input:
                return {"handled": True, "success": False, "reason": "Verification code input field not found"}
            
            # Check if we have verification code in config
            credentials = self.config.get("login", {})
            verification_code = credentials.get("verification_code")
            
            if verification_code:
                # Fill in the verification code
                await code_input.click()
                await code_input.fill(verification_code)
                await asyncio.sleep(1)
                
                # Look for submit button
                submit_button = await self.crawler_engine.page.query_selector("button[type='submit'], input[type='submit'], button:contains('Continue')")
                if submit_button:
                    await submit_button.click()
                    await asyncio.sleep(5)
                    
                    # Check if checkpoint was resolved
                    if await self._is_checkpoint_resolved():
                        return {"handled": True, "success": True, "reason": "Verification code accepted"}
                    else:
                        return {"handled": True, "success": False, "reason": "Verification code rejected"}
                else:
                    return {"handled": True, "success": False, "reason": "Submit button not found"}
            else:
                return {"handled": True, "success": False, "reason": "Verification code required but not provided in config"}
                
        except Exception as e:
            error_msg = f"Error handling verification code checkpoint: {str(e)}"
            self.logger.error(error_msg)
            return {"handled": True, "success": False, "reason": error_msg}
    
    async def _handle_security_questions_checkpoint(self) -> dict:
        """Handle security questions checkpoint"""
        try:
            self.logger.info("Handling security questions checkpoint...")
            
            # Look for security question input fields
            question_inputs = await self.crawler_engine.page.query_selector_all("input[type='text'], textarea")
            
            if not question_inputs:
                return {"handled": True, "success": False, "reason": "Security question input fields not found"}
            
            # Check if we have security answers in config
            credentials = self.config.get("login", {})
            security_answers = credentials.get("security_answers", {})
            
            if not security_answers:
                return {"handled": True, "success": False, "reason": "Security answers required but not provided in config"}
            
            # Try to fill in security answers
            for i, input_field in enumerate(question_inputs):
                try:
                    # Get the question text (usually above or near the input)
                    question_element = await input_field.evaluate("el => el.previousElementSibling ? el.previousElementSibling.textContent : ''")
                    question_text = question_element.lower() if question_element else ""
                    
                    # Try to find matching answer
                    answer = None
                    for question_key, answer_value in security_answers.items():
                        if question_key.lower() in question_text:
                            answer = answer_value
                            break
                    
                    if answer:
                        await input_field.click()
                        await input_field.fill(answer)
                        await asyncio.sleep(1)
                    
                except Exception as e:
                    self.logger.debug(f"Error filling security answer {i}: {e}")
                    continue
            
            # Look for submit button
            submit_button = await self.crawler_engine.page.query_selector("button[type='submit'], input[type='submit']")
            if submit_button:
                await submit_button.click()
                await asyncio.sleep(5)
                
                # Check if checkpoint was resolved
                if await self._is_checkpoint_resolved():
                    return {"handled": True, "success": True, "reason": "Security questions answered successfully"}
                else:
                    return {"handled": True, "success": False, "reason": "Security questions answered incorrectly"}
            else:
                return {"handled": True, "success": False, "reason": "Submit button not found"}
                
        except Exception as e:
            error_msg = f"Error handling security questions checkpoint: {str(e)}"
            self.logger.error(error_msg)
            return {"handled": True, "success": False, "reason": error_msg}
    
    async def _handle_device_confirmation_checkpoint(self) -> dict:
        """Handle device confirmation checkpoint"""
        try:
            self.logger.info("Handling device confirmation checkpoint...")
            
            # Look for various confirmation button patterns
            confirm_button_patterns = [
                # Text-based selectors
                "button:contains('This was me')",
                "button:contains('Yes, this was me')",
                "button:contains('Confirm')",
                "button:contains('Continue')",
                "button:contains('Trust')",
                "button:contains('Allow')",
                "button:contains('Proceed')",
                
                # Input-based selectors
                "input[value*='This was me']",
                "input[value*='Yes']",
                "input[value*='Confirm']",
                
                # Generic button selectors
                "button[type='submit']",
                "input[type='submit']",
                
                # Facebook-specific selectors
                "[data-testid='checkpoint_submit_button']",
                "[data-testid='checkpoint_continue_button']",
                "button[data-testid*='submit']",
                "button[data-testid*='continue']"
            ]
            
            # Also try to find buttons by their text content
            try:
                all_buttons = await self.crawler_engine.page.query_selector_all("button, input[type='submit']")
                for button in all_buttons:
                    try:
                        button_text = await button.text_content()
                        if button_text:
                            button_text_lower = button_text.lower()
                            if any(phrase in button_text_lower for phrase in [
                                "this was me", "yes", "confirm", "continue", "trust", "allow", "proceed"
                            ]):
                                self.logger.info(f"Found confirmation button: {button_text}")
                                await button.click()
                                await asyncio.sleep(5)
                                
                                # Check if checkpoint was resolved
                                if await self._is_checkpoint_resolved():
                                    return {"handled": True, "success": True, "reason": f"Device confirmed successfully via button: {button_text}"}
                                else:
                                    return {"handled": True, "success": False, "reason": "Device confirmation failed"}
                    except Exception as e:
                        self.logger.debug(f"Error processing button: {e}")
                        continue
            except Exception as e:
                self.logger.debug(f"Error finding buttons by text: {e}")
            
            # Try CSS selectors as fallback
            for button_selector in confirm_button_patterns:
                try:
                    button = await self.crawler_engine.page.query_selector(button_selector)
                    if button:
                        button_text = await button.text_content()
                        self.logger.info(f"Found confirmation button via selector: {button_text}")
                        await button.click()
                        await asyncio.sleep(5)
                        
                        # Check if checkpoint was resolved
                        if await self._is_checkpoint_resolved():
                            return {"handled": True, "success": True, "reason": f"Device confirmed successfully via selector: {button_selector}"}
                        else:
                            return {"handled": True, "success": False, "reason": "Device confirmation failed"}
                except Exception as e:
                    self.logger.debug(f"Selector {button_selector} failed: {e}")
                    continue
            
            return {"handled": True, "success": False, "reason": "Device confirmation button not found"}
            
        except Exception as e:
            error_msg = f"Error handling device confirmation checkpoint: {str(e)}"
            self.logger.error(error_msg)
            return {"handled": True, "success": False, "reason": error_msg}
    
    async def _handle_captcha_checkpoint(self) -> dict:
        """Handle captcha checkpoint"""
        try:
            self.logger.info("Handling captcha checkpoint...")
            
            # Look for captcha input field
            captcha_input = await self.crawler_engine.page.query_selector("input[name='captcha'], input[placeholder*='captcha'], input[placeholder*='code']")
            if not captcha_input:
                return {"handled": True, "success": False, "reason": "Captcha input field not found"}
            
            # Check if we have captcha solution in config
            credentials = self.config.get("login", {})
            captcha_solution = credentials.get("captcha_solution")
            
            if captcha_solution:
                # Fill in the captcha solution
                await captcha_input.click()
                await captcha_input.fill(captcha_solution)
                await asyncio.sleep(1)
                
                # Look for submit button
                submit_button = await self.crawler_engine.page.query_selector("button[type='submit'], input[type='submit']")
                if submit_button:
                    await submit_button.click()
                    await asyncio.sleep(5)
                    
                    # Check if checkpoint was resolved
                    if await self._is_checkpoint_resolved():
                        return {"handled": True, "success": True, "reason": "Captcha solved successfully"}
                    else:
                        return {"handled": True, "success": False, "reason": "Captcha solution rejected"}
                else:
                    return {"handled": True, "success": False, "reason": "Submit button not found"}
            else:
                return {"handled": True, "success": False, "reason": "Captcha solution required but not provided in config"}
                
        except Exception as e:
            error_msg = f"Error handling captcha checkpoint: {str(e)}"
            self.logger.error(error_msg)
            return {"handled": True, "success": False, "reason": error_msg}
    
    async def _handle_generic_checkpoint(self) -> dict:
        """Handle generic checkpoint when type cannot be determined"""
        try:
            self.logger.info("Handling generic checkpoint...")
            
            # Try to find any submit/continue button
            submit_buttons = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Continue')",
                "button:contains('Submit')",
                "button:contains('Next')"
            ]
            
            for button_selector in submit_buttons:
                try:
                    button = await self.crawler_engine.page.query_selector(button_selector)
                    if button:
                        await button.click()
                        await asyncio.sleep(5)
                        
                        # Check if checkpoint was resolved
                        if await self._is_checkpoint_resolved():
                            return {"handled": True, "success": True, "reason": "Generic checkpoint resolved successfully"}
                        else:
                            return {"handled": True, "success": False, "reason": "Generic checkpoint resolution failed"}
                except Exception:
                    continue
            
            return {"handled": True, "success": False, "reason": "No action buttons found for generic checkpoint"}
            
        except Exception as e:
            error_msg = f"Error handling generic checkpoint: {str(e)}"
            self.logger.error(error_msg)
            return {"handled": True, "success": False, "reason": error_msg}
    
    async def _is_checkpoint_resolved(self) -> bool:
        """Check if security checkpoint has been resolved"""
        try:
            await asyncio.sleep(2)
            
            # Check if we're redirected away from checkpoint page
            current_url = self.crawler_engine.page.url
            if "checkpoint" not in current_url.lower() and "login" not in current_url.lower():
                return True
            
            # Check for success indicators
            success_indicators = [
                "div[data-testid='pagelet_bluebar']",
                "div[data-testid='blue_bar_profile_link']",
                "div[aria-label='Your profile']"
            ]
            
            for indicator in success_indicators:
                if await self.crawler_engine.page.query_selector(indicator):
                    return True
            
            # Check for error messages that indicate checkpoint failed
            error_indicators = [
                "div[data-testid='error_box']",
                "div[class*='error']",
                "div[class*='alert']"
            ]
            
            for indicator in error_indicators:
                error_element = await self.crawler_engine.page.query_selector(indicator)
                if error_element:
                    error_text = await error_element.text_content()
                    if error_text and any(phrase in error_text.lower() for phrase in ["incorrect", "wrong", "failed", "error"]):
                        return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking checkpoint resolution: {e}")
            return False
    
    async def _extract_search_results(self, max_results: int) -> List[str]:
        """Extract video URLs from search results page"""
        try:
            video_urls = []
            
            # Wait for page to load completely
            await asyncio.sleep(3)
            
            # Look for video links in search results with more comprehensive selectors
            video_selectors = [
                "a[href*='/videos/']",
                "a[href*='/watch']",
                "a[href*='/permalink/']",
                "a[href*='/video.php']",
                "[data-testid='video_container'] a",
                "[data-testid='post_container'] a[href*='/videos/']",
                "div[role='article'] a[href*='/videos/']",
                "div[data-testid='post_message'] a[href*='/videos/']"
            ]
            
            for selector in video_selectors:
                try:
                    elements = await self.crawler_engine.page.query_selector_all(selector)
                    
                    for element in elements:
                        if len(video_urls) >= max_results:
                            break
                        
                        href = await element.get_attribute("href")
                        if href and self._is_valid_video_url(href):
                            full_url = self._make_absolute_url(href)
                            if full_url not in video_urls:
                                video_urls.append(full_url)
                
                except Exception as e:
                    self.logger.debug(f"Failed to extract with selector {selector}: {e}")
                    continue
            
            # If no videos found, try to look for posts that might contain videos
            if not video_urls:
                self.logger.info("No direct video links found, looking for post content...")
                try:
                    # Look for posts that might contain video content
                    post_selectors = [
                        "div[role='article']",
                        "[data-testid='post_container']",
                        "div[data-testid='post_message']"
                    ]
                    
                    for selector in post_selectors:
                        posts = await self.crawler_engine.page.query_selector_all(selector)
                        for post in posts:
                            if len(video_urls) >= max_results:
                                break
                            
                            # Check if post contains video indicators
                            video_indicators = await post.query_selector_all("video, [data-testid*='video'], [aria-label*='video']")
                            if video_indicators:
                                # Try to find the post link
                                post_link = await post.query_selector("a[href*='/permalink/'], a[href*='/posts/']")
                                if post_link:
                                    href = await post_link.get_attribute("href")
                                    if href:
                                        full_url = self._make_absolute_url(href)
                                        if full_url not in video_urls:
                                            video_urls.append(full_url)
                
                except Exception as e:
                    self.logger.debug(f"Failed to extract from posts: {e}")
            
            # Remove duplicates and limit results
            unique_urls = list(dict.fromkeys(video_urls))  # Preserve order
            self.logger.info(f"Found {len(unique_urls)} unique video URLs")
            return unique_urls[:max_results]
            
        except Exception as e:
            self.logger.error(f"Failed to extract search results: {e}")
            return []
    
    def _is_valid_video_url(self, url: str) -> bool:
        """Check if URL is a valid Facebook video URL"""
        video_patterns = [
            r'/videos/\d+/',
            r'/watch\?v=\d+',
            r'/permalink/\d+/',
            r'/video\.php\?v=\d+'
        ]
        
        return any(re.search(pattern, url) for pattern in video_patterns)
    
    def _make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute URL"""
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return f"https://www.facebook.com{url}"
        else:
            return f"https://www.facebook.com/{url}"
    
    async def download_videos(self, videos: List[VideoMetadata], 
                            output_dir: Optional[str] = None) -> List[VideoMetadata]:
        """
        Download multiple videos
        
        Args:
            videos: List of VideoMetadata objects
            output_dir: Output directory for downloads
            
        Returns:
            List of updated VideoMetadata objects
        """
        if not output_dir:
            output_dir = config.get("storage.video_path", "./data/videos")
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        downloaded_videos = []
        
        for i, video in enumerate(videos):
            try:
                self.logger.info(f"Downloading video {i+1}/{len(videos)}: {video.title}")
                
                # Generate output filename
                filename = self._generate_filename(video)
                output_path = Path(output_dir) / filename
                
                # Download video
                success = await self.video_extractor.download_video(video, str(output_path))
                
                if success:
                    self.stats["total_downloads"] += 1
                    downloaded_videos.append(video)
                else:
                    self.stats["failed_downloads"] += 1
                
                # Add delay between downloads
                if i < len(videos) - 1:
                    delay = random.randint(2, 5)
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"Failed to download video {video.title}: {e}")
                video.status = "download_failed"
                video.error_message = str(e)
                self.stats["failed_downloads"] += 1
                continue
        
        self.logger.info(f"Download completed. Success: {len(downloaded_videos)}, Failed: {len(videos) - len(downloaded_videos)}")
        return downloaded_videos
    
    def _generate_filename(self, video: VideoMetadata) -> str:
        """Generate filename for video download"""
        # Clean title for filename
        clean_title = "".join(c for c in video.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_title = clean_title[:50]  # Limit length
        
        # Add video ID and extension
        filename = f"{clean_title}_{video.video_id}.mp4"
        
        return filename
    
    async def process_video_urls(self, urls: List[str], download: bool = True) -> List[VideoMetadata]:
        """
        Process a list of video URLs
        
        Args:
            urls: List of Facebook video URLs
            download: Whether to download videos after extraction
            
        Returns:
            List of VideoMetadata objects
        """
        try:
            self.logger.info(f"Processing {len(urls)} video URLs")
            
            # Extract metadata
            videos = await self.video_extractor.extract_multiple_videos(urls)
            
            # Update statistics
            self.stats["total_videos_processed"] += len(videos)
            self.stats["successful_extractions"] += len([v for v in videos if v.status == "extracted"])
            self.stats["failed_extractions"] += len([v for v in videos if v.status == "failed"])
            
            # Download if requested
            if download and videos:
                downloaded_videos = await self.download_videos(videos)
                return downloaded_videos
            
            return videos
            
        except Exception as e:
            self.logger.error(f"Failed to process video URLs: {e}")
            return []
    
    async def rotate_fingerprint(self) -> Dict[str, Any]:
        """Rotate browser fingerprint"""
        try:
            new_fingerprint = self.fingerprint_manager.rotate_fingerprint()
            
            # Apply new fingerprint if crawler is running
            if self.crawler_engine and self.crawler_engine.context:
                await self._apply_fingerprint()
            
            self.logger.info("Browser fingerprint rotated successfully")
            return new_fingerprint
            
        except Exception as e:
            self.logger.error(f"Failed to rotate fingerprint: {e}")
            return {}
    
    async def rotate_proxy(self) -> Optional[Dict[str, str]]:
        """Rotate to next proxy"""
        try:
            new_proxy = self.proxy_manager.get_proxy()
            if new_proxy:
                # Restart crawler engine with new proxy
                await self.stop()
                await self.start()
                
                self.logger.info(f"Rotated to new proxy: {new_proxy.url}")
                return self.proxy_manager.get_proxy_dict(new_proxy)
            else:
                self.logger.warning("No working proxy available for rotation")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to rotate proxy: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current crawler status"""
        status = {
            "crawler_running": self.crawler_engine is not None and self.crawler_engine.is_running,
            "fingerprint_stats": self.fingerprint_manager.get_fingerprint_stats(),
            "proxy_stats": self.proxy_manager.get_proxy_stats(),
            "extraction_stats": self.stats.copy()
        }
        
        if self.crawler_engine:
            status["crawler_status"] = self.crawler_engine.get_status()
        
        return status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = {}
        
        if self.crawler_engine:
            metrics["crawler_metrics"] = self.crawler_engine.logger.get_performance_metrics()
        
        metrics["extraction_stats"] = self.stats.copy()
        
        return metrics
    
    async def export_metadata(self, videos: List[VideoMetadata], filepath: str) -> bool:
        """
        Export video metadata to JSON file
        
        Args:
            videos: List of VideoMetadata objects
            filepath: Output file path
            
        Returns:
            True if export successful
        """
        try:
            # Convert to dictionaries
            data = [video.to_dict() for video in videos]
            
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Metadata exported to: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export metadata: {e}")
            return False
    
    async def import_metadata(self, filepath: str) -> List[VideoMetadata]:
        """
        Import video metadata from JSON file
        
        Args:
            filepath: Input file path
            
        Returns:
            List of VideoMetadata objects
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            videos = [VideoMetadata.from_dict(item) for item in data]
            
            self.logger.info(f"Metadata imported from: {filepath}. {len(videos)} videos loaded.")
            return videos
            
        except Exception as e:
            self.logger.error(f"Failed to import metadata: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        health_status = {
            "overall_status": "healthy",
            "components": {},
            "recommendations": []
        }
        
        try:
            # Check crawler engine
            if self.crawler_engine and self.crawler_engine.is_healthy():
                health_status["components"]["crawler_engine"] = "healthy"
            else:
                health_status["components"]["crawler_engine"] = "unhealthy"
                health_status["overall_status"] = "unhealthy"
                health_status["recommendations"].append("Restart crawler engine")
            
            # Check proxy health
            proxy_stats = self.proxy_manager.get_proxy_stats()
            if proxy_stats.get("working_ratio", 0) > 0.5:
                health_status["components"]["proxy_pool"] = "healthy"
            else:
                health_status["components"]["proxy_pool"] = "unhealthy"
                health_status["overall_status"] = "degraded"
                health_status["recommendations"].append("Check proxy health and add more proxies")
            
            # Check fingerprint
            fingerprint_stats = self.fingerprint_manager.get_fingerprint_stats()
            if fingerprint_stats.get("total_fingerprints", 0) > 0:
                health_status["components"]["fingerprint_manager"] = "healthy"
            else:
                health_status["components"]["fingerprint_manager"] = "unhealthy"
                health_status["overall_status"] = "unhealthy"
                health_status["recommendations"].append("Check fingerprint generation")
            
            # Check storage
            storage_config = config.get_storage_config()
            video_path = Path(storage_config.get("video_path", "./data/videos"))
            if video_path.exists() and video_path.is_dir():
                health_status["components"]["storage"] = "healthy"
            else:
                health_status["components"]["storage"] = "unhealthy"
                health_status["overall_status"] = "degraded"
                health_status["recommendations"].append("Check storage directory permissions")
            
        except Exception as e:
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)
            self.logger.error(f"Health check failed: {e}")
        
        return health_status
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive crawler statistics including advanced anti-detection stats"""
        if self.stats["start_time"]:
            self.stats["current_session_duration"] = time.time() - self.stats["start_time"]
        
        # Add advanced anti-detection stats
        advanced_stats = {
            **self.stats.copy(),
            "advanced_anti_detection": {
                "fingerprint_profile": self.advanced_fingerprint_manager.get_current_profile(),
                "behavior_stats": self.advanced_behavior_simulator.get_behavior_stats(),
                "network_profile": self.network_fingerprint_spoofer.get_current_profile(),
                "session_stats": self.session_manager.get_account_stats()
            }
        }
        
        return advanced_stats


# Convenience functions for common operations
async def create_crawler(config_overrides: Optional[Dict[str, Any]] = None) -> FacebookVideoCrawler:
    """Create and start a crawler instance"""
    crawler = FacebookVideoCrawler(config_overrides)
    await crawler.start()
    return crawler


async def search_and_download(keyword: str, max_results: int = 50, 
                            region: Optional[str] = None, 
                            download: bool = True) -> List[VideoMetadata]:
    """Search for videos and optionally download them"""
    async with FacebookVideoCrawler() as crawler:
        # Search for videos
        videos = await crawler.search_videos(keyword, max_results, region)
        
        if download and videos:
            # Download videos
            downloaded_videos = await crawler.download_videos(videos)
            return downloaded_videos
        
        return videos


async def process_urls(urls: List[str], download: bool = True) -> List[VideoMetadata]:
    """Process a list of video URLs and optionally download them"""
    async with FacebookVideoCrawler() as crawler:
        return await crawler.process_video_urls(urls, download)


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create crawler
        async with FacebookVideoCrawler() as crawler:
            # Search for videos
            videos = await crawler.search_videos("美食制作", max_results=10)
            
            # Download videos
            if videos:
                downloaded = await crawler.download_videos(videos)
                print(f"Downloaded {len(downloaded)} videos")
            
            # Get status
            status = crawler.get_status()
            print(f"Crawler status: {status}")
    
    # Run example
    asyncio.run(main())
