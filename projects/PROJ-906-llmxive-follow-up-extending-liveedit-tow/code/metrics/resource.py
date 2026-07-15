"""
Memory profiling wrapper for tracking peak RAM usage per clip.

This module provides a context manager and utility functions to measure
and record peak memory consumption during video processing operations.
"""
import os
import gc
import logging
import threading
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
import time

# Try to import psutil for accurate memory measurement
# If not available, fall back to /proc on Linux or basic estimates
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    # Fallback for Linux systems
    if os.name == 'posix' and os.path.exists('/proc/self/status'):
        HAS_PROC = True
    else:
        HAS_PROC = False

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryProfileRecord:
    """Data class to store memory profiling results for a single clip."""
    clip_id: str
    peak_memory_mb: float
    start_time: float
    end_time: float
    duration_seconds: float
    process_id: int
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization."""
        return {
            'clip_id': self.clip_id,
            'peak_memory_mb': self.peak_memory_mb,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_seconds': self.duration_seconds,
            'process_id': self.process_id,
            'notes': self.notes,
            'metadata': self.metadata
        }


class MemoryProfiler:
    """
    Context manager and utility class for tracking peak RAM usage.
    
    Uses psutil if available for cross-platform accuracy, otherwise
    falls back to /proc on Linux systems.
    """
    
    def __init__(self, clip_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize the memory profiler.
        
        Args:
            clip_id: Unique identifier for the video clip being processed.
            metadata: Optional dictionary of additional context to store.
        """
        self.clip_id = clip_id
        self.metadata = metadata or {}
        self._peak_memory_mb: float = 0.0
        self._start_time: float = 0.0
        self._end_time: float = 0.0
        self._process = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        
        if HAS_PSUTIL:
            self._process = psutil.Process(os.getpid())
        elif HAS_PROC:
            logger.warning("psutil not available. Using /proc fallback (Linux only).")
        else:
            logger.warning("Memory profiling limited: psutil not available and not on Linux.")
    
    def _get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        if HAS_PSUTIL and self._process:
            # RSS (Resident Set Size) is the non-swapped physical memory
            return self._process.memory_info().rss / (1024 * 1024)
        elif HAS_PROC:
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # VmRSS is in kB
                            return int(line.split()[1]) / 1024.0
            except Exception as e:
                logger.error(f"Failed to read /proc/self/status: {e}")
            return 0.0
        else:
            logger.warning("No memory measurement backend available.")
            return 0.0
    
    def _monitor_peak(self):
        """Background thread to continuously monitor peak memory."""
        while not self._stop_monitoring.is_set():
            current = self._get_current_memory_mb()
            if current > self._peak_memory_mb:
                self._peak_memory_mb = current
            time.sleep(0.01)  # 10ms sampling interval
    
    def __enter__(self):
        """Start memory profiling."""
        gc.collect()  # Force garbage collection before starting
        self._start_time = time.time()
        self._peak_memory_mb = 0.0
        
        # Start background monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_peak, daemon=True)
        self._monitor_thread.start()
        
        logger.debug(f"Memory profiling started for clip: {self.clip_id}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop memory profiling and finalize record."""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=0.5)
        
        self._end_time = time.time()
        
        # Final memory check to capture any spikes at exit
        final_memory = self._get_current_memory_mb()
        if final_memory > self._peak_memory_mb:
            self._peak_memory_mb = final_memory
        
        duration = self._end_time - self._start_time
        
        record = MemoryProfileRecord(
            clip_id=self.clip_id,
            peak_memory_mb=self._peak_memory_mb,
            start_time=self._start_time,
            end_time=self._end_time,
            duration_seconds=duration,
            process_id=os.getpid(),
            notes="Exception occurred" if exc_type else "Completed successfully",
            metadata=self.metadata
        )
        
        logger.info(f"Memory profile for {self.clip_id}: Peak={self._peak_memory_mb:.2f}MB, Duration={duration:.2f}s")
        
        # Store the record as an attribute for retrieval
        self.record = record
        
        return False  # Don't suppress exceptions
    
    def get_record(self) -> MemoryProfileRecord:
        """
        Get the memory profile record.
        
        Must be called after exiting the context manager.
        
        Returns:
            MemoryProfileRecord: The recorded metrics.
        """
        if not hasattr(self, 'record'):
            raise RuntimeError("Record not available. Exit the context manager first.")
        return self.record


@contextmanager
def profile_memory(clip_id: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Context manager to profile memory usage for a specific clip.
    
    Usage:
        with profile_memory("clip_001", {"resolution": "720p"}) as recorder:
            # ... processing code ...
            pass
        
        record = recorder.get_record()
        print(f"Peak memory: {record.peak_memory_mb:.2f} MB")
    
    Args:
        clip_id: Unique identifier for the clip.
        metadata: Optional dictionary of additional context.
        
    Yields:
        MemoryProfiler: The profiler instance.
    """
    profiler = MemoryProfiler(clip_id, metadata)
    with profiler:
        yield profiler


def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the process in MB.
    
    Returns:
        float: Current memory usage in MB, or 0.0 if measurement failed.
    """
    profiler = MemoryProfiler("temp")
    return profiler._get_current_memory_mb()


def format_memory_record(record: MemoryProfileRecord) -> str:
    """
    Format a memory profile record as a human-readable string.
    
    Args:
        record: The memory profile record.
        
    Returns:
        str: Formatted string representation.
    """
    return (
        f"Clip: {record.clip_id}\n"
        f"  Peak Memory: {record.peak_memory_mb:.2f} MB\n"
        f"  Duration: {record.duration_seconds:.2f} seconds\n"
        f"  Process ID: {record.process_id}\n"
        f"  Status: {record.notes}"
    )