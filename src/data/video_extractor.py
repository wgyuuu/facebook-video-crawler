"""
Video Extractor for Facebook Video Crawler System
Provides video metadata extraction and download functionality
"""

import asyncio
import re
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from pathlib import Path
import aiohttp
import aiofiles

from ..utils.logger import get_logger
from ..utils.config_manager import config
from ..core.crawler_engine import CrawlerEngine


class VideoMetadata:
    """Container for video metadata"""
    
    def __init__(self):
        self.video_id: str = ""
        self.title: str = ""
        self.description: str = ""
        self.author: str = ""
        self.author_id: str = ""
        self.publish_time: str = ""
        self.duration: int = 0
        self.views: int = 0
        self.likes: int = 0
        self.comments: int = 0
        self.shares: int = 0
        self.tags: List[str] = []
        self.category: str = ""
        self.language: str = ""
        self.region: str = ""
        self.video_url: str = ""
        self.thumbnail_url: str = ""
        self.original_url: str = ""
        self.extracted_at: str = ""
        self.status: str = "pending"
        self.error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "author_id": self.author_id,
            "publish_time": self.publish_time,
            "duration": self.duration,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "tags": self.tags,
            "category": self.category,
            "language": self.language,
            "region": self.region,
            "video_url": self.video_url,
            "thumbnail_url": self.thumbnail_url,
            "original_url": self.original_url,
            "extracted_at": self.extracted_at,
            "status": self.status,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoMetadata':
        """Create from dictionary"""
        instance = cls()
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance


class VideoExtractor:
    """Extracts video metadata and downloads videos from Facebook"""
    
    def __init__(self, crawler_engine: Optional[CrawlerEngine] = None):
        """
        Initialize video extractor
        
        Args:
            crawler_engine: Optional crawler engine instance
        """
        self.logger = get_logger("video_extractor")
        self.config = config.get_facebook_config()
        self.crawler_engine = crawler_engine
        
        # Facebook selectors (may need updates as Facebook changes)
        self.selectors = {
            "video_container": "[data-testid='video_container']",
            "video_title": "h1, h2, h3, [data-testid='post_message']",
            "video_description": "[data-testid='post_message'], ._5pbx",
            "author_name": "[data-testid='post_actor_name'], ._5pbx a",
            "author_link": "[data-testid='post_actor_name'] a",
            "publish_time": "[data-testid='post_timestamp'], ._5pbx abbr",
            "video_stats": "[data-testid='UFI2ReactionsCount/root'], ._1g06",
            "like_count": "[data-testid='UFI2ReactionsCount/root'] span, ._1g06 span",
            "comment_count": "[data-testid='UFI2CommentsCount/root'] span, ._1g06 span",
            "share_count": "[data-testid='UFI2SharesCount/root'] span, ._1g06 span",
            "video_element": "video",
            "thumbnail": "img[data-testid='post_image'], ._5pbx img"
        }
        
        # Video quality preferences
        self.quality_preferences = ["best", "720p", "480p", "360p"]
        
        self.logger.info("Video extractor initialized")
    
    async def extract_video_metadata(self, url: str) -> Optional[VideoMetadata]:
        """
        Extract video metadata from Facebook video page
        
        Args:
            url: Facebook video URL
            
        Returns:
            VideoMetadata object or None if extraction failed
        """
        if not self.crawler_engine:
            self.logger.error("Crawler engine not available")
            return None
        
        try:
            self.logger.info(f"Extracting metadata from: {url}")
            
            # Navigate to video page
            if not await self.crawler_engine.navigate_to(url):
                self.logger.error("Failed to navigate to video page")
                return None
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Extract metadata
            metadata = VideoMetadata()
            metadata.original_url = url
            metadata.extracted_at = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Extract basic information
            await self._extract_basic_info(metadata)
            
            # Extract statistics
            await self._extract_statistics(metadata)
            
            # Extract video information
            await self._extract_video_info(metadata)
            
            # Extract author information
            await self._extract_author_info(metadata)
            
            # Extract tags and category
            await self._extract_tags_and_category(metadata)
            
            # Validate metadata
            if self._validate_metadata(metadata):
                metadata.status = "extracted"
                self.logger.info(f"Successfully extracted metadata for video: {metadata.title}")
                return metadata
            else:
                metadata.status = "failed"
                metadata.error_message = "Metadata validation failed"
                self.logger.warning("Metadata validation failed")
                return metadata
                
        except Exception as e:
            self.logger.error(f"Failed to extract video metadata: {e}")
            if 'metadata' in locals():
                metadata.status = "failed"
                metadata.error_message = str(e)
            return None
    
    async def _extract_basic_info(self, metadata: VideoMetadata) -> None:
        """Extract basic video information"""
        try:
            # Extract title
            title = await self.crawler_engine.get_element_text(self.selectors["video_title"])
            if title:
                metadata.title = title.strip()
            
            # Extract description
            description = await self.crawler_engine.get_element_text(self.selectors["video_description"])
            if description:
                metadata.description = description.strip()
            
            # Extract publish time
            publish_time = await self.crawler_engine.get_element_attribute(
                self.selectors["publish_time"], "title"
            )
            if publish_time:
                metadata.publish_time = publish_time.strip()
            
            # Extract video ID from URL
            video_id = self._extract_video_id_from_url(metadata.original_url)
            if video_id:
                metadata.video_id = video_id
            
        except Exception as e:
            self.logger.debug(f"Failed to extract basic info: {e}")
    
    async def _extract_statistics(self, metadata: VideoMetadata) -> None:
        """Extract video statistics"""
        try:
            # Extract like count
            like_text = await self.crawler_engine.get_element_text(self.selectors["like_count"])
            if like_text:
                metadata.likes = self._parse_count(like_text)
            
            # Extract comment count
            comment_text = await self.crawler_engine.get_element_text(self.selectors["comment_count"])
            if comment_text:
                metadata.comments = self._parse_count(comment_text)
            
            # Extract share count
            share_text = await self.crawler_engine.get_element_text(self.selectors["share_count"])
            if share_text:
                metadata.shares = self._parse_count(share_text)
            
            # Extract view count (may be in different locations)
            view_text = await self._extract_view_count()
            if view_text:
                metadata.views = self._parse_count(view_text)
            
        except Exception as e:
            self.logger.debug(f"Failed to extract statistics: {e}")
    
    async def _extract_video_info(self, metadata: VideoMetadata) -> None:
        """Extract video-specific information"""
        try:
            # Extract video URL
            video_url = await self._extract_video_url()
            if video_url:
                metadata.video_url = video_url
            
            # Extract thumbnail URL
            thumbnail_url = await self.crawler_engine.get_element_attribute(
                self.selectors["thumbnail"], "src"
            )
            if thumbnail_url:
                metadata.thumbnail_url = thumbnail_url
            
            # Extract duration
            duration = await self._extract_video_duration()
            if duration:
                metadata.duration = duration
            
        except Exception as e:
            self.logger.debug(f"Failed to extract video info: {e}")
    
    async def _extract_author_info(self, metadata: VideoMetadata) -> None:
        """Extract author information"""
        try:
            # Extract author name
            author_name = await self.crawler_engine.get_element_text(self.selectors["author_name"])
            if author_name:
                metadata.author = author_name.strip()
            
            # Extract author link
            author_link = await self.crawler_engine.get_element_attribute(
                self.selectors["author_link"], "href"
            )
            if author_link:
                # Extract author ID from link
                author_id = self._extract_author_id_from_url(author_link)
                if author_id:
                    metadata.author_id = author_id
            
        except Exception as e:
            self.logger.debug(f"Failed to extract author info: {e}")
    
    async def _extract_tags_and_category(self, metadata: VideoMetadata) -> None:
        """Extract tags and category information"""
        try:
            # Extract tags from description or other elements
            tags = await self._extract_tags()
            if tags:
                metadata.tags = tags
            
            # Extract category (may be inferred from tags or other elements)
            category = await self._extract_category()
            if category:
                metadata.category = category
            
        except Exception as e:
            self.logger.debug(f"Failed to extract tags and category: {e}")
    
    async def _extract_video_url(self) -> Optional[str]:
        """Extract direct video URL"""
        try:
            # Try to find video element
            video_element = await self.crawler_engine.page.query_selector(self.selectors["video_element"])
            if video_element:
                video_url = await video_element.get_attribute("src")
                if video_url:
                    return video_url
            
            # Try to extract from page source
            page_content = await self.crawler_engine.get_page_content()
            
            # Look for video URLs in various formats
            video_patterns = [
                r'"video_url":"([^"]+)"',
                r'"hd_src":"([^"]+)"',
                r'"sd_src":"([^"]+)"',
                r'"src":"([^"]+\.mp4[^"]*)"',
                r'https://[^"]+\.mp4[^"]*'
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, page_content)
                if matches:
                    # Return the first match, preferring higher quality
                    for match in matches:
                        if "hd" in match.lower() or "720" in match or "1080" in match:
                            return match
                    return matches[0]
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract video URL: {e}")
            return None
    
    async def _extract_view_count(self) -> Optional[str]:
        """Extract view count from various locations"""
        try:
            # Look for view count in different selectors
            view_selectors = [
                "[data-testid='video_view_count']",
                ".video_view_count",
                "[data-testid='post_views']",
                ".post_views"
            ]
            
            for selector in view_selectors:
                view_text = await self.crawler_engine.get_element_text(selector)
                if view_text:
                    return view_text
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract view count: {e}")
            return None
    
    async def _extract_video_duration(self) -> Optional[int]:
        """Extract video duration in seconds"""
        try:
            # Try to get duration from video element
            video_element = await self.crawler_engine.page.query_selector(self.selectors["video_element"])
            if video_element:
                duration = await video_element.get_attribute("duration")
                if duration:
                    return int(float(duration))
            
            # Try to extract from page source
            page_content = await self.crawler_engine.get_page_content()
            
            # Look for duration patterns
            duration_patterns = [
                r'"duration":(\d+)',
                r'"video_duration":(\d+)',
                r'"length":(\d+)'
            ]
            
            for pattern in duration_patterns:
                matches = re.findall(pattern, page_content)
                if matches:
                    return int(matches[0])
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract video duration: {e}")
            return None
    
    async def _extract_tags(self) -> List[str]:
        """Extract tags from video page"""
        try:
            # Look for tags in various locations
            tag_selectors = [
                "[data-testid='video_tags']",
                ".video_tags",
                "[data-testid='post_tags']",
                ".post_tags"
            ]
            
            tags = []
            for selector in tag_selectors:
                tag_elements = await self.crawler_engine.page.query_selector_all(selector)
                for element in tag_elements:
                    tag_text = await element.text_content()
                    if tag_text:
                        tags.extend([tag.strip() for tag in tag_text.split(",")])
            
            # Remove duplicates and empty tags
            tags = list(set([tag for tag in tags if tag]))
            return tags
            
        except Exception as e:
            self.logger.debug(f"Failed to extract tags: {e}")
            return []
    
    async def _extract_category(self) -> Optional[str]:
        """Extract video category"""
        try:
            # Look for category information
            category_selectors = [
                "[data-testid='video_category']",
                ".video_category",
                "[data-testid='post_category']",
                ".post_category"
            ]
            
            for selector in category_selectors:
                category_text = await self.crawler_engine.get_element_text(selector)
                if category_text:
                    return category_text.strip()
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract category: {e}")
            return None
    
    def _extract_video_id_from_url(self, url: str) -> Optional[str]:
        """Extract video ID from Facebook URL"""
        try:
            # Common Facebook video URL patterns
            patterns = [
                r'/videos/(\d+)/',
                r'/watch/\?v=(\d+)',
                r'/video\.php\?v=(\d+)',
                r'/permalink/(\d+)/'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract video ID: {e}")
            return None
    
    def _extract_author_id_from_url(self, url: str) -> Optional[str]:
        """Extract author ID from Facebook profile URL"""
        try:
            # Common Facebook profile URL patterns
            patterns = [
                r'/profile\.php\?id=(\d+)',
                r'/(\d+)/',
                r'/profile/(\d+)/'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract author ID: {e}")
            return None
    
    def _parse_count(self, text: str) -> int:
        """Parse count text to integer"""
        try:
            # Remove common text and symbols
            text = text.lower().strip()
            
            # Handle "K" (thousands)
            if "k" in text:
                number = float(text.replace("k", "").replace(",", ""))
                return int(number * 1000)
            
            # Handle "M" (millions)
            if "m" in text:
                number = float(text.replace("m", "").replace(",", ""))
                return int(number * 1000000)
            
            # Handle "B" (billions)
            if "b" in text:
                number = float(text.replace("b", "").replace(",", ""))
                return int(number * 1000000000)
            
            # Handle plain numbers
            number = text.replace(",", "").replace(".", "")
            return int(number)
            
        except Exception as e:
            self.logger.debug(f"Failed to parse count '{text}': {e}")
            return 0
    
    def _validate_metadata(self, metadata: VideoMetadata) -> bool:
        """Validate extracted metadata"""
        try:
            # Check required fields
            if not metadata.video_id:
                self.logger.warning("Missing video ID")
                return False
            
            if not metadata.title:
                self.logger.warning("Missing video title")
                return False
            
            if not metadata.author:
                self.logger.warning("Missing author")
                return False
            
            # Check for reasonable values
            if metadata.views < 0 or metadata.likes < 0 or metadata.comments < 0:
                self.logger.warning("Invalid statistics values")
                return False
            
            if metadata.duration < 0 or metadata.duration > 36000:  # Max 10 hours
                self.logger.warning("Invalid duration")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Metadata validation error: {e}")
            return False
    
    async def download_video(self, metadata: VideoMetadata, output_path: str) -> bool:
        """
        Download video file
        
        Args:
            metadata: Video metadata
            output_path: Output file path
            
        Returns:
            True if download successful
        """
        if not metadata.video_url:
            self.logger.error("No video URL available for download")
            return False
        
        try:
            self.logger.info(f"Downloading video: {metadata.title}")
            
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Download video
            async with aiohttp.ClientSession() as session:
                async with session.get(metadata.video_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        # Update metadata
                        metadata.status = "downloaded"
                        metadata.video_url = output_path
                        
                        self.logger.info(f"Video downloaded successfully: {output_path}")
                        return True
                    else:
                        self.logger.error(f"Download failed with status: {response.status}")
                        metadata.status = "download_failed"
                        metadata.error_message = f"HTTP {response.status}"
                        return False
                        
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            metadata.status = "download_failed"
            metadata.error_message = str(e)
            return False
    
    async def extract_multiple_videos(self, urls: List[str]) -> List[VideoMetadata]:
        """
        Extract metadata from multiple video URLs
        
        Args:
            urls: List of Facebook video URLs
            
        Returns:
            List of VideoMetadata objects
        """
        results = []
        
        for i, url in enumerate(urls):
            try:
                self.logger.info(f"Processing video {i+1}/{len(urls)}: {url}")
                
                metadata = await self.extract_video_metadata(url)
                if metadata:
                    results.append(metadata)
                
                # Add delay between extractions
                if i < len(urls) - 1:
                    delay = random.randint(2, 5)
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"Failed to process video {url}: {e}")
                continue
        
        self.logger.info(f"Completed processing {len(urls)} videos. Success: {len(results)}")
        return results
    
    def get_extraction_stats(self, metadata_list: List[VideoMetadata]) -> Dict[str, Any]:
        """Get statistics about extraction results"""
        if not metadata_list:
            return {}
        
        total = len(metadata_list)
        successful = len([m for m in metadata_list if m.status == "extracted"])
        failed = len([m for m in metadata_list if m.status == "failed"])
        downloaded = len([m for m in metadata_list if m.status == "downloaded"])
        
        # Calculate average statistics
        avg_views = sum(m.views for m in metadata_list if m.views > 0) / max(1, len([m for m in metadata_list if m.views > 0]))
        avg_likes = sum(m.likes for m in metadata_list if m.likes > 0) / max(1, len([m for m in metadata_list if m.likes > 0]))
        avg_comments = sum(m.comments for m in metadata_list if m.comments > 0) / max(1, len([m for m in metadata_list if m.comments > 0]))
        
        return {
            "total_videos": total,
            "successful_extractions": successful,
            "failed_extractions": failed,
            "downloaded_videos": downloaded,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_views": int(avg_views),
            "average_likes": int(avg_likes),
            "average_comments": int(avg_comments)
        }
