"""
Performance optimization module for memory-efficient streaming.
"""

from .streaming_optimizer import (
    MemoryMonitor,
    StreamingAggregator,
    stream_jsonl_file,
    process_posts_streaming,
    validate_streaming_output,
    benchmark_streaming_performance,
    main,
    DEFAULT_CHUNK_SIZE,
    MAX_MEMORY_MB,
    BATCH_SIZE
)

__all__ = [
    "MemoryMonitor",
    "StreamingAggregator",
    "stream_jsonl_file",
    "process_posts_streaming",
    "validate_streaming_output",
    "benchmark_streaming_performance",
    "main",
    "DEFAULT_CHUNK_SIZE",
    "MAX_MEMORY_MB",
    "BATCH_SIZE"
]
