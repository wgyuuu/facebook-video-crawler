"""
Behavior Simulator for Facebook Video Crawler System
"""

import random
import time
from typing import Dict, Any

from ..utils.logger import get_logger
from ..utils.config_manager import config


class BehaviorSimulator:
    """Simulates human-like behavior patterns"""
    
    def __init__(self):
        """Initialize behavior simulator"""
        self.logger = get_logger("behavior_simulator")
        self.config = config.get_anti_detection_config().get("behavior", {})
        self.logger.info("Behavior simulator initialized")
    
    def simulate_mouse_movement(self, page, target_selector: str = None) -> bool:
        """Simulate natural mouse movement"""
        try:
            if not self.config.get("mouse_simulation", True):
                return True
            
            # Random mouse movement
            target_x = random.randint(100, 800)
            target_y = random.randint(100, 600)
            page.mouse.move(target_x, target_y)
            
            self.logger.debug(f"Mouse movement simulated to ({target_x}, {target_y})")
            return True
            
        except Exception as e:
            self.logger.warning(f"Mouse movement simulation failed: {e}")
            return False
    
    def simulate_click(self, page, selector: str, click_type: str = "left") -> bool:
        """Simulate natural click behavior"""
        try:
            # Hover over element first
            page.hover(selector)
            time.sleep(random.uniform(0.1, 0.3))
            
            # Perform click
            page.click(selector)
            time.sleep(random.uniform(0.1, 0.3))
            
            self.logger.debug(f"Click simulated on: {selector}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Click simulation failed: {e}")
            return False
    
    def simulate_scroll(self, page, direction: str = "down", distance: int = None) -> bool:
        """Simulate natural scrolling behavior"""
        try:
            if not self.config.get("scroll_simulation", True):
                return True
            
            # Random distance if not specified
            if distance is None:
                distance = random.randint(100, 500)
            
            # Execute scroll
            if direction == "down":
                page.evaluate(f"window.scrollBy(0, {distance})")
            elif direction == "up":
                page.evaluate(f"window.scrollBy(0, -{distance})")
            
            # Random delay after scroll
            time.sleep(random.uniform(0.5, 1.5))
            
            self.logger.debug(f"Scroll simulated: {direction} {distance}px")
            return True
            
        except Exception as e:
            self.logger.warning(f"Scroll simulation failed: {e}")
            return False


# Global behavior simulator instance
behavior_simulator = BehaviorSimulator()
