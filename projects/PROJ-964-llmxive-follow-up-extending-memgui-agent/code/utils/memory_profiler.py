"""
Memory profiling and logging utilities for llmXive agents.

This module provides functionality to track peak memory footprint and
inference latency, logging these metrics to a JSON file for analysis.
"""
import json
import os
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, Optional, Callable, TypeVar
from contextlib import contextmanager

# Ensure the data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Ensure the synthetic_benchmark subdirectory exists
BENCHMARK_DIR = DATA_DIR / "synthetic_benchmark"
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

# Output file path as specified in T006
LOG_FILE = BENCHMARK_DIR / "memory_profile.json"

T = TypeVar('T')

def _load_existing_logs() -> list:
    """Load existing logs from the JSON file if it exists."""
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                # Handle JSONL format (one JSON object per line)
                if '\n' in content:
                    return [json.loads(line) for line in content.splitlines() if line.strip()]
                else:
                    # Single JSON object
                    return [json.loads(content)]
        except (json.JSONDecodeError, IOError):
            return []
    return []

def _append_log(entry: Dict[str, Any]) -> None:
    """Append a log entry to the JSONL file."""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def log_metrics(
    peak_memory_mb: float,
    latency_ms: float,
    agent_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log memory and latency metrics to data/synthetic_benchmark/memory_profile.json.

    Args:
        peak_memory_mb: Peak memory usage in megabytes.
        latency_ms: Inference latency in milliseconds.
        agent_type: Type/name of the agent being profiled.
        metadata: Optional additional metadata to include in the log entry.
    """
    entry = {
        "peak_memory_mb": round(peak_memory_mb, 2),
        "latency_ms": round(latency_ms, 2),
        "agent_type": agent_type,
        "timestamp": time.time()
    }
    if metadata:
        entry.update(metadata)
    
    _append_log(entry)

@contextmanager
def profile_memory_latency(
    agent_type: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Context manager to profile memory and latency for a code block.

    Usage:
        with profile_memory_latency("baseline_agent", {"step": 5}) as results:
            # ... run inference ...
        # results contains peak_memory_mb and latency_ms

    Args:
        agent_type: Type/name of the agent being profiled.
        metadata: Optional additional metadata to include in the log entry.

    Yields:
        dict: Contains 'peak_memory_mb' and 'latency_ms' after the block executes.
    """
    tracemalloc.start()
    start_time = time.perf_counter()
    
    try:
        yield {"peak_memory_mb": 0.0, "latency_ms": 0.0}
    finally:
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_memory_mb = peak / (1024 * 1024)
        latency_ms = (end_time - start_time) * 1000
        
        entry = {
            "peak_memory_mb": round(peak_memory_mb, 2),
            "latency_ms": round(latency_ms, 2),
            "agent_type": agent_type,
            "timestamp": time.time()
        }
        if metadata:
            entry.update(metadata)
        
        _append_log(entry)

def get_current_memory_usage() -> float:
    """
    Get current memory usage in megabytes.

    Returns:
        float: Current memory usage in MB.
    """
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_usage() -> float:
    """
    Get peak memory usage since tracemalloc started in megabytes.

    Returns:
        float: Peak memory usage in MB.
    """
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def clear_logs() -> None:
    """Clear all existing memory profile logs."""
    if LOG_FILE.exists():
        LOG_FILE.unlink()

def read_logs() -> list:
    """
    Read all memory profile logs.

    Returns:
        list: List of log entries (dictionaries).
    """
    return _load_existing_logs()