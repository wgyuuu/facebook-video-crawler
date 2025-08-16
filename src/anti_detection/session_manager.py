"""
Session Manager for Facebook Video Crawler System
Provides session hijacking, reuse, and multi-account rotation capabilities
"""

import json
import time
import random
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

from ..utils.logger import get_logger
from ..utils.config_manager import config


class SessionManager:
    """Manages Facebook sessions including hijacking and rotation"""
    
    def __init__(self):
        """Initialize session manager"""
        self.logger = get_logger("session_manager")
        self.config = config.get_anti_detection_config().get("session_management", {})
        
        # Session storage
        self.session_storage: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Account rotation
        self.accounts = self._load_accounts()
        self.current_account_index = 0
        self.account_usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # Session persistence
        self.session_file = Path("data/sessions/session_data.json")
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing sessions
        self._load_persisted_sessions()
        
        self.logger.info("Session manager initialized")
    
    def _load_accounts(self) -> List[Dict[str, Any]]:
        """Load multiple Facebook accounts"""
        accounts_config = self.config.get("accounts", [])
        
        if not accounts_config:
            # Fallback to single account from main config
            facebook_config = config.get_facebook_config()
            if facebook_config.get("login", {}).get("enabled"):
                accounts_config = [{
                    "email": facebook_config["login"]["email"],
                    "password": facebook_config["login"]["password"],
                    "proxy": None,
                    "user_agent": None,
                    "device_profile": "windows_desktop"
                }]
        
        # Add default accounts if none configured
        if not accounts_config:
            accounts_config = [
                {
                    "email": "account1@example.com",
                    "password": "password1",
                    "proxy": "proxy1:port",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "device_profile": "windows_desktop"
                },
                {
                    "email": "account2@example.com", 
                    "password": "password2",
                    "proxy": "proxy2:port",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "device_profile": "macbook_pro"
                }
            ]
        
        return accounts_config
    
    def _load_persisted_sessions(self) -> None:
        """Load persisted sessions from file"""
        try:
            if self.session_file.exists():
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.session_storage = data.get("sessions", {})
                    self.account_usage_stats = data.get("account_stats", {})
                
                self.logger.info(f"Loaded {len(self.session_storage)} persisted sessions")
        except Exception as e:
            self.logger.warning(f"Failed to load persisted sessions: {e}")
    
    def _save_persisted_sessions(self) -> None:
        """Save sessions to file"""
        try:
            data = {
                "sessions": self.session_storage,
                "account_stats": self.account_usage_stats,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.debug("Sessions persisted to file")
        except Exception as e:
            self.logger.error(f"Failed to save sessions: {e}")
    
    async def extract_session_data(self, page) -> Dict[str, Any]:
        """Extract complete session data from page"""
        try:
            # Get cookies
            cookies = await page.context.cookies()
            
            # Get localStorage
            local_storage = await page.evaluate("""
                () => {
                    const data = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        data[key] = localStorage.getItem(key);
                    }
                    return data;
                }
            """)
            
            # Get sessionStorage
            session_storage = await page.evaluate("""
                () => {
                    const data = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        data[key] = sessionStorage.getItem(key);
                    }
                    return data;
                }
            """)
            
            # Get current URL and page info
            current_url = page.url
            page_title = await page.title()
            
            session_data = {
                'cookies': cookies,
                'localStorage': local_storage,
                'sessionStorage': session_storage,
                'url': current_url,
                'title': page_title,
                'timestamp': time.time(),
                'extracted_at': datetime.now().isoformat()
            }
            
            self.logger.debug("Session data extracted successfully")
            return session_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract session data: {e}")
            return {}
    
    async def restore_session(self, page, session_data: Dict[str, Any]) -> bool:
        """Restore session data to page"""
        try:
            # Restore cookies
            if session_data.get('cookies'):
                await page.context.add_cookies(session_data['cookies'])
            
            # Restore localStorage
            if session_data.get('localStorage'):
                for key, value in session_data['localStorage'].items():
                    if value is not None:
                        await page.evaluate(f"localStorage.setItem('{key}', '{value}')")
            
            # Restore sessionStorage
            if session_data.get('sessionStorage'):
                for key, value in session_data['sessionStorage'].items():
                    if value is not None:
                        await page.evaluate(f"sessionStorage.setItem('{key}', '{value}')")
            
            # Navigate to stored URL if different
            if session_data.get('url') and page.url != session_data['url']:
                await page.goto(session_data['url'])
            
            self.logger.info("Session restored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore session: {e}")
            return False
    
    def store_session(self, account_email: str, session_data: Dict[str, Any]) -> None:
        """Store session data for an account"""
        try:
            # Clean sensitive data
            clean_session = self._clean_session_data(session_data)
            
            # Store with account identifier
            session_id = f"{account_email}_{int(time.time())}"
            self.session_storage[session_id] = {
                "account_email": account_email,
                "session_data": clean_session,
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            # Update account usage stats
            if account_email not in self.account_usage_stats:
                self.account_usage_stats[account_email] = {
                    "total_sessions": 0,
                    "last_login": None,
                    "success_rate": 0.0,
                    "total_usage_time": 0
                }
            
            self.account_usage_stats[account_email]["total_sessions"] += 1
            self.account_usage_stats[account_email]["last_login"] = datetime.now().isoformat()
            
            # Save to file
            self._save_persisted_sessions()
            
            self.logger.info(f"Session stored for account: {account_email}")
            
        except Exception as e:
            self.logger.error(f"Failed to store session: {e}")
    
    def _clean_session_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean sensitive data from session"""
        clean_data = session_data.copy()
        
        # Remove sensitive cookie data
        if 'cookies' in clean_data:
            for cookie in clean_data['cookies']:
                if 'value' in cookie and any(sensitive in cookie['name'].lower() 
                                           for sensitive in ['password', 'token', 'secret']):
                    cookie['value'] = '***REDACTED***'
        
        # Remove sensitive storage data
        sensitive_keys = ['password', 'token', 'secret', 'key', 'auth']
        for storage_type in ['localStorage', 'sessionStorage']:
            if storage_type in clean_data:
                clean_storage = {}
                for key, value in clean_data[storage_type].items():
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        clean_storage[key] = '***REDACTED***'
                    else:
                        clean_storage[key] = value
                clean_data[storage_type] = clean_storage
        
        return clean_data
    
    def get_available_sessions(self, account_email: str = None) -> List[Dict[str, Any]]:
        """Get available sessions for an account"""
        try:
            if account_email:
                # Filter by specific account
                sessions = [
                    {"session_id": sid, **data} 
                    for sid, data in self.session_storage.items()
                    if data.get("account_email") == account_email
                ]
            else:
                # Get all sessions
                sessions = [
                    {"session_id": sid, **data} 
                    for sid, data in self.session_storage.items()
                ]
            
            # Sort by last used (most recent first)
            sessions.sort(key=lambda x: x.get("last_used", ""), reverse=True)
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to get available sessions: {e}")
            return []
    
    async def rotate_account(self, crawler) -> Tuple[bool, str]:
        """Rotate to next available account"""
        try:
            if not self.accounts:
                return False, "No accounts configured"
            
            # Get next account
            account = self.accounts[self.current_account_index]
            account_email = account["email"]
            
            self.logger.info(f"Rotating to account: {account_email}")
            
            # Update proxy if configured
            if account.get("proxy") and hasattr(crawler, 'proxy_manager'):
                await crawler.proxy_manager.set_proxy(account["proxy"])
            
            # Update user agent if configured
            if account.get("user_agent") and hasattr(crawler, 'fingerprint_manager'):
                await crawler.fingerprint_manager.set_user_agent(account["user_agent"])
            
            # Update device profile if configured
            if account.get("device_profile") and hasattr(crawler, 'advanced_fingerprint_manager'):
                await crawler.advanced_fingerprint_manager.apply_device_profile(
                    crawler.crawler_engine.page, 
                    account["device_profile"]
                )
            
            # Try to restore existing session first
            available_sessions = self.get_available_sessions(account_email)
            if available_sessions:
                session_data = available_sessions[0]["session_data"]
                if await self.restore_session(crawler.crawler_engine.page, session_data):
                    self.logger.info(f"Restored existing session for {account_email}")
                    
                    # Update usage stats
                    session_id = available_sessions[0]["session_id"]
                    self.session_storage[session_id]["last_used"] = datetime.now().isoformat()
                    self.session_storage[session_id]["usage_count"] += 1
                    self._save_persisted_sessions()
                    
                    return True, f"Session restored for {account_email}"
            
            # If no session available, attempt login
            if hasattr(crawler, '_attempt_login'):
                login_result = await crawler._attempt_login(
                    account["email"], 
                    account["password"]
                )
                
                if login_result.get("success"):
                    # Extract and store new session
                    new_session = await self.extract_session_data(crawler.crawler_engine.page)
                    self.store_session(account_email, new_session)
                    
                    # Move to next account
                    self.current_account_index = (self.current_account_index + 1) % len(self.accounts)
                    
                    return True, f"Login successful for {account_email}"
                else:
                    return False, f"Login failed for {account_email}: {login_result.get('reason', 'Unknown error')}"
            
            return False, "Login method not available"
            
        except Exception as e:
            self.logger.error(f"Account rotation failed: {e}")
            return False, f"Rotation error: {str(e)}"
    
    def get_account_stats(self) -> Dict[str, Any]:
        """Get account usage statistics"""
        return {
            "total_accounts": len(self.accounts),
            "current_account_index": self.current_account_index,
            "account_usage_stats": self.account_usage_stats.copy(),
            "total_sessions": len(self.session_storage),
            "active_sessions": len(self.active_sessions)
        }
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up expired sessions"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            expired_sessions = []
            
            for session_id, session_data in self.session_storage.items():
                if session_data.get("timestamp", 0) < cutoff_time:
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            for session_id in expired_sessions:
                del self.session_storage[session_id]
            
            if expired_sessions:
                self._save_persisted_sessions()
                self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
            return len(expired_sessions)
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0


# Global session manager instance
session_manager = SessionManager()
