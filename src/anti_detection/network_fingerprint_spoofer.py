"""
Network Fingerprint Spoofer for Facebook Video Crawler System
Provides network characteristics spoofing and connection type simulation
"""

import random
import time
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..utils.logger import get_logger
from ..utils.config_manager import config


@dataclass
class NetworkProfile:
    """Network connection profile"""
    connection_type: str
    downlink: float
    rtt: int
    save_data: bool
    effective_type: str
    bandwidth: float


class NetworkFingerprintSpoofer:
    """Spoofs network characteristics to appear more human-like"""
    
    def __init__(self):
        """Initialize network fingerprint spoofer"""
        self.logger = get_logger("network_fingerprint_spoofer")
        self.config = config.get_anti_detection_config().get("network_spoofing", {})
        
        # Network profiles
        self.network_profiles = self._load_network_profiles()
        self.current_profile = None
        
        # Connection simulation
        self.connection_simulator = ConnectionSimulator()
        
        self.logger.info("Network fingerprint spoofer initialized")
    
    def _load_network_profiles(self) -> Dict[str, NetworkProfile]:
        """Load realistic network connection profiles"""
        return {
            "4g_fast": NetworkProfile(
                connection_type="4g",
                downlink=random.uniform(50.0, 100.0),
                rtt=random.randint(20, 50),
                save_data=False,
                effective_type="4g",
                bandwidth=random.uniform(50.0, 100.0)
            ),
            "4g_normal": NetworkProfile(
                connection_type="4g",
                downlink=random.uniform(20.0, 50.0),
                rtt=random.randint(50, 100),
                save_data=False,
                effective_type="4g",
                bandwidth=random.uniform(20.0, 50.0)
            ),
            "4g_slow": NetworkProfile(
                connection_type="4g",
                downlink=random.uniform(5.0, 20.0),
                rtt=random.randint(100, 200),
                save_data=True,
                effective_type="4g",
                bandwidth=random.uniform(5.0, 20.0)
            ),
            "3g": NetworkProfile(
                connection_type="3g",
                downlink=random.uniform(1.0, 5.0),
                rtt=random.randint(150, 300),
                save_data=True,
                effective_type="3g",
                bandwidth=random.uniform(1.0, 5.0)
            ),
            "wifi_fast": NetworkProfile(
                connection_type="wifi",
                downlink=random.uniform(100.0, 500.0),
                rtt=random.randint(10, 30),
                save_data=False,
                effective_type="4g",
                bandwidth=random.uniform(100.0, 500.0)
            ),
            "wifi_normal": NetworkProfile(
                connection_type="wifi",
                downlink=random.uniform(25.0, 100.0),
                rtt=random.randint(30, 80),
                save_data=False,
                effective_type="4g",
                bandwidth=random.uniform(25.0, 100.0)
            ),
            "ethernet": NetworkProfile(
                connection_type="ethernet",
                downlink=random.uniform(500.0, 1000.0),
                rtt=random.randint(5, 15),
                save_data=False,
                effective_type="4g",
                bandwidth=random.uniform(500.0, 1000.0)
            )
        }
    
    async def apply_network_profile(self, page, profile_name: str = None) -> bool:
        """Apply a specific network profile to the page"""
        try:
            if profile_name is None:
                profile_name = random.choice(list(self.network_profiles.keys()))
            
            if profile_name not in self.network_profiles:
                self.logger.error(f"Unknown network profile: {profile_name}")
                return False
            
            profile = self.network_profiles[profile_name]
            self.current_profile = profile
            
            # Inject network characteristics
            await self._inject_network_characteristics(page, profile)
            
            # Inject connection API spoofing
            await self._inject_connection_api(page, profile)
            
            # Inject performance API spoofing
            await self._inject_performance_api(page, profile)
            
            # Start connection simulation
            await self.connection_simulator.start_simulation(page, profile)
            
            self.logger.info(f"Applied network profile: {profile_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply network profile: {e}")
            return False
    
    async def _inject_network_characteristics(self, page, profile: NetworkProfile) -> None:
        """Inject network characteristics into the page"""
        script = f"""
        // Override navigator.connection
        if ('connection' in navigator) {{
            Object.defineProperty(navigator.connection, 'effectiveType', {{
                get: () => '{profile.effective_type}',
                configurable: true
            }});
            
            Object.defineProperty(navigator.connection, 'downlink', {{
                get: () => {profile.downlink},
                configurable: true
            }});
            
            Object.defineProperty(navigator.connection, 'rtt', {{
                get: () => {profile.rtt},
                configurable: true
            }});
            
            Object.defineProperty(navigator.connection, 'saveData', {{
                get: () => {str(profile.save_data).lower()},
                configurable: true
            }});
        }} else {{
            // Create connection object if it doesn't exist
            Object.defineProperty(navigator, 'connection', {{
                get: () => ({{
                    effectiveType: '{profile.effective_type}',
                    downlink: {profile.downlink},
                    rtt: {profile.rtt},
                    saveData: {str(profile.save_data).lower()}
                }}),
                configurable: true
            }});
        }}
        
        // Override navigator.onLine
        Object.defineProperty(navigator, 'onLine', {{
            get: () => true,
            configurable: true
        }});
        
        // Override navigator.connection.type
        if ('connection' in navigator) {{
            Object.defineProperty(navigator.connection, 'type', {{
                get: () => '{profile.connection_type}',
                configurable: true
            }});
        }}
        """
        
        await page.add_init_script(script)
    
    async def _inject_connection_api(self, page, profile: NetworkProfile) -> None:
        """Inject connection API spoofing"""
        script = f"""
        // Override fetch API to simulate network delays
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {{
            const startTime = performance.now();
            
            try {{
                const response = await originalFetch(...args);
                
                // Simulate network delay based on profile
                const delay = {profile.rtt} + Math.random() * 50;
                await new Promise(resolve => setTimeout(resolve, delay));
                
                const endTime = performance.now();
                console.log(`[Network Sim] Fetch completed in ${{endTime - startTime}}ms`);
                
                return response;
            }} catch (error) {{
                // Simulate network errors occasionally
                if (Math.random() < 0.01) {{
                    throw new Error('Network error simulation');
                }}
                throw error;
            }}
        }};
        
        // Override XMLHttpRequest to simulate network delays
        const originalXHROpen = XMLHttpRequest.prototype.open;
        const originalXHRSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(method, url, ...args) {{
            this._startTime = performance.now();
            return originalXHROpen.call(this, method, url, ...args);
        }};
        
        XMLHttpRequest.prototype.send = function(...args) {{
            const xhr = this;
            const originalOnReadyStateChange = xhr.onreadystatechange;
            
            xhr.onreadystatechange = function() {{
                if (xhr.readyState === 4) {{
                    const endTime = performance.now();
                    const delay = {profile.rtt} + Math.random() * 50;
                    
                    setTimeout(() => {{
                        console.log(`[Network Sim] XHR completed in ${{endTime - xhr._startTime}}ms`);
                    }}, delay);
                }}
                
                if (originalOnReadyStateChange) {{
                    originalOnReadyStateChange.apply(xhr, arguments);
                }}
            }};
            
            return originalXHRSend.apply(this, args);
        }};
        """
        
        await page.add_init_script(script)
    
    async def _inject_performance_api(self, page, profile: NetworkProfile) -> None:
        """Inject performance API spoofing"""
        script = f"""
        // Override performance.timing for network simulation
        if ('performance' in window && 'timing' in performance) {{
            const originalTiming = performance.timing;
            
            Object.defineProperty(performance.timing, 'navigationStart', {{
                get: () => Date.now() - Math.random() * 1000,
                configurable: true
            }});
            
            Object.defineProperty(performance.timing, 'domainLookupStart', {{
                get: () => performance.timing.navigationStart + {profile.rtt} + Math.random() * 50,
                configurable: true
            }});
            
            Object.defineProperty(performance.timing, 'domainLookupEnd', {{
                get: () => performance.timing.domainLookupStart + Math.random() * 20,
                configurable: true
            }});
            
            Object.defineProperty(performance.timing, 'connectStart', {{
                get: () => performance.timing.domainLookupEnd + Math.random() * 10,
                configurable: true
            }});
            
            Object.defineProperty(performance.timing, 'connectEnd', {{
                get: () => performance.timing.connectStart + Math.random() * 30,
                configurable: true
            }});
        }}
        
        // Override performance.now for consistent timing
        const originalNow = performance.now;
        let timeOffset = 0;
        
        performance.now = function() {{
            return originalNow.call(performance) + timeOffset;
        }};
        
        // Add random time offset
        timeOffset = Math.random() * 1000;
        """
        
        await page.add_init_script(script)
    
    def get_current_profile(self) -> Optional[NetworkProfile]:
        """Get current network profile"""
        return self.current_profile
    
    async def rotate_network_profile(self) -> None:
        """Rotate to a new network profile"""
        profile_name = random.choice(list(self.network_profiles.keys()))
        self.logger.info(f"Rotating to network profile: {profile_name}")
        
        # Update current profile
        self.current_profile = self.network_profiles[profile_name]


class ConnectionSimulator:
    """Simulates realistic network connection behavior"""
    
    def __init__(self):
        """Initialize connection simulator"""
        self.logger = get_logger("connection_simulator")
        self.simulation_active = False
        self.simulation_task = None
    
    async def start_simulation(self, page, profile: NetworkProfile) -> None:
        """Start network connection simulation"""
        try:
            if self.simulation_active:
                await self.stop_simulation()
            
            self.simulation_active = True
            self.simulation_task = asyncio.create_task(
                self._run_simulation(page, profile)
            )
            
            self.logger.info("Network simulation started")
            
        except Exception as e:
            self.logger.error(f"Failed to start network simulation: {e}")
    
    async def stop_simulation(self) -> None:
        """Stop network connection simulation"""
        try:
            self.simulation_active = False
            if self.simulation_task:
                self.simulation_task.cancel()
                try:
                    await self.simulation_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Network simulation stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop network simulation: {e}")
    
    async def _run_simulation(self, page, profile: NetworkProfile) -> None:
        """Run the network simulation loop"""
        try:
            while self.simulation_active:
                # Simulate network fluctuations
                await self._simulate_network_fluctuations(page, profile)
                
                # Simulate occasional disconnections
                if random.random() < 0.001:  # 0.1% chance
                    await self._simulate_disconnection(page)
                
                # Wait before next simulation cycle
                await asyncio.sleep(random.uniform(5, 15))
                
        except asyncio.CancelledError:
            self.logger.debug("Network simulation cancelled")
        except Exception as e:
            self.logger.error(f"Network simulation error: {e}")
    
    async def _simulate_network_fluctuations(self, page, profile: NetworkProfile) -> None:
        """Simulate realistic network speed fluctuations"""
        try:
            # Randomly adjust network characteristics
            fluctuation_factor = random.uniform(0.8, 1.2)
            
            script = f"""
            if ('connection' in navigator) {{
                Object.defineProperty(navigator.connection, 'downlink', {{
                    get: () => {profile.downlink * fluctuation_factor},
                    configurable: true
                }});
                
                Object.defineProperty(navigator.connection, 'rtt', {{
                    get: () => {int(profile.rtt * fluctuation_factor)},
                    configurable: true
                }});
            }}
            """
            
            await page.evaluate(script)
            
        except Exception as e:
            self.logger.debug(f"Network fluctuation simulation failed: {e}")
    
    async def _simulate_disconnection(self, page) -> None:
        """Simulate brief network disconnection"""
        try:
            self.logger.debug("Simulating network disconnection")
            
            # Set offline status
            await page.evaluate("""
                Object.defineProperty(navigator, 'onLine', {
                    get: () => false,
                    configurable: true
                });
            """)
            
            # Wait for disconnection duration
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Restore online status
            await page.evaluate("""
                Object.defineProperty(navigator, 'onLine', {
                    get: () => true,
                    configurable: true
                });
            """)
            
            self.logger.debug("Network disconnection simulation completed")
            
        except Exception as e:
            self.logger.debug(f"Disconnection simulation failed: {e}")


# Global network fingerprint spoofer instance
network_fingerprint_spoofer = NetworkFingerprintSpoofer()
