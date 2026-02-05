"""
HX365 Command Center - Hardware Optimizer Module
==================================================

Performance optimization for AMD Ryzen 9 HX processors and XDNA NPU.
Implements CPU affinity, NPU activity monitoring, and MCDM counter reading.
"""

import asyncio
import os
import time
import psutil
import logging
import subprocess
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from hx365_core import hx365_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HX365-Hardware")

# Configuration for Ryzen 9 HX optimization
RYZEN_9_HX_CORE_COUNT = int(os.getenv("RYZEN_CORES", str(psutil.cpu_count(logical=False))))
ENABLE_NPU_MONITORING = os.getenv("ENABLE_NPU_MONITORING", "true").lower() == "true"

class NPUMode(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    AUTO = "auto"

@dataclass
class HardwareMetrics:
    """Hardware performance metrics"""
    cpu_affinity_cores: List[int]
    cpu_usage_per_core: List[float]
    npu_utilization: float
    npu_power: float
    npu_temperature: float
    memory_bandwidth: float
    cache_hit_rate: float
    timestamp: float

class CPUAffinityManager:
    """
    Manages CPU affinity for Ryzen 9 HX optimization
    """
    
    def __init__(self):
        self.original_affinity = None
        self.optimized_affinity = None
        self.is_applied = False
        self.process = psutil.Process()
    
    def get_high_performance_cores(self) -> List[int]:
        """
        Get high-performance cores (typically CCX 0 on Ryzen)
        This is a simplified approach - in reality, we'd detect CCX topology
        """
        # For Ryzen 9, typically the first physical cores are on CCX 0
        # which has direct access to more cache and memory controllers
        physical_cores = list(range(RYZEN_9_HX_CORE_COUNT))
        
        # On Ryzen 9 5900HX, CCX 0 contains cores 0-2, 8-10 (0-indexed)
        # For simplicity, we'll use the first half of physical cores
        ccx_cores = physical_cores[:len(physical_cores)//2]
        return ccx_cores
    
    def apply_affinity(self, cores: Optional[List[int]] = None) -> bool:
        """
        Apply CPU affinity to specified cores
        """
        try:
            if cores is None:
                cores = self.get_high_performance_cores()
            
            # Save original affinity
            self.original_affinity = self.process.cpu_affinity()
            
            # Apply new affinity
            self.process.cpu_affinity(cores)
            self.optimized_affinity = cores
            self.is_applied = True
            
            logger.info(f"CPU Affinity applied to cores: {cores}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply CPU affinity: {e}")
            return False
    
    def restore_affinity(self):
        """
        Restore original CPU affinity
        """
        if self.original_affinity:
            try:
                self.process.cpu_affinity(self.original_affinity)
                self.is_applied = False
                logger.info("Original CPU affinity restored")
            except Exception as e:
                logger.error(f"Failed to restore CPU affinity: {e}")
    
    def get_current_affinity(self) -> List[int]:
        """
        Get current CPU affinity
        """
        try:
            return self.process.cpu_affinity()
        except Exception as e:
            logger.error(f"Failed to get CPU affinity: {e}")
            return []

class NPUMonitor:
    """
    Monitors NPU activity via MCDM counters (AMD-specific)
    """
    
    def __init__(self, enabled: bool = ENABLE_NPU_MONITORING):
        self.enabled = enabled
        self.mode = NPUMode.AUTO
        self.mcdm_available = False
        self._detect_mcdm_support()
    
    def _detect_mcdm_support(self):
        """
        Detect if MCDM (Machine Learning Compute Device Manager) is available
        """
        try:
            # Check for AMD ML libraries
            import platform
            if platform.system() == "Windows":
                # Check for AMD drivers and MCDM
                result = subprocess.run(
                    ["wmic", "path", "win32_videocontroller", "get", "name"],
                    capture_output=True, text=True
                )
                if "Radeon" in result.stdout or "AMD" in result.stdout:
                    self.mcdm_available = True
            else:
                # On Linux, check for AMD drivers
                if os.path.exists("/sys/class/kfd/kfd/topology/nodes/"):
                    self.mcdm_available = True
            
            logger.info(f"MCDM support detected: {self.mcdm_available}")
        except Exception as e:
            logger.warning(f"Could not detect MCDM support: {e}")
            self.mcdm_available = False
    
    def read_npu_metrics(self) -> Dict[str, float]:
        """
        Read NPU metrics from MCDM or other AMD-specific interfaces
        This is a simulated implementation - real implementation would interface with AMD drivers
        """
        if not self.enabled or not self.mcdm_available:
            return {
                "utilization": 0.0,
                "power": 0.0,
                "temperature": 0.0
            }
        
        # Simulated metrics - in real implementation, these would come from MCDM
        try:
            # Placeholder for actual MCDM counter reading
            # This would interface with AMD's ML compute stack
            utilization = self._read_utilization_from_mcdm()
            power = self._read_power_from_mcdm()
            temperature = self._read_temperature_from_mcdm()
            
            return {
                "utilization": utilization,
                "power": power,
                "temperature": temperature
            }
        except Exception as e:
            logger.warning(f"Could not read NPU metrics: {e}")
            return {
                "utilization": 0.0,
                "power": 0.0,
                "temperature": 0.0
            }
    
    def _read_utilization_from_mcdm(self) -> float:
        """
        Read NPU utilization from MCDM (simulated)
        """
        # In real implementation, this would read from AMD's device manager
        # For simulation, return a value based on system load
        return min(psutil.cpu_percent() / 100.0, 1.0) * 0.8  # Cap at 80% for simulation
    
    def _read_power_from_mcdm(self) -> float:
        """
        Read NPU power consumption from MCDM (simulated)
        """
        # In real implementation, this would read power counters from AMD drivers
        return 15.0 + (psutil.cpu_percent() / 100.0) * 10.0  # Base 15W + load
    
    def _read_temperature_from_mcdm(self) -> float:
        """
        Read NPU temperature from MCDM (simulated)
        """
        # In real implementation, this would read thermal sensors
        return 45.0 + (psutil.cpu_percent() / 100.0) * 20.0  # Base 45°C + load
    
    def set_npu_mode(self, mode: NPUMode):
        """
        Set NPU operation mode
        """
        self.mode = mode
        logger.info(f"NPU mode set to: {mode.value}")

class PerformanceGovernor:
    """
    Performance governor for Ryzen 9 HX and NPU
    """
    
    def __init__(self):
        self.cpu_manager = CPUAffinityManager()
        self.npu_monitor = NPUMonitor()
        self.is_active = False
        self.monitoring_task = None
        self.metrics_history: List[HardwareMetrics] = []
        self.max_history = 100
    
    def optimize_for_inference(self):
        """
        Apply optimizations specifically for AI inference
        """
        # Apply CPU affinity to high-performance cores
        success = self.cpu_manager.apply_affinity()
        if success:
            logger.info("Applied CPU affinity optimization for inference")
        else:
            logger.error("Failed to apply CPU affinity optimization")
        
        # Enable NPU monitoring
        self.npu_monitor.set_npu_mode(NPUMode.ENABLED)
        
        return success
    
    def start_monitoring(self):
        """
        Start background monitoring of hardware metrics
        """
        if not self.is_active:
            self.is_active = True
            self.monitoring_task = asyncio.create_task(self._monitor_hardware())
            logger.info("Hardware monitoring started")
    
    def stop_monitoring(self):
        """
        Stop background monitoring
        """
        if self.is_active and self.monitoring_task:
            self.monitoring_task.cancel()
            self.is_active = False
            logger.info("Hardware monitoring stopped")
    
    async def _monitor_hardware(self):
        """
        Background task to continuously monitor hardware metrics
        """
        while self.is_active:
            try:
                metrics = self.get_current_hardware_metrics()
                self.metrics_history.append(metrics)
                
                # Keep history size manageable
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history.pop(0)
                
                # Adjust performance based on metrics
                await self._adjust_performance(metrics)
                
                # Monitor every 1 second
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                logger.info("Hardware monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in hardware monitoring: {e}")
                await asyncio.sleep(5.0)  # Wait longer on error
    
    def get_current_hardware_metrics(self) -> HardwareMetrics:
        """
        Get current hardware metrics
        """
        current_time = time.time()
        
        # Get CPU affinity
        affinity = self.cpu_manager.get_current_affinity()
        
        # Get CPU usage per core
        cpu_percentages = psutil.cpu_percent(percpu=True, interval=0.1)
        
        # Get NPU metrics
        npu_metrics = self.npu_monitor.read_npu_metrics()
        
        # Placeholder for other metrics (would require specialized libraries)
        memory_bandwidth = 0.0  # Would come from specialized monitoring
        cache_hit_rate = 0.0    # Would come from performance counters
        
        return HardwareMetrics(
            cpu_affinity_cores=affinity,
            cpu_usage_per_core=cpu_percentages,
            npu_utilization=npu_metrics["utilization"],
            npu_power=npu_metrics["power"],
            npu_temperature=npu_metrics["temperature"],
            memory_bandwidth=memory_bandwidth,
            cache_hit_rate=cache_hit_rate,
            timestamp=current_time
        )
    
    async def _adjust_performance(self, metrics: HardwareMetrics):
        """
        Adjust performance based on current metrics
        """
        # Example: If NPU temperature is too high, throttle
        if metrics.npu_temperature > 85.0:  # High temperature threshold
            logger.warning(f"NPU temperature high: {metrics.npu_temperature:.1f}°C")
            # Could implement throttling here
        
        # Example: If CPU usage is low, consider power saving
        avg_cpu = sum(metrics.cpu_usage_per_core) / len(metrics.cpu_usage_per_core)
        if avg_cpu < 10.0:  # Low usage
            # Could adjust power profile here
            pass
    
    def get_historical_metrics(self, minutes: int = 5) -> List[HardwareMetrics]:
        """
        Get historical hardware metrics
        """
        cutoff_time = time.time() - (minutes * 60)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def apply_system_wide_optimizations(self):
        """
        Apply system-wide optimizations for Ryzen 9 HX
        """
        # This would include:
        # - Setting process priority
        # - Configuring NUMA policies
        # - Adjusting kernel parameters (on Linux)
        # - Applying Windows power profiles (on Windows)
        
        logger.info("Applying system-wide Ryzen 9 HX optimizations")
        
        # Set high priority for this process
        try:
            import psutil
            p = psutil.Process()
            if hasattr(p, 'nice'):
                if os.name == 'nt':  # Windows
                    p.nice(psutil.HIGH_PRIORITY_CLASS)
                else:  # Unix-like
                    p.nice(-10)  # Higher priority (requires appropriate permissions)
            logger.info("Set process priority for inference")
        except Exception as e:
            logger.warning(f"Could not set process priority: {e}")
        
        # Apply CPU affinity
        self.optimize_for_inference()

class HX365HardwareOptimizer:
    """
    Main hardware optimizer class that ties everything together
    """
    
    def __init__(self):
        self.governor = PerformanceGovernor()
        self.is_initialized = False
    
    async def initialize(self):
        """
        Initialize the hardware optimizer
        """
        if not self.is_initialized:
            # Apply system-wide optimizations
            self.governor.apply_system_wide_optimizations()
            
            # Start monitoring
            self.governor.start_monitoring()
            
            self.is_initialized = True
            logger.info("HX365 Hardware Optimizer initialized")
    
    async def shutdown(self):
        """
        Shutdown the hardware optimizer
        """
        if self.is_initialized:
            # Stop monitoring
            self.governor.stop_monitoring()
            
            # Restore original CPU affinity
            self.governor.cpu_manager.restore_affinity()
            
            self.is_initialized = False
            logger.info("HX365 Hardware Optimizer shutdown")
    
    def get_hardware_status(self) -> Dict[str, any]:
        """
        Get current hardware status and metrics
        """
        current_metrics = self.governor.get_current_hardware_metrics()
        
        return {
            "timestamp": current_metrics.timestamp,
            "cpu": {
                "affinity_cores": current_metrics.cpu_affinity_cores,
                "usage_per_core": current_metrics.cpu_usage_per_core,
                "avg_usage": sum(current_metrics.cpu_usage_per_core) / len(current_metrics.cpu_usage_per_core)
            },
            "npu": {
                "utilization": current_metrics.npu_utilization,
                "power": current_metrics.npu_power,
                "temperature": current_metrics.npu_temperature,
                "enabled": self.governor.npu_monitor.enabled,
                "mcdm_available": self.governor.npu_monitor.mcdm_available
            },
            "system": {
                "optimized": self.governor.cpu_manager.is_applied,
                "monitoring_active": self.governor.is_active
            }
        }
    
    def get_optimization_suggestions(self) -> List[str]:
        """
        Get suggestions for hardware optimization
        """
        suggestions = []
        metrics = self.governor.get_current_hardware_metrics()
        
        # Check if optimizations are applied
        if not self.governor.cpu_manager.is_applied:
            suggestions.append("Apply CPU affinity to high-performance cores")
        
        # Check NPU status
        if not self.governor.npu_monitor.enabled:
            suggestions.append("Enable NPU monitoring for XDNA acceleration")
        
        # Check temperature
        if metrics.npu_temperature > 75.0:
            suggestions.append("NPU temperature elevated - consider cooling or reducing load")
        
        # Check utilization
        if metrics.npu_utilization < 0.1 and sum(metrics.cpu_usage_per_core) / len(metrics.cpu_usage_per_core) > 50.0:
            suggestions.append("High CPU usage with low NPU utilization - consider optimizing model for NPU")
        
        return suggestions

# Global instance
hardware_optimizer = HX365HardwareOptimizer()

# Initialize the optimizer when module is loaded
async def init_hardware_optimizer():
    await hardware_optimizer.initialize()

# Run initialization
if __name__ != "__main__":
    # If imported, initialize in the background
    asyncio.create_task(init_hardware_optimizer())