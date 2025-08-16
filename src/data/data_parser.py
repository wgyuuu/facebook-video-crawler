"""
Data Parser for Facebook Video Crawler System
"""

import re
from typing import Dict, Any, List, Optional

from ..utils.logger import get_logger


class DataParser:
    """Parses and processes extracted data from Facebook"""
    
    def __init__(self):
        """Initialize data parser"""
        self.logger = get_logger("data_parser")
        
        # Regular expressions for parsing
        self.patterns = {
            "view_count": r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:views?|观看|次观看)",
            "like_count": r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:likes?|赞|喜欢)",
            "comment_count": r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:comments?|评论|留言)",
            "share_count": r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:shares?|分享|转发)",
            "save_count": r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:saves?|收藏|保存)",
            "duration": r"(\d+):(\d+)",
            "url": r"https?://[^\s<>\"{}|\\^`\[\]]+"
        }
        
        self.logger.info("Data parser initialized")
    
    def parse_video_stats(self, stats_text: str) -> Dict[str, Any]:
        """Parse video statistics from text"""
        stats = {
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0,
            "save_count": 0
        }
        
        try:
            # Parse view count
            view_match = re.search(self.patterns["view_count"], stats_text, re.IGNORECASE)
            if view_match:
                stats["view_count"] = self._parse_number(view_match.group(1))
            
            # Parse like count
            like_match = re.search(self.patterns["like_count"], stats_text, re.IGNORECASE)
            if like_match:
                stats["like_count"] = self._parse_number(like_match.group(1))
            
            # Parse comment count
            comment_match = re.search(self.patterns["comment_count"], stats_text, re.IGNORECASE)
            if comment_match:
                stats["comment_count"] = self._parse_number(comment_match.group(1))
            
            # Parse share count
            share_match = re.search(self.patterns["share_count"], stats_text, re.IGNORECASE)
            if share_match:
                stats["share_count"] = self._parse_number(share_match.group(1))
            
            # Parse save count
            save_match = re.search(self.patterns["save_count"], stats_text, re.IGNORECASE)
            if save_match:
                stats["save_count"] = self._parse_number(save_match.group(1))
            
        except Exception as e:
            self.logger.warning(f"Failed to parse video stats: {e}")
        
        return stats
    
    def parse_video_duration(self, duration_text: str) -> Optional[int]:
        """Parse video duration from text"""
        try:
            duration_match = re.search(self.patterns["duration"], duration_text)
            if duration_match:
                minutes = int(duration_match.group(1))
                seconds = int(duration_match.group(2))
                return minutes * 60 + seconds
        except Exception as e:
            self.logger.warning(f"Failed to parse duration: {e}")
        
        return None
    
    def parse_video_urls(self, text: str) -> List[str]:
        """Extract video URLs from text"""
        try:
            urls = re.findall(self.patterns["url"], text)
            video_urls = [url for url in urls if self._is_video_url(url)]
            return video_urls
        except Exception as e:
            self.logger.warning(f"Failed to parse URLs: {e}")
            return []
    
    def parse_tags(self, text: str) -> List[str]:
        """Extract hashtags and tags from text"""
        try:
            hashtags = re.findall(r'#(\w+)', text)
            mentions = re.findall(r'@(\w+)', text)
            tags = hashtags + mentions
            tags = [tag.lower() for tag in tags if len(tag) > 1]
            return list(set(tag))
        except Exception as e:
            self.logger.warning(f"Failed to parse tags: {e}")
            return []
    
    def _parse_number(self, number_str: str) -> int:
        """Parse number string to integer"""
        try:
            number_str = number_str.replace(",", "")
            
            if "K" in number_str.upper():
                number_str = number_str.upper().replace("K", "")
                return int(float(number_str) * 1000)
            
            if "M" in number_str.upper():
                number_str = number_str.upper().replace("M", "")
                return int(float(number_str) * 1000000)
            
            return int(float(number_str))
            
        except Exception as e:
            self.logger.warning(f"Failed to parse number '{number_str}': {e}")
            return 0
    
    def _is_video_url(self, url: str) -> bool:
        """Check if URL is a video URL"""
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        video_domains = ['facebook.com', 'fb.com', 'youtube.com', 'ytimg.com']
        
        for ext in video_extensions:
            if ext in url.lower():
                return True
        
        for domain in video_domains:
            if domain in url.lower():
                return True
        
        return False


# Global data parser instance
data_parser = DataParser()
