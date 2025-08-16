"""
Advanced Anti-Detection Demo for Facebook Video Crawler
Demonstrates the advanced fingerprint spoofing, behavior simulation, and session management features
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from main import FacebookVideoCrawler
from anti_detection.advanced_fingerprint_manager import advanced_fingerprint_manager
from anti_detection.advanced_behavior_simulator import advanced_behavior_simulator
from anti_detection.session_manager import session_manager
from anti_detection.network_fingerprint_spoofer import network_fingerprint_spoofer


async def demo_advanced_fingerprint():
    """Demonstrate advanced fingerprint management"""
    print("🔍 Advanced Fingerprint Management Demo")
    print("=" * 50)
    
    # Show available device profiles
    profiles = advanced_fingerprint_manager.real_device_profiles
    print(f"Available device profiles: {list(profiles.keys())}")
    
    # Show current fingerprint
    current_fp = advanced_fingerprint_manager.get_current_fingerprint()
    print(f"Current fingerprint: {current_fp['device_profile']}")
    
    # Rotate fingerprint
    print("Rotating fingerprint...")
    await advanced_fingerprint_manager.rotate_fingerprint()
    
    new_fp = advanced_fingerprint_manager.get_current_fingerprint()
    print(f"New fingerprint: {new_fp['device_profile']}")
    
    print()


async def demo_advanced_behavior():
    """Demonstrate advanced behavior simulation"""
    print("🎭 Advanced Behavior Simulation Demo")
    print("=" * 50)
    
    # Show behavior patterns
    patterns = advanced_behavior_simulator.typing_patterns
    print(f"Typing speed options: {list(patterns['typing_speed'].keys())}")
    
    # Show current stats
    stats = advanced_behavior_simulator.get_behavior_stats()
    print(f"Current behavior stats: {stats}")
    
    print()


async def demo_network_spoofing():
    """Demonstrate network fingerprint spoofing"""
    print("🌐 Network Fingerprint Spoofing Demo")
    print("=" * 50)
    
    # Show available network profiles
    profiles = network_fingerprint_spoofer.network_profiles
    print(f"Available network profiles: {list(profiles.keys())}")
    
    # Show current profile
    current_profile = network_fingerprint_spoofer.get_current_profile()
    if current_profile:
        print(f"Current network profile: {current_profile.connection_type} - {current_profile.effective_type}")
        print(f"  Downlink: {current_profile.downlink:.1f} Mbps")
        print(f"  RTT: {current_profile.rtt} ms")
        print(f"  Save Data: {current_profile.save_data}")
    
    print()


async def demo_session_management():
    """Demonstrate session management"""
    print("🔐 Session Management Demo")
    print("=" * 50)
    
    # Show account stats
    account_stats = session_manager.get_account_stats()
    print(f"Total accounts: {account_stats['total_accounts']}")
    print(f"Current account index: {account_stats['current_account_index']}")
    print(f"Total sessions: {account_stats['total_sessions']}")
    
    # Show available sessions
    available_sessions = session_manager.get_available_sessions()
    print(f"Available sessions: {len(available_sessions)}")
    
    print()


async def demo_full_crawler_integration():
    """Demonstrate full crawler integration with advanced features"""
    print("🚀 Full Crawler Integration Demo")
    print("=" * 50)
    
    try:
        # Create crawler with advanced features
        async with FacebookVideoCrawler() as crawler:
            print("✅ Crawler started successfully")
            
            # Show advanced anti-detection status
            stats = crawler.get_stats()
            advanced_stats = stats.get("advanced_anti_detection", {})
            
            print(f"Advanced fingerprint profile: {advanced_stats.get('fingerprint_profile', {}).get('device_profile', 'Unknown')}")
            print(f"Network profile: {advanced_stats.get('network_profile', {}).get('connection_type', 'Unknown')}")
            print(f"Session management: {'Enabled' if advanced_stats.get('session_stats') else 'Disabled'}")
            
            # Try to navigate to Facebook (without login)
            print("\n🌐 Testing navigation to Facebook...")
            if await crawler.crawler_engine.navigate_to("https://www.facebook.com/"):
                print("✅ Successfully navigated to Facebook")
                
                # Wait a bit to see the page
                await asyncio.sleep(3)
                
                # Get page title
                page_title = await crawler.crawler_engine.page.title()
                print(f"Page title: {page_title}")
                
                # Show current URL
                current_url = crawler.crawler_engine.page.url
                print(f"Current URL: {current_url}")
                
            else:
                print("❌ Failed to navigate to Facebook")
            
            print("\n✅ Full integration demo completed successfully")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all demos"""
    print("🎯 Facebook Video Crawler - Advanced Anti-Detection Demo")
    print("=" * 70)
    print()
    
    # Run individual demos
    await demo_advanced_fingerprint()
    await demo_advanced_behavior()
    await demo_network_spoofing()
    await demo_session_management()
    
    print("\n" + "=" * 70)
    print("🚀 Starting full crawler integration demo...")
    print()
    
    # Run full integration demo
    await demo_full_crawler_integration()
    
    print("\n" + "=" * 70)
    print("✅ All demos completed!")
    print("\n💡 Tips for using advanced anti-detection features:")
    print("   - Enable features in config/config.yaml")
    print("   - Configure multiple accounts for rotation")
    print("   - Set up proxies for better anonymity")
    print("   - Monitor behavior statistics for optimization")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
