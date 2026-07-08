"""
Memory management utilities for the Structure-Only Surrogate Model pipeline.

Implements dynamic sampling strategies and data volume verification to guarantee
the 7GB RAM limit (FR-007/SC-004).
"""

import os
import sys
import gc
from typing import List, Optional, Tuple, Callable, Any
from pathlib import Path

import numpy as np

# Import existing project utilities
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
MAX_RAM_GB = 7.0
MAX_RAM_BYTES = MAX_RAM_GB * 1024**3
SAFETY_FACTOR = 0.85  # Use only 85% of available RAM for safety
MAX_SAFE_BYTES = int(MAX_RAM_BYTES * SAFETY_FACTOR)

# Estimated memory overhead per MaterialGraph object (approximate)
# Based on typical node/edge counts in 2D materials graphs
GRAPH_OVERHEAD_BYTES = 1024  # Base object overhead
NODE_BYTES = 128  # Per node features
EDGE_BYTES = 64   # Per edge features
TARGET_BYTES = 24 # Per target value (3 elastic moduli)


def get_available_memory_gb() -> float:
    """
    Returns the estimated available memory in GB.

    On Linux/macOS, reads from /proc/meminfo or uses psutil if available.
    Falls back to a conservative estimate if detection fails.

    Returns:
        float: Available memory in GB
    """
    try:
        if sys.platform.startswith('linux'):
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemAvailable:'):
                        # Format: "MemAvailable:    12345678 kB"
                        parts = line.split()
                        if len(parts) >= 2:
                            kb = int(parts[1])
                            return kb / (1024 * 1024)
        elif sys.platform == 'darwin':
            import subprocess
            result = subprocess.run(
                ['sysctl', '-n', 'hw.memsize'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                total_bytes = int(result.stdout.strip())
                # Assume ~50% available on macOS for safety
                return (total_bytes * 0.5) / (1024**3)
        elif sys.platform == 'win32':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_mem = ctypes.c_ulonglong(0)
            if kernel32.GlobalMemoryStatusEx(ctypes.byref(c_mem)):
                total = c_mem.value
                # Assume ~50% available on Windows for safety
                return (total * 0.5) / (1024**3)
    except Exception as e:
        logger.warning(f"Could not detect available memory: {e}. Using conservative estimate.")

    # Conservative fallback: assume 4GB available
    return 4.0


def estimate_graph_memory(graph: Any) -> int:
    """
    Estimates the memory footprint of a MaterialGraph object in bytes.

    Args:
        graph: A MaterialGraph instance or similar object

    Returns:
        int: Estimated memory usage in bytes
    """
    if graph is None:
        return 0

    try:
        # Attempt to get node/edge counts if available
        num_nodes = len(graph.nodes) if hasattr(graph, 'nodes') else 0
        num_edges = len(graph.edges) if hasattr(graph, 'edges') else 0
        num_targets = len(graph.targets) if hasattr(graph, 'targets') else 0

        estimated = (
            GRAPH_OVERHEAD_BYTES +
            (num_nodes * NODE_BYTES) +
            (num_edges * EDGE_BYTES) +
            (num_targets * TARGET_BYTES)
        )

        # Add numpy array overhead if present
        if hasattr(graph, 'node_features') and graph.node_features is not None:
            estimated += graph.node_features.nbytes
        if hasattr(graph, 'edge_features') and graph.edge_features is not None:
            estimated += graph.edge_features.nbytes

        return estimated
    except Exception as e:
        logger.warning(f"Could not estimate graph memory: {e}. Using default estimate.")
        return GRAPH_OVERHEAD_BYTES + (100 * NODE_BYTES) + (500 * EDGE_BYTES)


def calculate_max_safe_sample_size(
    total_count: int,
    sample_graph: Optional[Any] = None
) -> int:
    """
    Calculates the maximum number of samples that can safely fit in memory.

    Args:
        total_count: Total number of available samples
        sample_graph: Optional sample graph to use for memory estimation.
                     If None, uses a default estimate.

    Returns:
        int: Maximum safe number of samples to load
    """
    available_bytes = int(get_available_memory_gb() * 1024**3 * SAFETY_FACTOR)

    # Reserve memory for other operations (config, logging, etc.)
    reserved_bytes = 500 * 1024 * 1024  # 500 MB
    usable_bytes = max(0, available_bytes - reserved_bytes)

    if sample_graph is not None:
        per_sample_bytes = estimate_graph_memory(sample_graph)
    else:
        # Default estimate for a typical 2D material graph
        per_sample_bytes = GRAPH_OVERHEAD_BYTES + (50 * NODE_BYTES) + (200 * EDGE_BYTES)

    if per_sample_bytes <= 0:
        per_sample_bytes = 1

    max_samples = int(usable_bytes / per_sample_bytes)
    return min(max_samples, total_count)


def dynamic_sampling(
    data_source: Callable[[], List[Any]],
    target_count: Optional[int] = None,
    sample_graph: Optional[Any] = None
) -> Tuple[List[Any], int]:
    """
    Implements dynamic sampling to respect memory constraints.

    This function:
    1. Estimates available memory
    2. Calculates a safe sample size
    3. Returns a subset of data that fits within the 7GB limit

    Args:
        data_source: A callable that returns the full dataset (lazy evaluation preferred)
        target_count: Optional target number of samples (if None, uses max safe size)
        sample_graph: Optional sample for memory estimation

    Returns:
        Tuple of (sampled_data_list, actual_count)
    """
    logger.info("Starting dynamic sampling with 7GB RAM constraint")

    # Get full dataset or estimate size
    try:
        full_data = data_source()
        total_count = len(full_data)
    except Exception as e:
        logger.error(f"Failed to load data source: {e}")
        return [], 0

    if total_count == 0:
        logger.warning("No data available from source")
        return [], 0

    # Calculate safe sample size
    if target_count is None:
        max_safe = calculate_max_safe_sample_size(total_count, sample_graph)
        target_count = max_safe
    else:
        max_safe = calculate_max_safe_sample_size(total_count, sample_graph)
        if target_count > max_safe:
            logger.warning(
                f"Requested {target_count} samples exceeds safe limit of {max_safe}. "
                f"Reducing to safe limit."
            )
            target_count = max_safe

    # Select samples (randomly if possible, otherwise sequentially)
    if target_count >= total_count:
        sampled = full_data
    else:
        # Random sampling if we have enough data
        indices = np.random.choice(total_count, target_count, replace=False)
        sampled = [full_data[i] for i in indices]

    # Verify memory usage
    total_estimated = sum(estimate_graph_memory(g) for g in sampled)
    logger.info(
        f"Dynamic sampling complete: {len(sampled)} samples selected. "
        f"Estimated memory: {total_estimated / (1024**2):.2f} MB"
    )

    return sampled, len(sampled)


def verify_data_volume(
    data_path: Path,
    file_format: str = "parquet",
    max_rows: Optional[int] = None
) -> bool:
    """
    Verifies that a dataset file does not exceed memory constraints.

    Args:
        data_path: Path to the data file
        file_format: Format of the file ('parquet', 'csv', 'json')
        max_rows: Optional maximum number of rows to check

    Returns:
        bool: True if the file is safe to load, False otherwise
    """
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return False

    try:
        if file_format.lower() == 'parquet':
            import pandas as pd
            # Read metadata only to estimate size
            # Parquet files store row counts in metadata
            df_sample = pd.read_parquet(data_path, columns=[])
            total_rows = len(pd.read_parquet(data_path, columns=['__dummy__']).head(1))
            # Re-read to get actual count without loading all data
            # Use pandas' parquet engine metadata if available
            try:
                import pyarrow.parquet as pq
                parquet_file = pq.ParquetFile(data_path)
                total_rows = parquet_file.metadata.num_rows
            except Exception:
                # Fallback: estimate from file size
                file_size_bytes = data_path.stat().st_size
                avg_row_bytes = 1024  # Conservative estimate
                total_rows = file_size_bytes // avg_row_bytes

        elif file_format.lower() == 'csv':
            import pandas as pd
            # Count lines quickly
            with open(data_path, 'r') as f:
                total_rows = sum(1 for _ in f) - 1  # Subtract header
        elif file_format.lower() == 'json':
            import json
            with open(data_path, 'r') as f:
                data = json.load(f)
                total_rows = len(data) if isinstance(data, list) else 1
        else:
            logger.warning(f"Unsupported format for volume check: {file_format}")
            return False

        if max_rows is not None and total_rows > max_rows:
            logger.warning(
                f"Data volume check failed: {total_rows} rows exceeds max {max_rows}"
            )
            return False

        # Check against memory limit
        max_safe = calculate_max_safe_sample_size(total_rows)
        if total_rows > max_safe:
            logger.warning(
                f"Data volume check failed: {total_rows} rows exceeds safe limit of {max_safe}"
            )
            return False

        logger.info(
            f"Data volume check passed: {total_rows} rows within safe limit of {max_safe}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to verify data volume: {e}")
        return False


def enforce_memory_limit(
    data_loader: Callable[[], List[Any]],
    batch_size: int = 1000
) -> List[Any]:
    """
    Loads data in batches while enforcing memory limits.

    Args:
        data_loader: Callable that returns data (can be lazy)
        batch_size: Number of items to load per batch

    Returns:
        List of all loaded data within memory limits
    """
    all_data = []
    available = get_available_memory_gb()

    logger.info(f"Enforcing memory limit with {available:.2f} GB available")

    try:
        full_data = data_loader()
    except Exception as e:
        logger.error(f"Data loader failed: {e}")
        return []

    if not full_data:
        return []

    total_count = len(full_data)
    max_safe = calculate_max_safe_sample_size(total_count)

    if total_count <= max_safe:
        logger.info(f"Full dataset ({total_count} items) fits in memory")
        return full_data

    # Load in batches until limit reached
    loaded_count = 0
    for i in range(0, total_count, batch_size):
        batch = full_data[i:i+batch_size]
        batch_size_actual = len(batch)

        # Estimate memory before adding
        current_estimated = sum(estimate_graph_memory(g) for g in all_data)
        batch_estimated = sum(estimate_graph_memory(g) for g in batch)

        if current_estimated + batch_estimated > MAX_SAFE_BYTES:
            logger.warning(
                f"Stopping at {loaded_count} items to respect memory limit. "
                f"Next batch would exceed limit."
            )
            break

        all_data.extend(batch)
        loaded_count += batch_size_actual

        # Periodic garbage collection
        if loaded_count % (batch_size * 10) == 0:
            gc.collect()

    logger.info(
        f"Memory-enforced loading complete: {loaded_count}/{total_count} items loaded"
    )
    return all_data


def get_memory_profile() -> dict:
    """
    Returns a snapshot of current memory usage.

    Returns:
        dict: Memory statistics including total, available, and used
    """
    available_gb = get_available_memory_gb()
    used_gb = MAX_RAM_GB - available_gb

    return {
        "total_gb": MAX_RAM_GB,
        "available_gb": round(available_gb, 2),
        "used_gb": round(used_gb, 2),
        "safety_limit_gb": round(MAX_RAM_GB * SAFETY_FACTOR, 2),
        "usage_percent": round((used_gb / MAX_RAM_GB) * 100, 1)
    }