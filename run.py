#!/usr/bin/env python3
"""
Command-line interface for Facebook Video Crawler System
Provides easy-to-use commands for video extraction and download
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import FacebookVideoCrawler, search_and_download, process_urls
from src.utils.config_manager import config
from src.utils.logger import setup_logging


def setup_logging_from_config():
    """Setup logging based on configuration"""
    storage_config = config.get_storage_config()
    logging_config = storage_config.get("logging", {})
    setup_logging(logging_config)


async def cmd_search(args):
    """Search for videos by keyword"""
    print(f"🔍 Searching for videos with keyword: '{args.keyword}'")
    print(f"📊 Max results: {args.max_results}")
    print(f"🌍 Region: {args.region or 'Default'}")
    print("-" * 50)
    
    try:
        videos = await search_and_download(
            keyword=args.keyword,
            max_results=args.max_results,
            region=args.region,
            download=args.download
        )
        
        if videos:
            # Check if any videos have errors
            error_videos = [v for v in videos if v.status == "failed"]
            success_videos = [v for v in videos if v.status != "failed"]
            
            if error_videos:
                print(f"\n⚠️  Found {len(error_videos)} videos with errors:")
                for i, video in enumerate(error_videos, 1):
                    print(f"{i:2d}. ❌ Error: {video.error_message}")
                print()
            
            if success_videos:
                print(f"\n✅ Found {len(success_videos)} successful videos:")
                for i, video in enumerate(success_videos, 1):
                    print(f"{i:2d}. {video.title}")
                    print(f"    👤 Author: {video.author}")
                    print(f"    👁️  Views: {video.views:,}")
                    print(f"    👍 Likes: {video.likes:,}")
                    print(f"    💬 Comments: {video.comments:,}")
                    print(f"    📅 Published: {video.publish_time}")
                    print(f"    📍 Status: {video.status}")
                    print()
            else:
                print("❌ No successful videos found")
            
            # Export metadata if requested
            if args.export:
                export_path = f"metadata_{args.keyword}_{len(videos)}_videos.json"
                async with FacebookVideoCrawler() as crawler:
                    success = await crawler.export_metadata(videos, export_path)
                    if success:
                        print(f"📁 Metadata exported to: {export_path}")
                    else:
                        print("❌ Failed to export metadata")
        else:
            print("❌ No videos found")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return 1
    
    return 0


async def cmd_download(args):
    """Download videos from URLs"""
    print(f"📥 Processing {len(args.urls)} video URLs")
    print("-" * 50)
    
    try:
        videos = await process_urls(args.urls, download=True)
        
        if videos:
            print(f"\n✅ Processed {len(videos)} videos:")
            for i, video in enumerate(videos, 1):
                print(f"{i:2d}. {video.title}")
                print(f"    👤 Author: {video.author}")
                print(f"    📍 Status: {video.status}")
                if video.status == "downloaded":
                    print(f"    💾 File: {video.video_url}")
                elif video.status == "download_failed":
                    print(f"    ❌ Error: {video.error_message}")
                print()
            
            # Export metadata if requested
            if args.export:
                export_path = f"metadata_downloaded_{len(videos)}_videos.json"
                async with FacebookVideoCrawler() as crawler:
                    success = await crawler.export_metadata(videos, export_path)
                    if success:
                        print(f"📁 Metadata exported to: {export_path}")
                    else:
                        print("❌ Failed to export metadata")
        else:
            print("❌ No videos processed")
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 1
    
    return 0


async def cmd_status(args):
    """Show crawler status"""
    print("📊 Facebook Video Crawler Status")
    print("=" * 50)
    
    try:
        async with FacebookVideoCrawler() as crawler:
            status = crawler.get_status()
            
            # Crawler status
            print(f"🖥️  Crawler Engine: {'🟢 Running' if status['crawler_running'] else '🔴 Stopped'}")
            
            # Fingerprint stats
            fp_stats = status.get('fingerprint_stats', {})
            print(f"🆔 Fingerprint Manager: {'🟢 Active' if fp_stats.get('total_fingerprints', 0) > 0 else '🔴 Inactive'}")
            if fp_stats:
                print(f"   📊 Total fingerprints: {fp_stats.get('total_fingerprints', 0)}")
                print(f"   ⏰ Last rotation: {fp_stats.get('last_rotation', 'N/A')}")
            
            # Proxy stats
            proxy_stats = status.get('proxy_stats', {})
            print(f"🌐 Proxy Manager: {'🟢 Active' if proxy_stats.get('working_proxies', 0) > 0 else '🔴 Inactive'}")
            if proxy_stats:
                print(f"   📊 Total proxies: {proxy_stats.get('total_proxies', 0)}")
                print(f"   ✅ Working proxies: {proxy_stats.get('working_proxies', 0)}")
                print(f"   📈 Success rate: {proxy_stats.get('average_success_rate', 0):.1%}")
            
            # Extraction stats
            ext_stats = status.get('extraction_stats', {})
            if ext_stats:
                print(f"📹 Extraction Stats:")
                print(f"   📊 Total processed: {ext_stats.get('total_videos_processed', 0)}")
                print(f"   ✅ Successful: {ext_stats.get('successful_extractions', 0)}")
                print(f"   ❌ Failed: {ext_stats.get('failed_extractions', 0)}")
                print(f"   💾 Downloaded: {ext_stats.get('total_downloads', 0)}")
                print(f"   ⏱️  Session duration: {ext_stats.get('current_session_duration', 0):.1f}s")
            
            # Health check
            print("\n🏥 System Health Check:")
            health = await crawler.health_check()
            print(f"   Overall Status: {health['overall_status'].upper()}")
            
            for component, status in health.get('components', {}).items():
                icon = "🟢" if status == "healthy" else "🟡" if status == "degraded" else "🔴"
                print(f"   {icon} {component}: {status}")
            
            if health.get('recommendations'):
                print("\n💡 Recommendations:")
                for rec in health['recommendations']:
                    print(f"   • {rec}")
                    
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return 1
    
    return 0


async def cmd_config(args):
    """Show or modify configuration"""
    if args.show:
        print("⚙️  Current Configuration")
        print("=" * 50)
        
        config_data = config.get_all()
        print(json.dumps(config_data, indent=2, ensure_ascii=False))
        
    elif args.modify:
        print(f"🔧 Modifying configuration: {args.modify}")
        
        try:
            # Parse key=value format
            if '=' not in args.modify:
                print("❌ Invalid format. Use: key=value")
                return 1
            
            key, value = args.modify.split('=', 1)
            config.set(key.strip(), value.strip())
            
            # Save configuration
            config.save()
            print(f"✅ Configuration updated: {key} = {value}")
            
        except Exception as e:
            print(f"❌ Failed to modify configuration: {e}")
            return 1
    
    return 0


async def cmd_test(args):
    """Test crawler functionality"""
    print("🧪 Testing Facebook Video Crawler")
    print("=" * 50)
    
    try:
        async with FacebookVideoCrawler() as crawler:
            print("✅ Crawler started successfully")
            
            # Test basic functionality
            print("\n🔍 Testing search functionality...")
            test_videos = await crawler.search_videos("test", max_results=2)
            
            if test_videos:
                print(f"✅ Search test passed: Found {len(test_videos)} videos")
            else:
                print("⚠️  Search test: No videos found (this might be normal)")
            
            # Test health check
            print("\n🏥 Testing health check...")
            health = await crawler.health_check()
            print(f"✅ Health check passed: {health['overall_status']}")
            
            # Test fingerprint rotation
            print("\n🆔 Testing fingerprint rotation...")
            new_fp = await crawler.rotate_fingerprint()
            if new_fp:
                print("✅ Fingerprint rotation passed")
            else:
                print("⚠️  Fingerprint rotation: No new fingerprint generated")
            
            print("\n🎉 All tests completed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Facebook Video Crawler System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for videos
  python run.py search "美食制作" --max-results 20 --region US
  
  # Download videos from URLs
  python run.py download "https://facebook.com/video1" "https://facebook.com/video2"
  
  # Check system status
  python run.py status
  
  # Show configuration
  python run.py config --show
  
  # Test system
  python run.py test
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for videos by keyword')
    search_parser.add_argument('keyword', help='Search keyword')
    search_parser.add_argument('--max-results', '-m', type=int, default=50, help='Maximum number of results')
    search_parser.add_argument('--region', '-r', help='Target region (US, UK, CA, etc.)')
    search_parser.add_argument('--download', '-d', action='store_true', help='Download videos after extraction')
    search_parser.add_argument('--export', '-e', action='store_true', help='Export metadata to JSON file')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download videos from URLs')
    download_parser.add_argument('urls', nargs='+', help='Facebook video URLs')
    download_parser.add_argument('--export', '-e', action='store_true', help='Export metadata to JSON file')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show crawler status and health')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show or modify configuration')
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('--show', '-s', action='store_true', help='Show current configuration')
    config_group.add_argument('--modify', '-m', help='Modify configuration (format: key=value)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test crawler functionality')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging
    setup_logging_from_config()
    
    # Run command
    try:
        if args.command == 'search':
            return asyncio.run(cmd_search(args))
        elif args.command == 'download':
            return asyncio.run(cmd_download(args))
        elif args.command == 'status':
            return asyncio.run(cmd_status(args))
        elif args.command == 'config':
            return asyncio.run(cmd_config(args))
        elif args.command == 'test':
            return asyncio.run(cmd_test(args))
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
