"""Memory enforcement and monitoring for GNN training.

Implements dynamic batch size reduction to enforce SC-004 (MAX_MEMORY_GB = 7.0).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tracemalloc
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import torch

from utils.config import get_config

logger = logging.getLogger(__name__)

# Constants derived from T004
MAX_MEMORY_GB = 7.0
INITIAL_BATCH_SIZE = 64
MIN_BATCH_SIZE = 1

def get_memory_peak_mb() -> float:
    """Return peak memory usage in MB using tracemalloc."""
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def enforce_memory_limit(
    epoch_func: callable,
    initial_batch_size: int = INITIAL_BATCH_SIZE,
    min_batch_size: int = MIN_BATCH_SIZE,
    max_memory_gb: float = MAX_MEMORY_GB,
    output_log_path: Optional[str] = None,
) -> Tuple[int, float, Dict[str, Any]]:
    """Execute an epoch function with dynamic batch size reduction.

    Algorithm:
    1. Start with `initial_batch_size`.
    2. Start tracemalloc.
    3. Run `epoch_func(batch_size)`.
    4. Measure peak memory.
    5. If peak > max_memory_gb:
       - Stop tracemalloc.
       - Halve batch size.
       - If batch_size < min_batch_size, raise SystemExit with SC-004 failure message.
       - Restart tracemalloc and retry.
    6. If successful, return (final_batch_size, memory_peak_gb, log_entry).

    Args:
        epoch_func: A callable that accepts `batch_size` as its first argument.
        initial_batch_size: Starting batch size (default 64).
        min_batch_size: Minimum allowed batch size (default 1).
        max_memory_gb: Memory limit in GB (default 7.0).
        output_log_path: Path to write training_logs.json.

    Returns:
        Tuple of (final_batch_size, memory_peak_gb, log_entry_dict).

    Raises:
        SystemExit: If memory limit is exceeded even at min_batch_size.
    """
    batch_size = initial_batch_size
    max_memory_mb = max_memory_gb * 1024
    log_entry: Dict[str, Any] = {
        "initial_batch_size": initial_batch_size,
        "reduction_steps": 0,
        "final_batch_size": initial_batch_size,
        "memory_peak_gb": 0.0,
        "status": "success",
    }

    while True:
        tracemalloc.start()
        try:
            # Run the epoch function
            epoch_func(batch_size)
        except Exception as e:
            tracemalloc.stop()
            logger.error(f"Epoch failed with batch_size={batch_size}: {e}")
            raise

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / (1024 * 1024)
        peak_gb = peak_mb / 1024.0

        logger.info(f"Epoch with batch_size={batch_size}: peak memory = {peak_gb:.2f} GB")

        if peak_mb <= max_memory_mb:
            # Success
            log_entry["final_batch_size"] = batch_size
            log_entry["memory_peak_gb"] = round(peak_gb, 4)
            log_entry["status"] = "success"
            log_entry["reduction_steps"] = initial_batch_size // batch_size - 1 if batch_size < initial_batch_size else 0

            if output_log_path:
                _write_log(output_log_path, log_entry)

            return batch_size, peak_gb, log_entry

        # Memory exceeded: reduce batch size
        logger.warning(f"Memory limit exceeded ({peak_gb:.2f} GB > {max_memory_gb} GB). Reducing batch size.")
        batch_size = max(min_batch_size, batch_size // 2)
        log_entry["reduction_steps"] = initial_batch_size // batch_size - 1

        if batch_size < min_batch_size:
            error_msg = f"SC-004 Failed: Memory limit exceeded even with batch size {min_batch_size}"
            logger.error(error_msg)
            log_entry["status"] = "failed"
            log_entry["final_batch_size"] = min_batch_size
            log_entry["memory_peak_gb"] = round(peak_gb, 4)
            log_entry["error"] = error_msg

            if output_log_path:
                _write_log(output_log_path, log_entry)

            raise SystemExit(1)

def _write_log(path: str, log_entry: Dict[str, Any]) -> None:
    """Append or write log entry to JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    data = []
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    if not isinstance(data, list):
                        data = [data]
        except (json.JSONDecodeError, IOError):
            data = []

    data.append(log_entry)

    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_training_with_memory_enforcement(
    train_epoch_func: callable,
    epochs: int,
    initial_batch_size: int = INITIAL_BATCH_SIZE,
    min_batch_size: int = MIN_BATCH_SIZE,
    max_memory_gb: float = MAX_MEMORY_GB,
    output_log_path: Optional[str] = None,
) -> Tuple[int, float, Dict[str, Any]]:
    """Wrapper to run training epochs with memory enforcement.

    This wraps the epoch function to enforce memory limits per epoch.
    If an epoch fails due to memory, it reduces batch size and retries.

    Args:
        train_epoch_func: Function that runs one epoch, accepting batch_size.
        epochs: Number of epochs to run (not used directly, but for logging).
        initial_batch_size: Starting batch size.
        min_batch_size: Minimum allowed batch size.
        max_memory_gb: Memory limit in GB.
        output_log_path: Path to write training_logs.json.

    Returns:
        Tuple of (final_batch_size, memory_peak_gb, log_entry).
    """
    def epoch_wrapper(batch_size: int) -> None:
        train_epoch_func(batch_size)

    return enforce_memory_limit(
        epoch_func=epoch_wrapper,
        initial_batch_size=initial_batch_size,
        min_batch_size=min_batch_size,
        max_memory_gb=max_memory_gb,
        output_log_path=output_log_path,
    )

def main() -> None:
    """CLI entry point for memory enforcement testing (if needed)."""
    parser = argparse.ArgumentParser(description="Memory enforcement test.")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs to simulate.")
    parser.add_argument("--output-log", type=str, default="data/results/training_logs.json", help="Output log path.")
    args = parser.parse_args()

    def dummy_epoch(batch_size: int) -> None:
        """Simulate an epoch that consumes memory proportional to batch size."""
        # Allocate dummy tensors to simulate memory usage
        # This is just for testing the enforcement logic
        size = batch_size * 1000000  # 1M elements per batch
        dummy = torch.randn(size)
        _ = dummy.sum()
        del dummy
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        gc.collect()

    import argparse
    import gc

    try:
        final_bs, peak_gb, log = run_training_with_memory_enforcement(
            dummy_epoch,
            epochs=args.epochs,
            output_log_path=args.output_log,
        )
        print(f"Memory enforcement successful. Final batch size: {final_bs}, Peak: {peak_gb:.2f} GB")
    except SystemExit as e:
        print(f"Memory enforcement failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
