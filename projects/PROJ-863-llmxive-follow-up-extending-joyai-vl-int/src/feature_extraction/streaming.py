"""
Streaming and batching utilities for feature extraction.

This module provides memory-safe processing of video streams and model
inference to ensure RAM usage stays below the 6GB limit (FR-001).

Key components:
- ChunkedFrameIterator: Yields frames in fixed-size batches to control memory.
- MemoryMonitor: Tracks peak and current memory usage.
- process_stream: Main entry point for streaming processing with backpressure.
"""

import gc
import os
import time
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Generator,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
)

import numpy as np
import psutil

# Constants
RAM_LIMIT_GB = 6.0
RAM_LIMIT_BYTES = RAM_LIMIT_GB * 1024**3
DEFAULT_CHUNK_SIZE = 16  # Frames per batch

T = TypeVar("T")

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

class MemoryMonitor:
    """
    Monitors process memory usage using psutil.
    
    Provides methods to check current usage, peak usage, and enforce limits.
    """

    def __init__(self, limit_gb: float = RAM_LIMIT_GB):
        self.limit_bytes = limit_gb * 1024**3
        self.process = psutil.Process(os.getpid())
        self._peak_usage: float = 0.0

    def get_current_usage(self) -> float:
        """Returns current memory usage in bytes."""
        return self.process.memory_info().rss

    def get_current_usage_gb(self) -> float:
        """Returns current memory usage in GB."""
        return self.get_current_usage() / (1024**3)

    def get_peak_usage(self) -> float:
        """Returns peak memory usage observed since initialization."""
        return self._peak_usage

    def update_peak(self) -> None:
        """Updates the peak usage if current usage is higher."""
        current = self.get_current_usage()
        if current > self._peak_usage:
            self._peak_usage = current

    def check_limit(self) -> bool:
        """
        Checks if current memory usage is within limits.
        
        Returns:
            True if within limit, False otherwise.
        """
        self.update_peak()
        return self.get_current_usage() <= self.limit_bytes

    def enforce_limit(self, raise_on_exceed: bool = True) -> bool:
        """
        Enforces memory limit, optionally raising an exception.
        
        Args:
            raise_on_exceed: If True, raises MemoryLimitExceed on violation.
        
        Returns:
            True if within limit, False otherwise.
        """
        if not self.check_limit():
            if raise_on_exceed:
                raise MemoryLimitExceeded(
                    f"Memory limit exceeded: {self.get_current_usage_gb():.2f}GB > "
                    f"{self.limit_bytes / (1024**3):.2f}GB limit. "
                    f"Peak: {self._peak_usage / (1024**3):.2f}GB"
                )
            return False
        return True

    def force_gc(self) -> None:
        """Forces garbage collection to reclaim memory."""
        gc.collect()

@contextmanager
def memory_guard(
    monitor: MemoryMonitor, chunk_size: int = DEFAULT_CHUNK_SIZE
) -> Generator[None, None, None]:
    """
    Context manager that ensures memory limits are respected during processing.
    
    Yields control to the block, then forces GC and checks limits on exit.
    """
    yield
    monitor.force_gc()
    monitor.enforce_limit()

class ChunkedFrameIterator:
    """
    Iterates over a video stream in chunks to control memory usage.
    
    Args:
        frame_generator: A generator that yields individual frames (numpy arrays).
        chunk_size: Number of frames per batch.
        monitor: Optional MemoryMonitor to enforce limits.
    """

    def __init__(
        self,
        frame_generator: Iterator[np.ndarray],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        monitor: Optional[MemoryMonitor] = None,
    ):
        self.frame_generator = frame_generator
        self.chunk_size = chunk_size
        self.monitor = monitor or MemoryMonitor()

    def __iter__(self) -> "ChunkedFrameIterator":
        return self

    def __next__(self) -> List[np.ndarray]:
        """
        Fetches the next chunk of frames.
        
        Returns:
            List of frames (numpy arrays) in the current chunk.
        
        Raises:
            StopIteration: When no more frames are available.
            MemoryLimitExceeded: If memory limit is breached after fetching.
        """
        chunk: List[np.ndarray] = []

        try:
            for _ in range(self.chunk_size):
                frame = next(self.frame_generator)
                chunk.append(frame)
        except StopIteration:
            if not chunk:
                raise
            return chunk

        # Check memory after fetching a chunk
        self.monitor.update_peak()
        if not self.monitor.check_limit():
            # Attempt to recover by forcing GC
            self.monitor.force_gc()
            if not self.monitor.check_limit():
                raise MemoryLimitExceeded(
                    f"Memory limit exceeded after fetching {len(chunk)} frames. "
                    f"Current: {self.monitor.get_current_usage_gb():.2f}GB"
                )

        return chunk

def process_stream(
    frame_generator: Iterator[np.ndarray],
    processor: Callable[[List[np.ndarray]], Any],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    monitor: Optional[MemoryMonitor] = None,
) -> Generator[Any, None, None]:
    """
    Processes a video stream in chunks with memory enforcement.
    
    Args:
        frame_generator: Generator yielding individual frames.
        processor: Function that takes a list of frames and returns processed data.
        chunk_size: Number of frames per batch.
        monitor: Optional MemoryMonitor instance.
        
    Yields:
        Results from the processor for each chunk.
        
    Raises:
        MemoryLimitExceeded: If memory usage exceeds the limit.
    """
    monitor = monitor or MemoryMonitor()
    iterator = ChunkedFrameIterator(frame_generator, chunk_size, monitor)

    for chunk in iterator:
        with memory_guard(monitor, chunk_size):
            result = processor(chunk)
            yield result
            # Explicitly delete chunk reference to aid GC
            del chunk
            gc.collect()

def create_batched_iterator(
    iterable: Iterator[T], batch_size: int
) -> Generator[List[T], None, None]:
    """
    Generic utility to batch any iterator into lists.
    
    Args:
        iterable: Input iterator.
        batch_size: Number of items per batch.
        
    Yields:
        Lists of items.
    """
    batch: List[T] = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

# Helper for debugging memory usage
def log_memory_snapshot(tag: str = "Snapshot") -> None:
    """Logs current memory usage to stdout for debugging."""
    monitor = MemoryMonitor()
    print(
        f"[Memory {tag}] Current: {monitor.get_current_usage_gb():.3f}GB, "
        f"Peak: {monitor.get_peak_usage() / (1024**3):.3f}GB, "
        f"Limit: {monitor.limit_bytes / (1024**3):.3f}GB"
    )
