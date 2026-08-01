"""
Resource enforcement utilities for the llmXive pipeline.

This module provides logic to detect dataset size and apply sampling/capping
if the dataset exceeds available memory thresholds (default 7GB).
It logs enforcement actions to a JSON file in the results directory.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Any, Dict

import datasets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAM_THRESHOLD_BYTES = 7 * 1024 * 1024 * 1024  # 7 GB
MAX_SAMPLES = 500_000
RESULTS_DIR = Path("results")
RESOURCE_LOG_PATH = RESULTS_DIR / "resource_log.json"


def ensure_results_dir() -> None:
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_resource_log() -> Dict[str, Any]:
    """Load existing resource log or return a new empty structure."""
    ensure_results_dir()
    if RESOURCE_LOG_PATH.exists():
        try:
            with open(RESOURCE_LOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load existing resource log: {e}. Starting fresh.")
    return {
        "enforcement_actions": [],
        "dataset_info": {}
    }


def save_resource_log(log_data: Dict[str, Any]) -> None:
    """Save the resource log to disk."""
    ensure_results_dir()
    with open(RESOURCE_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, default=str)


def estimate_dataset_size(dataset: datasets.Dataset) -> int:
    """
    Estimate the size of a HuggingFace dataset in bytes.

    This uses the dataset's _fingerprint and info to estimate memory usage.
    For streaming datasets, we estimate based on the number of features
    and a rough row size estimate if explicit size info isn't available.

    Args:
        dataset: The HuggingFace Dataset object.

    Returns:
        Estimated size in bytes.
    """
    if hasattr(dataset, "_info") and dataset._info:
        info = dataset._info
        if hasattr(info, "dataset_size") and info.dataset_size:
            return info.dataset_size

    # Fallback estimation:
    # Count rows and estimate bytes per row based on features
    # This is a rough heuristic for streaming datasets where size is unknown
    try:
        num_rows = len(dataset)
        # Estimate ~1KB per row as a conservative average for text-heavy datasets
        # This is very rough; real size depends on content
        avg_row_size = 1024
        return num_rows * avg_row_size
    except Exception:
        # If we can't count rows (streaming), return 0 to indicate unknown
        return 0


def enforce_resource_limits(
    dataset: datasets.Dataset,
    dataset_name: str = "unknown"
) -> datasets.Dataset:
    """
    Enforce resource limits on a dataset.

    If the dataset size exceeds RAM_THRESHOLD_BYTES (7GB), it will be sampled
    to MAX_SAMPLES (500k items). The action is logged to results/resource_log.json.

    Args:
        dataset: The HuggingFace Dataset object to check/enforce.
        dataset_name: Name of the dataset for logging purposes.

    Returns:
        The original dataset (if under limit) or a sampled version (if over limit).
    """
    log_data = load_resource_log()

    size_bytes = estimate_dataset_size(dataset)
    size_gb = size_bytes / (1024**3)

    log_entry = {
        "dataset_name": dataset_name,
        "estimated_size_gb": round(size_gb, 2),
        "threshold_gb": 7.0,
        "action_taken": "none",
        "samples_before": len(dataset) if hasattr(dataset, "__len__") else "unknown",
        "samples_after": len(dataset) if hasattr(dataset, "__len__") else "unknown"
    }

    logger.info(f"Dataset '{dataset_name}' estimated size: {size_gb:.2f} GB")

    if size_bytes > RAM_THRESHOLD_BYTES:
        logger.warning(
            f"Dataset '{dataset_name}' exceeds 7GB threshold ({size_gb:.2f} GB). "
            f"Applying sampling to {MAX_SAMPLES} items."
        )

        # Sample the dataset
        # For streaming datasets, we need to convert to a list first or use select
        # with a specific set of indices. We'll use a simple approach:
        # If it's a streaming dataset, we'll collect the first MAX_SAMPLES rows
        # and create a new dataset from them.

        if hasattr(dataset, "streaming") and dataset.streaming:
            # For streaming, we need to materialize a sample
            logger.info("Dataset is streaming, materializing sample...")
            sampled_data = []
            count = 0
            for item in dataset:
                if count >= MAX_SAMPLES:
                    break
                sampled_data.append(item)
                count += 1

            # Create new dataset from sample
            dataset = datasets.Dataset.from_list(sampled_data)
            log_entry["action_taken"] = "sampling"
            log_entry["samples_before"] = "streaming_unknown"
            log_entry["samples_after"] = len(sampled_data)
        else:
            # For non-streaming, we can use select with random sampling
            if len(dataset) > MAX_SAMPLES:
                indices = dataset.shuffle(seed=42).select(range(MAX_SAMPLES))
                dataset = dataset.select(indices)
                log_entry["action_taken"] = "sampling"
                log_entry["samples_after"] = MAX_SAMPLES

        logger.info(f"Sampling applied: {MAX_SAMPLES} items selected")
    else:
        logger.info(f"Dataset '{dataset_name}' is within limits. No sampling applied.")
        log_entry["action_taken"] = "none"

    log_data["enforcement_actions"].append(log_entry)
    log_data["dataset_info"][dataset_name] = {
        "size_gb": round(size_gb, 2),
        "threshold_gb": 7.0,
        "limit_applied": log_entry["action_taken"] == "sampling"
    }

    save_resource_log(log_data)
    logger.info(f"Resource enforcement log saved to {RESOURCE_LOG_PATH}")

    return dataset

def get_resource_summary() -> Dict[str, Any]:
    """
    Get a summary of all resource enforcement actions taken.

    Returns:
        Dictionary containing enforcement actions and dataset info.
    """
    return load_resource_log()
