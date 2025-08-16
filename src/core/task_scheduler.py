"""
Task Scheduler for Facebook Video Crawler System
Manages crawling tasks and scheduling
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger
from ..utils.config_manager import config


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority enumeration"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class CrawlTask:
    """Crawling task definition"""
    id: str
    keyword: str
    max_results: int
    region: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result_count: int = 0
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class TaskScheduler:
    """Manages crawling task scheduling and execution"""
    
    def __init__(self):
        """Initialize task scheduler"""
        self.logger = get_logger("task_scheduler")
        self.config = config.get_crawler_config()
        
        # Task storage
        self.tasks: Dict[str, CrawlTask] = {}
        self.task_queue: List[str] = []
        self.running_tasks: List[str] = []
        
        # Scheduler settings
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 3)
        self.task_timeout = self.config.get("task_timeout", 300)  # 5 minutes
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0
        }
        
        self.logger.info("Task scheduler initialized")
    
    def add_task(self, keyword: str, max_results: int = 10, 
                 region: Optional[str] = None, 
                 priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """
        Add a new crawling task
        
        Args:
            keyword: Search keyword
            max_results: Maximum number of results to fetch
            region: Optional region filter
            priority: Task priority
            
        Returns:
            Task ID
        """
        task_id = f"task_{int(time.time() * 1000)}_{len(self.tasks)}"
        
        task = CrawlTask(
            id=task_id,
            keyword=keyword,
            max_results=max_results,
            region=region,
            priority=priority
        )
        
        self.tasks[task_id] = task
        self._add_to_queue(task_id, priority)
        
        self.stats["total_tasks"] += 1
        self.logger.info(f"Added task: {task_id} - '{keyword}' (priority: {priority.name})")
        
        return task_id
    
    def _add_to_queue(self, task_id: str, priority: TaskPriority) -> None:
        """Add task to priority queue"""
        # Insert based on priority (higher priority first)
        for i, queued_id in enumerate(self.task_queue):
            queued_task = self.tasks[queued_id]
            if priority.value > queued_task.priority.value:
                self.task_queue.insert(i, task_id)
                return
        
        # Add to end if no higher priority tasks
        self.task_queue.append(task_id)
    
    def get_next_task(self) -> Optional[CrawlTask]:
        """Get next available task from queue"""
        if not self.task_queue or len(self.running_tasks) >= self.max_concurrent_tasks:
            return None
        
        task_id = self.task_queue.pop(0)
        task = self.tasks[task_id]
        
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        self.running_tasks.append(task_id)
        
        self.logger.debug(f"Started task: {task_id}")
        return task
    
    def complete_task(self, task_id: str, result_count: int = 0, 
                     error_message: Optional[str] = None) -> bool:
        """
        Mark task as completed
        
        Args:
            task_id: Task identifier
            result_count: Number of results obtained
            error_message: Error message if task failed
            
        Returns:
            True if task was found and updated
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.completed_at = time.time()
        task.result_count = result_count
        
        if error_message:
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            self.stats["failed_tasks"] += 1
            self.logger.warning(f"Task failed: {task_id} - {error_message}")
        else:
            task.status = TaskStatus.COMPLETED
            self.stats["completed_tasks"] += 1
            self.logger.info(f"Task completed: {task_id} - {result_count} results")
        
        # Remove from running tasks
        if task_id in self.running_tasks:
            self.running_tasks.remove(task_id)
        
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if task.status == TaskStatus.PENDING:
            # Remove from queue
            if task_id in self.task_queue:
                self.task_queue.remove(task_id)
            task.status = TaskStatus.CANCELLED
            self.stats["cancelled_tasks"] += 1
            
        elif task.status == TaskStatus.RUNNING:
            # Mark as cancelled (will be cleaned up when completed)
            task.status = TaskStatus.CANCELLED
            self.stats["cancelled_tasks"] += 1
        
        self.logger.info(f"Task cancelled: {task_id}")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed task status"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            "id": task.id,
            "keyword": task.keyword,
            "status": task.status.value,
            "priority": task.priority.value,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "result_count": task.result_count,
            "error_message": task.error_message
        }
    
    def get_all_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[Dict[str, Any]]:
        """Get all tasks with optional status filter"""
        tasks = []
        for task in self.tasks.values():
            if status_filter is None or task.status == status_filter:
                tasks.append(self.get_task_status(task.id))
        return tasks
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "queue_length": len(self.task_queue),
            "running_tasks": len(self.running_tasks),
            "max_concurrent": self.max_concurrent_tasks,
            "available_slots": max(0, self.max_concurrent_tasks - len(self.running_tasks))
        }
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        return {
            **self.stats,
            "queue_status": self.get_queue_status(),
            "active_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        }
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """Clean up old completed tasks"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if task.completed_at and (current_time - task.completed_at) > max_age_seconds:
                    tasks_to_remove.append(task_id)
        
        # Remove old tasks
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            self.logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
        
        return len(tasks_to_remove)


# Global task scheduler instance
task_scheduler = TaskScheduler()


def add_task(keyword: str, max_results: int = 10, 
             region: Optional[str] = None, 
             priority: TaskPriority = TaskPriority.NORMAL) -> str:
    """Global function to add task"""
    return task_scheduler.add_task(keyword, max_results, region, priority)


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Global function to get task status"""
    return task_scheduler.get_task_status(task_id)


def get_scheduler_stats() -> Dict[str, Any]:
    """Global function to get scheduler stats"""
    return task_scheduler.get_scheduler_stats()
