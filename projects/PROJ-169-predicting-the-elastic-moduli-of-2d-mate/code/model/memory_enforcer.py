"""Memory enforcement module for training with dynamic batch size reduction.

Implements SC-004: Enforce memory limit during training by dynamically reducing
batch size if peak memory exceeds 7GB.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tracemalloc
from typing import Any, Callable, Dict, Optional, Tuple

import torch
from torch_geometric.data import Data

from utils.config import get_config

# Constants
MAX_MEMORY_GB = 7.0
INITIAL_BATCH_SIZE = 64
MIN_BATCH_SIZE = 1
MEMORY_LOG_PATH = "data/results/training_logs.json"

logger = logging.getLogger(__name__)


def get_memory_peak_mb() -> float:
    """Get the peak memory usage in MB using tracemalloc.

    Returns:
        Peak memory usage in MB.
    """
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)


def enforce_memory_limit(
    batch_size: int,
    train_func: Callable[[int], Tuple[float, float]],
    max_iterations: int = 1000
) -> Tuple[bool, float, int]:
    """Enforce memory limit by dynamically reducing batch size.

    Algorithm:
    1. Start with batch_size (default 64).
    2. Run one epoch with current batch_size.
    3. Measure peak memory.
    4. If peak memory > 7GB:
       - Halve batch_size.
       - If batch_size < 1, fail.
       - Retry epoch with new batch_size.
    5. If batch_size == 1 and memory > 7GB, exit with code 1.

    Args:
        batch_size: Starting batch size.
        train_func: Function that takes batch_size and returns (loss, accuracy).
        max_iterations: Maximum number of iterations to run.

    Returns:
        Tuple of (success, memory_peak_mb, final_batch_size).
        success: True if training completed within memory limits, False otherwise.
        memory_peak_mb: Peak memory usage in MB.
        final_batch_size: The batch size used for the successful epoch.

    Raises:
        SystemExit: If memory limit is exceeded even with batch_size=1.
    """
    config = get_config()
    current_batch_size = batch_size
    memory_peak_mb = 0.0
    iteration = 0

    while current_batch_size >= MIN_BATCH_SIZE and iteration < max_iterations:
        # Reset tracemalloc for each epoch attempt
        tracemalloc.stop()
        tracemalloc.start()

        logger.info(f"Attempting epoch with batch_size={current_batch_size}")

        try:
            # Run one epoch with current batch size
            loss, accuracy = train_func(current_batch_size)

            # Measure peak memory for this epoch
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            memory_peak_mb = peak_mem / (1024 * 1024)

            logger.info(f"Epoch completed. Loss: {loss:.4f}, Accuracy: {accuracy:.4f}")
            logger.info(f"Peak memory: {memory_peak_mb:.2f} MB ({memory_peak_mb / 1024:.2f} GB)")

            # Check if memory exceeds limit
            if memory_peak_mb > MAX_MEMORY_GB * 1024:
                logger.warning(
                    f"Peak memory ({memory_peak_mb:.2f} MB) exceeds limit "
                    f"({MAX_MEMORY_GB * 1024} MB). Reducing batch size."
                )

                # Clean up to free memory before retry
                gc.collect()
                torch.cuda.empty_cache() if torch.cuda.is_available() else None

                # Halve batch size
                current_batch_size = max(MIN_BATCH_SIZE, current_batch_size // 2)

                if current_batch_size == MIN_BATCH_SIZE:
                    logger.error(
                        f"SC-004 Failed: Memory limit exceeded even with batch size 1. "
                        f"Peak memory: {memory_peak_mb:.2f} MB"
                    )
                    sys.exit(1)

                iteration += 1
                continue

            # If we get here, memory was within limits
            return True, memory_peak_mb, current_batch_size

        except MemoryError as e:
            logger.warning(
                f"MemoryError caught with batch_size={current_batch_size}: {e}. "
                "Reducing batch size."
            )
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None

            current_batch_size = max(MIN_BATCH_SIZE, current_batch_size // 2)

            if current_batch_size == MIN_BATCH_SIZE:
                logger.error(
                    f"SC-004 Failed: Memory limit exceeded even with batch size 1. "
                    f"MemoryError occurred."
                )
                sys.exit(1)

            iteration += 1
            continue

    # Should not reach here if logic is correct, but handle edge case
    logger.error(
        f"SC-004 Failed: Maximum iterations ({max_iterations}) reached without "
        f"successful epoch. Final batch size: {current_batch_size}"
    )
    sys.exit(1)


def run_training_with_memory_enforcement(
    train_epoch_func: Callable[[int], Tuple[float, float]],
    initial_batch_size: int = INITIAL_BATCH_SIZE,
    epochs: int = 10,
    log_path: str = MEMORY_LOG_PATH
) -> Dict[str, Any]:
    """Run training with memory enforcement and logging.

    Args:
        train_epoch_func: Function that takes batch_size and returns (loss, accuracy).
        initial_batch_size: Starting batch size.
        epochs: Number of epochs to train.
        log_path: Path to write training logs.

    Returns:
        Dictionary containing training results and memory statistics.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger.info(f"Starting training with memory enforcement. Initial batch size: {initial_batch_size}")

    # Track results across epochs
    epoch_results = []
    memory_peaks = []
    batch_sizes_used = []

    for epoch in range(epochs):
        logger.info(f"--- Epoch {epoch + 1}/{epochs} ---")

        # Use memory enforcement for this epoch
        success, peak_mb, final_bs = enforce_memory_limit(
            batch_size=initial_batch_size if epoch == 0 else batch_sizes_used[-1],
            train_func=train_epoch_func
        )

        if not success:
            # This should not happen if enforce_memory_limit raises on failure
            logger.error(f"Training failed at epoch {epoch + 1}")
            break

        # Record results
        loss, accuracy = train_epoch_func(final_bs)
        epoch_results.append({
            "epoch": epoch + 1,
            "loss": loss,
            "accuracy": accuracy,
            "batch_size": final_bs
        })
        memory_peaks.append(peak_mb)
        batch_sizes_used.append(final_bs)

        logger.info(f"Epoch {epoch + 1} completed with batch_size={final_bs}, "
                    f"peak_memory={peak_mb:.2f} MB")

    # Prepare final log entry
    final_log = {
        "initial_batch_size": initial_batch_size,
        "epochs_completed": len(epoch_results),
        "final_batch_size": batch_sizes_used[-1] if batch_sizes_used else initial_batch_size,
        "memory_peak_mb": max(memory_peaks) if memory_peaks else 0.0,
        "memory_limit_gb": MAX_MEMORY_GB,
        "sc004_status": "PASSED",
        "epoch_details": epoch_results
    }

    # Write log to file
    with open(log_path, "w") as f:
        json.dump(final_log, f, indent=2)

    logger.info(f"Training logs written to {log_path}")
    logger.info(f"Final batch size: {final_log['final_batch_size']}, "
                f"Peak memory: {final_log['memory_peak_mb']:.2f} MB")

    return final_log


def main() -> None:
    """Main entry point for memory enforcement testing.

    This function demonstrates the memory enforcement mechanism by running
    a dummy training loop with synthetic data.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Dummy training function for demonstration
    def dummy_train_epoch(batch_size: int) -> Tuple[float, float]:
        """Dummy training function that simulates memory usage.

        Args:
            batch_size: Batch size for the epoch.

        Returns:
            Tuple of (loss, accuracy).
        """
        # Simulate some computation
        import time
        time.sleep(0.1)

        # Simulate memory usage based on batch size
        # In real scenario, this would be actual model training
        _ = torch.randn(1000 * batch_size, 64)  # Simulate data

        return 0.5, 0.8  # Dummy loss and accuracy

    # Run memory enforcement
    try:
        result = run_training_with_memory_enforcement(
            train_epoch_func=dummy_train_epoch,
            initial_batch_size=INITIAL_BATCH_SIZE,
            epochs=3,
            log_path=MEMORY_LOG_PATH
        )
        print(f"Training completed successfully. Result: {result}")
    except SystemExit as e:
        print(f"Training failed with exit code: {e.code}")
        raise


if __name__ == "__main__":
    main()