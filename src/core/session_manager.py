"""
Session Manager for Facebook Video Crawler System
Manages browser sessions and cookies
"""

import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.config_manager import config


class SessionManager:
    """Manages browser sessions and cookies"""
    
    def __init__(self):
        """Initialize session manager"""
        self.logger = get_logger("session_manager")
        self.config = config.get_crawler_config()
        
        # Session storage
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: List[str] = []
        
        # Cookie storage
        self.cookies_file = Path(config.get("paths.cookies_file", "data/cookies.json"))
        self.cookies_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Session manager initialized")
    
    def create_session(self, session_id: str, browser_type: str = "chromium") -> Dict[str, Any]:
        """
        Create a new browser session
        
        Args:
            session_id: Unique session identifier
            browser_type: Type of browser to use
            
        Returns:
            Session configuration
        """
        session_config = {
            "id": session_id,
            "browser_type": browser_type,
            "created_at": time.time(),
            "last_used": time.time(),
            "cookies": {},
            "user_agent": None,
            "viewport": None,
            "proxy": None,
            "status": "active"
        }
        
        self.sessions[session_id] = session_config
        self.active_sessions.append(session_id)
        
        self.logger.info(f"Created session: {session_id} ({browser_type})")
        return session_config
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        if session_id in self.sessions:
            # Update last used time
            self.sessions[session_id]["last_used"] = time.time()
            return self.sessions[session_id]
        return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session configuration"""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]["last_used"] = time.time()
            self.logger.debug(f"Updated session: {session_id}")
            return True
        return False
    
    def close_session(self, session_id: str) -> bool:
        """Close and cleanup session"""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "closed"
            self.sessions[session_id]["closed_at"] = time.time()
            
            if session_id in self.active_sessions:
                self.active_sessions.remove(session_id)
            
            self.logger.info(f"Closed session: {session_id}")
            return True
        return False
    
    def save_cookies(self, session_id: str, cookies: List[Dict[str, Any]]) -> bool:
        """Save cookies for a session"""
        try:
            if session_id in self.sessions:
                self.sessions[session_id]["cookies"] = cookies
                
                # Save to file
                self._save_cookies_to_file()
                
                self.logger.debug(f"Saved {len(cookies)} cookies for session: {session_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to save cookies: {e}")
        
        return False
    
    def load_cookies(self, session_id: str) -> List[Dict[str, Any]]:
        """Load cookies for a session"""
        if session_id in self.sessions:
            return self.sessions[session_id].get("cookies", [])
        return []
    
    def _save_cookies_to_file(self) -> None:
        """Save all cookies to file"""
        try:
            all_cookies = {}
            for session_id, session in self.sessions.items():
                if session.get("cookies"):
                    all_cookies[session_id] = session["cookies"]
            
            with open(self.cookies_file, 'w') as f:
                json.dump(all_cookies, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save cookies to file: {e}")
    
    def _load_cookies_from_file(self) -> None:
        """Load cookies from file"""
        try:
            if self.cookies_file.exists():
                with open(self.cookies_file, 'r') as f:
                    all_cookies = json.load(f)
                
                for session_id, cookies in all_cookies.items():
                    if session_id in self.sessions:
                        self.sessions[session_id]["cookies"] = cookies
                        
        except Exception as e:
            self.logger.error(f"Failed to load cookies from file: {e}")
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return self.active_sessions.copy()
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        closed_sessions = []
        for session_id, session in self.sessions.items():
            if session.get("status") == "closed":
                closed_at = session.get("closed_at", 0)
                if current_time - closed_at > max_age_seconds:
                    closed_sessions.append(session_id)
        
        # Remove old sessions
        for session_id in closed_sessions:
            del self.sessions[session_id]
        
        if closed_sessions:
            self.logger.info(f"Cleaned up {len(closed_sessions)} old sessions")
        
        return len(closed_sessions)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        total_sessions = len(self.sessions)
        active_sessions = len(self.active_sessions)
        closed_sessions = total_sessions - active_sessions
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "closed_sessions": closed_sessions,
            "browser_types": list(set(s.get("browser_type") for s in self.sessions.values()))
        }


# Global session manager instance
session_manager = SessionManager()


def create_session(session_id: str, browser_type: str = "chromium") -> Dict[str, Any]:
    """Global function to create session"""
    return session_manager.create_session(session_id, browser_type)


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Global function to get session"""
    return session_manager.get_session(session_id)


def close_session(session_id: str) -> bool:
    """Global function to close session"""
    return session_manager.close_session(session_id)
