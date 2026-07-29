import os
import gc
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """
    Monitor system memory usage to enforce RAM constraints.
    Provides methods to check current usage and trigger garbage collection.
    """
    
    def __init__(self, warning_threshold_gb: float = 12.0, critical_threshold_gb: float = 14.0):
        """
        Initialize memory monitor with thresholds.
        
        Args:
            warning_threshold_gb: GB at which to log warnings
            critical_threshold_gb: GB at which to suggest batch size reduction
        """
        self.warning_threshold_gb = warning_threshold_gb
        self.critical_threshold_gb = critical_threshold_gb
        self._start_time = datetime.now()
        self._peak_memory_gb = 0.0
    
    def get_memory_usage_gb(self) -> float:
        """
        Get current memory usage in GB.
        
        Returns:
            Current memory usage in GB (float)
        """
        try:
            # Try psutil first (most accurate)
            import psutil
            process = psutil.Process(os.getpid())
            memory_bytes = process.memory_info().rss
            memory_gb = memory_bytes / (1024 ** 3)
            
            # Update peak memory
            if memory_gb > self._peak_memory_gb:
                self._peak_memory_gb = memory_gb
            
            return memory_gb
            
        except ImportError:
            # Fallback: read from /proc/meminfo (Linux only)
            try:
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                
                # ParseVmRSS from /proc/<pid>/status
                pid = os.getpid()
                with open(f'/proc/{pid}/status', 'r') as status_file:
                    status_lines = status_file.readlines()
                
                for line in status_lines:
                    if line.startswith('VmRSS:'):
                        # Value is in kB
                        value_kb = int(line.split()[1])
                        memory_gb = value_kb / (1024 * 1024)
                        return memory_gb
                        
            except Exception as e:
                logger.warning(f"Could not read memory info: {e}")
                return 0.0
        
        except Exception as e:
            logger.warning(f"Memory monitoring failed: {e}")
            return 0.0
    
    def check_and_warn(self) -> bool:
        """
        Check current memory usage and log warnings if thresholds exceeded.
        
        Returns:
            True if memory usage is critical, False otherwise
        """
        current_gb = self.get_memory_usage_gb()
        
        if current_gb >= self.critical_threshold_gb:
            logger.critical(
                f"CRITICAL: Memory usage at {current_gb:.2f}GB "
                f"(threshold: {self.critical_threshold_gb}GB). "
                "Consider reducing batch size."
            )
            return True
        elif current_gb >= self.warning_threshold_gb:
            logger.warning(
                f"WARNING: Memory usage at {current_gb:.2f}GB "
                f"(threshold: {self.warning_threshold_gb}GB)"
            )
            return False
        
        return False
    
    def force_gc(self) -> float:
        """
        Force garbage collection and return memory freed.
        
        Returns:
            Memory usage after GC in GB
        """
        gc.collect()
        new_usage = self.get_memory_usage_gb()
        logger.debug(f"Garbage collection completed. Memory: {new_usage:.2f}GB")
        return new_usage
    
    def get_peak_memory_gb(self) -> float:
        """Get peak memory usage since monitor initialization."""
        return self._peak_memory_gb
    
    def get_runtime_seconds(self) -> float:
        """Get runtime since monitor initialization in seconds."""
        return (datetime.now() - self._start_time).total_seconds()

def get_available_ram_gb() -> float:
    """
    Estimate total available RAM on the system.
    
    Returns:
        Estimated available RAM in GB
    """
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except ImportError:
        # Fallback: read from /proc/meminfo
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                if line.startswith('MemAvailable:'):
                    value_kb = int(line.split()[1])
                    return value_kb / (1024 * 1024)
        except:
            pass
    
    # Default safe value
    return 8.0
