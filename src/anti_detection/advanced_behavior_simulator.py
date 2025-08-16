"""
Advanced Behavior Simulator for Facebook Video Crawler System
Provides sophisticated human behavior simulation including typing patterns and mouse trails
"""

import random
import time
import math
import asyncio
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass

from ..utils.logger import get_logger
from ..utils.config_manager import config


@dataclass
class MousePoint:
    """Mouse position point with timestamp"""
    x: int
    y: int
    timestamp: float


class HumanBehaviorSimulator:
    """Advanced human behavior simulator with realistic patterns"""
    
    def __init__(self):
        """Initialize advanced behavior simulator"""
        self.logger = get_logger("advanced_behavior_simulator")
        self.config = config.get_anti_detection_config().get("advanced_behavior", {})
        
        # Mouse trail tracking
        self.mouse_trail: List[MousePoint] = []
        self.last_mouse_position: Optional[Tuple[int, int]] = None
        
        # Typing patterns
        self.typing_patterns = self._load_typing_patterns()
        
        # Behavior statistics
        self.behavior_stats = {
            "total_movements": 0,
            "total_clicks": 0,
            "total_typing": 0,
            "session_start": time.time()
        }
        
        self.logger.info("Advanced behavior simulator initialized")
    
    def _load_typing_patterns(self) -> Dict[str, Any]:
        """Load realistic typing patterns"""
        return {
            "typing_speed": {
                "slow": {"min": 0.1, "max": 0.3},
                "normal": {"min": 0.05, "max": 0.15},
                "fast": {"min": 0.02, "max": 0.08}
            },
            "pause_patterns": {
                "word_pause": {"probability": 0.3, "min": 0.2, "max": 0.8},
                "sentence_pause": {"probability": 0.1, "min": 0.5, "max": 1.5},
                "thinking_pause": {"probability": 0.05, "min": 1.0, "max": 3.0}
            },
            "error_patterns": {
                "typo_probability": 0.02,
                "correction_delay": {"min": 0.5, "max": 2.0}
            }
        }
    
    async def simulate_human_typing(self, page, element, text: str, 
                                  speed: str = "normal", 
                                  include_errors: bool = True) -> bool:
        """Simulate realistic human typing patterns"""
        try:
            self.logger.debug(f"Starting human typing simulation: {len(text)} characters")
            
            # Focus on element first
            await element.click()
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Clear existing content
            await element.fill("")
            await asyncio.sleep(random.uniform(0.1, 0.2))
            
            # Get typing speed configuration
            speed_config = self.typing_patterns["typing_speed"][speed]
            pause_config = self.typing_patterns["pause_patterns"]
            error_config = self.typing_patterns["error_patterns"]
            
            # Type each character with realistic delays
            for i, char in enumerate(text):
                # Basic typing delay
                base_delay = random.uniform(speed_config["min"], speed_config["max"])
                
                # Add word pause
                if char == " " and random.random() < pause_config["word_pause"]["probability"]:
                    base_delay += random.uniform(
                        pause_config["word_pause"]["min"], 
                        pause_config["word_pause"]["max"]
                    )
                
                # Add sentence pause
                if char in ".!?" and random.random() < pause_config["sentence_pause"]["probability"]:
                    base_delay += random.uniform(
                        pause_config["sentence_pause"]["min"], 
                        pause_config["sentence_pause"]["max"]
                    )
                
                # Add thinking pause
                if random.random() < pause_config["thinking_pause"]["probability"]:
                    base_delay += random.uniform(
                        pause_config["thinking_pause"]["min"], 
                        pause_config["thinking_pause"]["max"]
                    )
                
                # Simulate typing error and correction
                if include_errors and random.random() < error_config["typo_probability"]:
                    await self._simulate_typo_and_correction(element, char)
                else:
                    # Type character
                    await element.type(char)
                
                # Wait for calculated delay
                await asyncio.sleep(base_delay)
                
                # Update statistics
                self.behavior_stats["total_typing"] += 1
            
            self.logger.debug("Human typing simulation completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Human typing simulation failed: {e}")
            return False
    
    async def _simulate_typo_and_correction(self, element, char: str) -> None:
        """Simulate typing error and correction"""
        # Type wrong character
        wrong_char = random.choice("qwertyuiopasdfghjklzxcvbnm")
        await element.type(wrong_char)
        
        # Wait a bit
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Delete wrong character
        await element.press("Backspace")
        
        # Wait for correction delay
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        # Type correct character
        await element.type(char)
    
    async def simulate_mouse_trail(self, page, target_selector: str, 
                                 complexity: int = 4) -> bool:
        """Simulate realistic mouse movement with Bezier curve trajectory"""
        try:
            if not self.config.get("mouse_trail_simulation", True):
                return True
            
            # Get current mouse position
            current_pos = page.mouse.position
            if not current_pos:
                current_pos = (400, 300)  # Default position
            
            # Get target element position
            target_element = await page.query_selector(target_selector)
            if not target_element:
                self.logger.warning(f"Target element not found: {target_selector}")
                return False
            
            target_box = await target_element.bounding_box()
            target_pos = (
                target_box["x"] + target_box["width"] / 2,
                target_box["y"] + target_box["height"] / 2
            )
            
            # Generate Bezier curve control points
            control_points = self._generate_bezier_curve(
                current_pos, target_pos, complexity
            )
            
            # Move mouse along the curve
            for i, point in enumerate(control_points):
                # Add some randomness to the movement
                jitter_x = random.randint(-2, 2)
                jitter_y = random.randint(-2, 2)
                
                final_x = max(0, min(point[0] + jitter_x, 1920))
                final_y = max(0, min(point[1] + jitter_y, 1080))
                
                await page.mouse.move(final_x, final_y)
                
                # Variable delay based on distance
                distance = math.sqrt((final_x - current_pos[0])**2 + (final_y - current_pos[1])**2)
                delay = max(0.01, min(0.05, distance / 1000))
                await asyncio.sleep(delay)
                
                # Update current position
                current_pos = (final_x, final_y)
                
                # Store in trail
                self.mouse_trail.append(MousePoint(final_x, final_y, time.time()))
            
            # Update statistics
            self.behavior_stats["total_movements"] += 1
            
            self.logger.debug(f"Mouse trail simulation completed: {len(control_points)} points")
            return True
            
        except Exception as e:
            self.logger.error(f"Mouse trail simulation failed: {e}")
            return False
    
    def _generate_bezier_curve(self, start: Tuple[int, int], 
                              end: Tuple[int, int], 
                              complexity: int) -> List[Tuple[int, int]]:
        """Generate Bezier curve control points for natural mouse movement"""
        points = []
        
        # Generate random control points
        control_points = [start]
        for i in range(complexity):
            # Random intermediate point
            mid_x = (start[0] + end[0]) / 2 + random.randint(-100, 100)
            mid_y = (start[1] + end[1]) / 2 + random.randint(-100, 100)
            control_points.append((mid_x, mid_y))
        control_points.append(end)
        
        # Generate curve points using De Casteljau's algorithm
        steps = max(10, complexity * 3)
        for t in range(steps + 1):
            t_normalized = t / steps
            point = self._bezier_point(control_points, t_normalized)
            points.append((int(point[0]), int(point[1])))
        
        return points
    
    def _bezier_point(self, points: List[Tuple[int, int]], t: float) -> Tuple[float, float]:
        """Calculate point on Bezier curve using De Casteljau's algorithm"""
        if len(points) == 1:
            return points[0]
        
        new_points = []
        for i in range(len(points) - 1):
            x = (1 - t) * points[i][0] + t * points[i + 1][0]
            y = (1 - t) * points[i][1] + t * points[i + 1][1]
            new_points.append((x, y))
        
        return self._bezier_point(new_points, t)
    
    async def simulate_human_click(self, page, selector: str, 
                                 click_type: str = "left",
                                 include_hover: bool = True) -> bool:
        """Simulate realistic human click behavior"""
        try:
            # Hover over element first (if enabled)
            if include_hover:
                await page.hover(selector)
                hover_delay = random.uniform(0.1, 0.4)
                await asyncio.sleep(hover_delay)
            
            # Small random movement before click
            if random.random() < 0.3:
                await page.mouse.move(
                    page.mouse.position[0] + random.randint(-5, 5),
                    page.mouse.position[1] + random.randint(-5, 5)
                )
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Perform click
            if click_type == "left":
                await page.click(selector, button="left")
            elif click_type == "right":
                await page.click(selector, button="right")
            elif click_type == "double":
                await page.dblclick(selector)
            
            # Random delay after click
            click_delay = random.uniform(0.1, 0.3)
            await asyncio.sleep(click_delay)
            
            # Update statistics
            self.behavior_stats["total_clicks"] += 1
            
            self.logger.debug(f"Human click simulation completed: {click_type} click on {selector}")
            return True
            
        except Exception as e:
            self.logger.error(f"Human click simulation failed: {e}")
            return False
    
    async def simulate_human_scroll(self, page, direction: str = "down", 
                                  distance: int = None,
                                  smooth: bool = True) -> bool:
        """Simulate realistic human scrolling behavior"""
        try:
            if not self.config.get("scroll_simulation", True):
                return True
            
            # Random distance if not specified
            if distance is None:
                distance = random.randint(100, 500)
            
            if smooth:
                # Smooth scrolling with multiple small movements
                steps = random.randint(5, 15)
                step_distance = distance / steps
                
                for i in range(steps):
                    if direction == "down":
                        await page.evaluate(f"window.scrollBy(0, {step_distance})")
                    elif direction == "up":
                        await page.evaluate(f"window.scrollBy(0, -{step_distance})")
                    
                    # Random delay between steps
                    step_delay = random.uniform(0.02, 0.08)
                    await asyncio.sleep(step_delay)
            else:
                # Single scroll movement
                if direction == "down":
                    await page.evaluate(f"window.scrollBy(0, {distance})")
                elif direction == "up":
                    await page.evaluate(f"window.scrollBy(0, -{distance})")
            
            # Random delay after scroll
            scroll_delay = random.uniform(0.5, 1.5)
            await asyncio.sleep(scroll_delay)
            
            self.logger.debug(f"Human scroll simulation completed: {direction} {distance}px")
            return True
            
        except Exception as e:
            self.logger.error(f"Human scroll simulation failed: {e}")
            return False
    
    async def simulate_page_interaction(self, page, 
                                      interaction_type: str = "random") -> bool:
        """Simulate random page interactions to appear more human-like"""
        try:
            if interaction_type == "random":
                interaction_type = random.choice([
                    "mouse_movement", "scroll", "hover", "click_random"
                ])
            
            if interaction_type == "mouse_movement":
                # Random mouse movement
                target_x = random.randint(100, 800)
                target_y = random.randint(100, 600)
                await page.mouse.move(target_x, target_y)
                
            elif interaction_type == "scroll":
                # Random scroll
                direction = random.choice(["up", "down"])
                distance = random.randint(50, 200)
                await self.simulate_human_scroll(page, direction, distance)
                
            elif interaction_type == "hover":
                # Hover over random element
                elements = await page.query_selector_all("a, button, div[role='button']")
                if elements:
                    random_element = random.choice(elements)
                    await page.hover(random_element)
                    
            elif interaction_type == "click_random":
                # Click on random clickable element
                clickable_elements = await page.query_selector_all("a, button")
                if clickable_elements:
                    random_element = random.choice(clickable_elements)
                    await self.simulate_human_click(page, random_element)
            
            # Random delay after interaction
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Page interaction simulation failed: {e}")
            return False
    
    def get_behavior_stats(self) -> Dict[str, Any]:
        """Get behavior simulation statistics"""
        session_duration = time.time() - self.behavior_stats["session_start"]
        
        return {
            **self.behavior_stats,
            "session_duration": session_duration,
            "movements_per_minute": (self.behavior_stats["total_movements"] / session_duration) * 60,
            "clicks_per_minute": (self.behavior_stats["total_clicks"] / session_duration) * 60,
            "typing_speed": (self.behavior_stats["total_typing"] / session_duration) * 60
        }
    
    def reset_stats(self) -> None:
        """Reset behavior statistics"""
        self.behavior_stats = {
            "total_movements": 0,
            "total_clicks": 0,
            "total_typing": 0,
            "session_start": time.time()
        }
        self.mouse_trail.clear()


# Global advanced behavior simulator instance
advanced_behavior_simulator = HumanBehaviorSimulator()
