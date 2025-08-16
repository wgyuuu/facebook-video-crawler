"""
Error Handler for Facebook Video Crawler System
Provides unified error handling and recovery mechanisms
"""

import traceback
import sys
from typing import Any, Dict, Optional, Callable
from functools import wraps

from .logger import get_logger


class ErrorHandler:
    """Unified error handler for the crawler system"""
    
    def __init__(self):
        """Initialize error handler"""
        self.logger = get_logger("error_handler")
        self.error_callbacks: Dict[str, Callable] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        
        # Register default error handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default error handlers"""
        # Network errors
        self.register_error_handler("ConnectionError", self._handle_connection_error)
        self.register_error_handler("TimeoutError", self._handle_timeout_error)
        
        # Browser errors
        self.register_error_handler("BrowserError", self._handle_browser_error)
        
        # Parsing errors
        self.register_error_handler("ParseError", self._handle_parse_error)
        
        # Anti-detection errors
        self.register_error_handler("AntiDetectionError", self._handle_anti_detection_error)
    
    def register_error_handler(self, error_type: str, handler: Callable) -> None:
        """Register custom error handler"""
        self.error_callbacks[error_type] = handler
        self.logger.debug(f"Registered error handler for: {error_type}")
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable) -> None:
        """Register recovery strategy for error type"""
        self.recovery_strategies[error_type] = strategy
        self.logger.debug(f"Registered recovery strategy for: {error_type}")
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle error with appropriate handler
        
        Args:
            error: Exception to handle
            context: Additional context information
            
        Returns:
            True if error was handled successfully
        """
        try:
            error_type = type(error).__name__
            self.logger.error(f"Handling error: {error_type}", extra_fields={
                "error_message": str(error),
                "context": context or {}
            })
            
            # Try to find specific handler
            if error_type in self.error_callbacks:
                handler = self.error_callbacks[error_type]
                result = handler(error, context)
                
                # Try recovery strategy if available
                if error_type in self.recovery_strategies:
                    recovery = self.recovery_strategies[error_type]
                    recovery_result = recovery(error, context)
                    self.logger.info(f"Recovery strategy executed: {recovery_result}")
                
                return result
            
            # Use default handler
            return self._handle_generic_error(error, context)
            
        except Exception as e:
            self.logger.error(f"Error in error handler: {e}")
            return False
    
    def _handle_connection_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> bool:
        """Handle connection-related errors"""
        self.logger.warning("Connection error detected, may retry later")
        
        # Log connection details if available
        if context and "url" in context:
            self.logger.debug(f"Failed connection to: {context['url']}")
        
        return True
    
    def _handle_timeout_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> bool:
        """Handle timeout errors"""
        self.logger.warning("Timeout error detected, operation may be retried")
        
        # Log timeout context
        if context and "operation" in context:
            self.logger.debug(f"Timeout in operation: {context['operation']}")
        
        return True
    
    def _handle_browser_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> bool:
        """Handle browser-related errors"""
        self.logger.warning("Browser error detected, may need restart")
        
        # Log browser context
        if context and "browser_type" in context:
            self.logger.debug(f"Browser error in: {context['browser_type']}")
        
        return True
    
    def _handle_parse_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> bool:
        """Handle parsing errors"""
        self.logger.warning("Parse error detected, data extraction may be incomplete")
        
        # Log parsing context
        if context and "selector" in context:
            self.logger.debug(f"Parse error with selector: {context['selector']}")
        
        return True
    
    def _handle_anti_detection_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> bool:
        """Handle anti-detection errors"""
        self.logger.warning("Anti-detection error detected, may need strategy adjustment")
        
        # Log anti-detection context
        if context and "strategy" in context:
            self.logger.debug(f"Anti-detection error in strategy: {context['strategy']}")
        
        return True
    
    def _handle_generic_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> bool:
        """Handle generic errors"""
        self.logger.error(f"Unhandled error type: {type(error).__name__}")
        
        # Log full traceback for debugging
        self.logger.debug(f"Full traceback: {traceback.format_exc()}")
        
        return False
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Safely execute function with error handling
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or None if error occurred
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs
            })
            return None
    
    async def safe_execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Safely execute async function with error handling
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or None if error occurred
        """
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs
            })
            return None
    
    def retry_on_error(self, max_retries: int = 3, delay: float = 1.0):
        """
        Decorator to retry function on error
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_error = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        
                        if attempt < max_retries:
                            self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                            import time
                            time.sleep(delay)
                        else:
                            self.logger.error(f"All {max_retries} attempts failed")
                            self.handle_error(e, {
                                "function": func.__name__,
                                "attempts": max_retries + 1
                            })
                
                # Re-raise last error if all attempts failed
                if last_error:
                    raise last_error
            
            return wrapper
        return decorator
    
    async def retry_on_error_async(self, max_retries: int = 3, delay: float = 1.0):
        """
        Decorator to retry async function on error
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_error = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        
                        if attempt < max_retries:
                            self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                            import asyncio
                            await asyncio.sleep(delay)
                        else:
                            self.logger.error(f"All {max_retries} attempts failed")
                            self.handle_error(e, {
                                "function": func.__name__,
                                "attempts": max_retries + 1
                            })
                
                # Re-raise last error if all attempts failed
                if last_error:
                    raise last_error
            
            return wrapper
        return decorator
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of handled errors"""
        # This would typically track error statistics
        return {
            "total_errors_handled": 0,
            "error_types": {},
            "recovery_attempts": 0
        }


# Global error handler instance
error_handler = ErrorHandler()


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
    """Global error handling function"""
    return error_handler.handle_error(error, context)


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """Global safe execution function"""
    return error_handler.safe_execute(func, *args, **kwargs)


async def safe_execute_async(func: Callable, *args, **kwargs) -> Any:
    """Global safe async execution function"""
    return await error_handler.safe_execute_async(func, *args, **kwargs)
