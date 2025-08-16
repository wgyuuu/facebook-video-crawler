"""
Storage Manager for Facebook Video Crawler System
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..utils.logger import get_logger
from ..utils.config_manager import config


class StorageManager:
    """Manages data storage and retrieval"""
    
    def __init__(self):
        """Initialize storage manager"""
        self.logger = get_logger("storage_manager")
        
        # Storage paths
        self.data_dir = Path(config.get("paths.data_dir", "data"))
        self.videos_dir = self.data_dir / "videos"
        self.database_dir = self.data_dir / "database"
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.database_dir.mkdir(parents=True, exist_ok=True)
        
        # Database file
        self.db_file = self.database_dir / "crawler.db"
        
        # Initialize database
        self._init_database()
        
        self.logger.info("Storage manager initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE,
                    title TEXT,
                    description TEXT,
                    author TEXT,
                    duration INTEGER,
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER,
                    share_count INTEGER,
                    save_count INTEGER,
                    tags TEXT,
                    video_url TEXT,
                    region TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
    
    def save_video(self, video_data: Dict[str, Any]) -> bool:
        """Save video data to database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Prepare data
            video_id = video_data.get("video_id", "")
            title = video_data.get("title", "")
            description = video_data.get("description", "")
            author = video_data.get("author", "")
            duration = video_data.get("duration", 0)
            
            # Stats
            stats = video_data.get("stats", {})
            view_count = stats.get("view_count", 0)
            like_count = stats.get("like_count", 0)
            comment_count = stats.get("comment_count", 0)
            share_count = stats.get("share_count", 0)
            save_count = stats.get("save_count", 0)
            
            # Other fields
            tags = json.dumps(video_data.get("tags", []))
            video_url = video_data.get("video_url", "")
            region = video_data.get("region", "")
            
            # Insert or update
            cursor.execute('''
                INSERT OR REPLACE INTO videos (
                    video_id, title, description, author, duration,
                    view_count, like_count, comment_count, share_count, save_count,
                    tags, video_url, region
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id, title, description, author, duration,
                view_count, like_count, comment_count, share_count, save_count,
                tags, video_url, region
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Saved video: {video_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save video: {e}")
            return False
    
    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video by ID"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM videos WHERE video_id = ?', (video_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return self._row_to_dict(row, cursor.description)
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get video: {e}")
            return None
    
    def search_videos(self, keyword: str = None, region: str = None, 
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Search videos by criteria"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            query = "SELECT * FROM videos WHERE 1=1"
            params = []
            
            if keyword:
                query += " AND (title LIKE ? OR description LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            if region:
                query += " AND region = ?"
                params.append(region)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            videos = []
            for row in rows:
                videos.append(self._row_to_dict(row, cursor.description))
            
            return videos
            
        except Exception as e:
            self.logger.error(f"Failed to search videos: {e}")
            return []
    
    def _row_to_dict(self, row: tuple, description) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        return {desc[0]: value for desc, value in zip(description, row)}


# Global storage manager instance
storage_manager = StorageManager()
