"""
Enhanced Error Handler for Facebook Video Crawler
Provides specialized error handling for Facebook-specific issues
"""

import asyncio
import time
from typing import Optional, Callable, Any
from ..utils.logger import get_logger


class FacebookErrorHandler:
    """Specialized error handler for Facebook crawling operations"""
    
    def __init__(self):
        self.logger = get_logger("facebook_error_handler")
        self.retry_delays = [5, 10, 20, 30, 60]  # Progressive delays
    
    async def retry_with_backoff(self, 
                                operation: Callable, 
                                max_retries: int = 5,
                                operation_name: str = "operation") -> Optional[Any]:
        """
        Retry operation with exponential backoff
        
        Args:
            operation: Async function to retry
            max_retries: Maximum number of retry attempts
            operation_name: Name of operation for logging
            
        Returns:
            Operation result or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                return await operation()
                
            except Exception as e:
                error_msg = str(e)
                self.logger.warning(f"{operation_name} attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < max_retries - 1:
                    # Determine delay based on error type
                    delay = self._get_delay_for_error(error_msg, attempt)
                    self.logger.info(f"Retrying {operation_name} in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All {max_retries} attempts for {operation_name} failed")
                    return None
        
        return None
    
    def _get_delay_for_error(self, error_msg: str, attempt: int) -> int:
        """Get appropriate delay based on error type"""
        error_lower = error_msg.lower()
        
        # Network/connection errors - longer delays
        if any(x in error_lower for x in ["err_aborted", "frame was detached", "timeout", "network"]):
            return self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
        
        # Rate limiting - very long delays
        if any(x in error_lower for x in ["rate limit", "too many requests", "blocked"]):
            return 120  # 2 minutes
        
        # Default progressive delay
        return self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
    
    def is_recoverable_error(self, error: Exception) -> bool:
        """Check if error is recoverable"""
        error_msg = str(error).lower()
        
        recoverable_patterns = [
            "err_aborted",
            "frame was detached", 
            "timeout",
            "network",
            "connection reset",
            "temporary failure"
        ]
        
        return any(pattern in error_msg for pattern in recoverable_patterns)
    
    def is_facebook_blocking(self, error: Exception) -> bool:
        """Check if Facebook is actively blocking the request"""
        error_msg = str(error).lower()
        
        blocking_patterns = [
            "blocked",
            "suspicious activity",
            "security checkpoint",
            "verify identity",
            "captcha",
            "rate limit exceeded"
        ]
        
        return any(pattern in error_msg for pattern in blocking_patterns)
    
    async def handle_facebook_error(self, error: Exception, context: str = "") -> dict:
        """
        Handle Facebook-specific errors and provide recovery recommendations
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
            
        Returns:
            Dictionary with error analysis and recommendations
        """
        error_msg = str(error)
        error_lower = error_msg.lower()
        
        analysis = {
            "error_type": "unknown",
            "recoverable": False,
            "recommendation": "manual_intervention_required",
            "wait_time": 0,
            "context": context
        }
        
        # Analyze error type
        if "err_aborted" in error_lower or "frame was detached" in error_lower:
            analysis.update({
                "error_type": "navigation_interrupted",
                "recoverable": True,
                "recommendation": "retry_with_delay",
                "wait_time": 30
            })
        
        elif "timeout" in error_lower:
            analysis.update({
                "error_type": "page_load_timeout",
                "recoverable": True,
                "recommendation": "retry_with_longer_timeout",
                "wait_time": 60
            })
        
        elif "network" in error_lower or "connection" in error_lower:
            analysis.update({
                "error_type": "network_issue",
                "recoverable": True,
                "recommendation": "check_network_and_retry",
                "wait_time": 45
            })
        
        elif self.is_facebook_blocking(error):
            analysis.update({
                "error_type": "facebook_blocking",
                "recoverable": False,
                "recommendation": "wait_and_retry_later",
                "wait_time": 300  # 5 minutes
            })
        
        self.logger.info(f"Error analysis for {context}: {analysis}")
        return analysis
