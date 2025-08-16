"""
Logging system for Facebook Video Crawler System
Provides structured logging, file rotation, and performance monitoring
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time
import threading
from functools import wraps


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        """Format log record with structured data"""
        # Create base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add thread info
        log_entry["thread"] = threading.current_thread().name
        log_entry["thread_id"] = threading.current_thread().ident
        
        return json.dumps(log_entry, ensure_ascii=False)


class PerformanceLogger:
    """Performance monitoring and logging"""
    
    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()
    
    def start_timer(self, operation: str) -> float:
        """Start timing an operation"""
        start_time = time.time()
        with self.lock:
            if operation not in self.metrics:
                self.metrics[operation] = {"count": 0, "total_time": 0, "min_time": float('inf'), "max_time": 0}
            self.metrics[operation]["start_time"] = start_time
        return start_time
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and record metrics"""
        end_time = time.time()
        with self.lock:
            if operation in self.metrics and "start_time" in self.metrics[operation]:
                duration = end_time - self.metrics[operation]["start_time"]
                self.metrics[operation]["count"] += 1
                self.metrics[operation]["total_time"] += duration
                self.metrics[operation]["min_time"] = min(self.metrics[operation]["min_time"], duration)
                self.metrics[operation]["max_time"] = max(self.metrics[operation]["max_time"], duration)
                del self.metrics[operation]["start_time"]
                return duration
        return 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        with self.lock:
            result = {}
            for operation, data in self.metrics.items():
                if data["count"] > 0:
                    result[operation] = {
                        "count": data["count"],
                        "total_time": data["total_time"],
                        "avg_time": data["total_time"] / data["count"],
                        "min_time": data["min_time"],
                        "max_time": data["max_time"]
                    }
            return result
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics"""
        with self.lock:
            self.metrics.clear()


class Logger:
    """Main logger class for the crawler system"""
    
    def __init__(self, name: str = "facebook_crawler", config: Optional[Dict[str, Any]] = None):
        """
        Initialize logger
        
        Args:
            name: Logger name
            config: Logger configuration
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(name)
        self.performance_logger = PerformanceLogger()
        
        # Set log level
        log_level = self.config.get("level", "INFO")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_handlers()
        
        # Setup performance monitoring
        self._setup_performance_monitoring()
    
    def _setup_handlers(self) -> None:
        """Setup logging handlers"""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = self.config.get("file_path", "./data/logs/crawler.log")
        if log_file:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir:
                Path(log_dir).mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler
            max_bytes = self.config.get("max_file_size_mb", 100) * 1024 * 1024
            backup_count = self.config.get("backup_count", 5)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Use structured formatter for file logs
            file_formatter = StructuredFormatter()
            file_handler.setFormatter(file_formatter)
            
            self.logger.addHandler(file_handler)
        
        # Error file handler
        error_log_file = log_file.replace('.log', '_error.log') if log_file else None
        if error_log_file:
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            self.logger.addHandler(error_handler)
    
    def _setup_performance_monitoring(self) -> None:
        """Setup performance monitoring"""
        # Start background thread for metrics collection
        def collect_metrics():
            while True:
                try:
                    time.sleep(60)  # Collect metrics every minute
                    self._log_performance_metrics()
                except Exception as e:
                    self.error(f"Error collecting performance metrics: {e}")
        
        metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
        metrics_thread.start()
    
    def _log_performance_metrics(self) -> None:
        """Log current performance metrics"""
        metrics = self.performance_logger.get_metrics()
        if metrics:
            self.info("Performance metrics", extra_fields={"metrics": metrics})
    
    def _log_with_extra(self, level: int, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log message with extra fields"""
        extra = {'extra_fields': extra_fields} if extra_fields else None
        self.logger.log(level, message, extra=extra, stacklevel=3, **kwargs)
    
    def debug(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log debug message"""
        self._log_with_extra(logging.DEBUG, message, extra_fields, **kwargs)
    
    def info(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log info message"""
        self._log_with_extra(logging.INFO, message, extra_fields, **kwargs)
    
    def warning(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log warning message"""
        self._log_with_extra(logging.WARNING, message, extra_fields, **kwargs)
    
    def error(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log error message"""
        self._log_with_extra(logging.ERROR, message, extra_fields, **kwargs)
    
    def critical(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log critical message"""
        self._log_with_extra(logging.CRITICAL, message, extra_fields, **kwargs)
    
    def exception(self, message: str, extra_fields: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log exception message with traceback"""
        extra = {'extra_fields': extra_fields} if extra_fields else None
        self.logger.exception(message, extra=extra, stacklevel=2, **kwargs)
    
    def performance_timer(self, operation: str):
        """Decorator for performance timing"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.performance_logger.start_timer(operation)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = self.performance_logger.end_timer(operation)
                    self.debug(f"Operation '{operation}' completed in {duration:.3f}s")
            return wrapper
        return decorator
    
    def start_operation(self, operation: str) -> float:
        """Start timing an operation"""
        return self.performance_logger.start_timer(operation)
    
    def end_operation(self, operation: str) -> float:
        """End timing an operation"""
        return self.performance_logger.end_timer(operation)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_logger.get_metrics()
    
    def reset_performance_metrics(self) -> None:
        """Reset performance metrics"""
        self.performance_logger.reset_metrics()
    
    def log_crawler_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log crawler-specific events"""
        extra_fields = {
            "event_type": event_type,
            "crawler_event": True,
            **details
        }
        self.info(f"Crawler event: {event_type}", extra_fields=extra_fields)
    
    def log_anti_detection_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log anti-detection events"""
        extra_fields = {
            "event_type": event_type,
            "anti_detection_event": True,
            **details
        }
        self.info(f"Anti-detection event: {event_type}", extra_fields=extra_fields)
    
    def log_data_extraction_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log data extraction events"""
        extra_fields = {
            "event_type": event_type,
            "data_extraction_event": True,
            **details
        }
        self.info(f"Data extraction event: {event_type}", extra_fields=extra_fields)
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with additional context"""
        extra_fields = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        self.error(f"Error occurred: {error}", extra_fields=extra_fields)
    
    def set_level(self, level: str) -> None:
        """Set logging level"""
        level_upper = level.upper()
        if hasattr(logging, level_upper):
            self.logger.setLevel(getattr(logging, level_upper))
            self.info(f"Log level changed to {level_upper}")
        else:
            self.warning(f"Invalid log level: {level}")
    
    def get_logger(self) -> logging.Logger:
        """Get the underlying logging.Logger instance"""
        return self.logger


# Global logger instance
logger = Logger()


def get_logger(name: str = None, config: Optional[Dict[str, Any]] = None) -> Logger:
    """Get logger instance"""
    if name:
        return Logger(name, config)
    return logger


def setup_logging(config: Dict[str, Any]) -> Logger:
    """Setup logging with configuration"""
    global logger
    logger = Logger("facebook_crawler", config)
    return logger
