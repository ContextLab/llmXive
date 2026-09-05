"""
Data loading and preprocessing for MolmoMotion dataset.
Handles streaming, subsampling, and validation of dataset instances.
"""
import os
import sys
import time
import json
import random
import resource
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

from src.config import get_config, Config
from src.logging_config import get_logger, log_memory_usage, log_latency

logger = get_logger(__name__)


def load_molmomotion_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load MolmoMotion dataset in streaming mode to avoid OOM.
    Fetches from verified URL and implements retry logic.
    """
    config = get_config()
    dataset_name = config.get('dataset_name', 'mlabonne/molmomotion-1m')
    max_retries = 3
    attempt = 0

    while attempt < max_retries:
        try:
            logger.info(f"Attempting to load dataset (attempt {attempt + 1}/{max_retries})")
            dataset = load_dataset(
                dataset_name,
                split="train",
                streaming=True,
                trust_remote_code=True
            )
            logger.info("Dataset loaded successfully in streaming mode")
            return iter(dataset)
        except Exception as e:
            attempt += 1
            logger.warning(f"Failed to load dataset: {e}. Retrying...")
            if attempt >= max_retries:
                logger.error("Download failed after 3 retries")
                sys.exit(1)
            time.sleep(2 ** attempt)  # Exponential backoff

    raise RuntimeError("Dataset loading failed after all retries")


def subsample_instances(target_memory_gb: float = 7.0, random_seed: int = 42) -> List[Dict[str, Any]]:
    """
    Subsample instances from the streaming dataset using reservoir sampling
    to meet memory constraints while maintaining statistical representativeness.

    Args:
        target_memory_gb: Target memory usage in GB (default 7.0)
        random_seed: Random seed for reproducibility

    Returns:
        List of subsampled instances
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    # Estimate memory per instance (approximate based on typical MolmoMotion structure)
    # Each instance has: instance_id, ground_truth_points (list of 3D points),
    # kinematic_metadata, instruction_nl, instruction_struct
    # Rough estimate: ~50KB per instance average
    bytes_per_instance = 50 * 1024
    target_bytes = target_memory_gb * 1024 ** 3
    max_instances = int(target_bytes / bytes_per_instance)

    logger.info(f"Target memory: {target_memory_gb}GB, Max instances: {max_instances}")

    dataset_iter = load_molmomotion_streaming()
    reservoir = []

    for i, instance in enumerate(dataset_iter):
        if len(reservoir) < max_instances:
            reservoir.append(instance)
        else:
            # Reservoir sampling: replace with probability max_instances / (i + 1)
            j = random.randint(0, i)
            if j < max_instances:
                reservoir[j] = instance

        if (i + 1) % 10000 == 0:
            log_memory_usage()
            logger.info(f"Processed {i + 1} instances, reservoir size: {len(reservoir)}")

    logger.info(f"Subsampling complete. Final reservoir size: {len(reservoir)}")
    return reservoir


def save_instances_to_parquet(instances: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save instances to a Parquet file for efficient storage and loading.

    Args:
        instances: List of instance dictionaries
        output_path: Path to output Parquet file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Convert to DataFrame
    df = pd.DataFrame(instances)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(instances)} instances to {output_path}")


def load_instances_from_parquet(input_path: str) -> List[Dict[str, Any]]:
    """
    Load instances from a Parquet file.

    Args:
        input_path: Path to input Parquet file

    Returns:
        List of instance dictionaries
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Parquet file not found: {input_path}")

    df = pd.read_parquet(input_path)
    instances = df.to_dict('records')
    logger.info(f"Loaded {len(instances)} instances from {input_path}")
    return instances


def validate_sample_size(
    input_path: str,
    min_instances: int = 10000,
    target_memory_gb: float = 7.0
) -> bool:
    """
    Validate that the subsampled dataset meets the minimum threshold for statistical power.

    Args:
        input_path: Path to the subsampled Parquet file
        min_instances: Minimum number of instances required (default 10,000)
        target_memory_gb: Target memory constraint for logging reference

    Returns:
        True if validation passes

    Raises:
        ValueError: If the sample size is below the minimum threshold
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Subsampled dataset not found at {input_path}. "
                              "Run subsample_instances first.")

    instances = load_instances_from_parquet(input_path)
    count = len(instances)

    logger.info(f"Validating sample size: {count} instances (target memory: {target_memory_gb}GB)")
    logger.info(f"Minimum threshold: {min_instances} instances")

    if count < min_instances:
        error_msg = (
            f"CRITICAL: Sample size ({count}) is below minimum threshold ({min_instances}). "
            f"This is insufficient for statistical power. The pipeline cannot proceed. "
            f"Increase target_memory_gb or adjust subsampling parameters."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Validation passed: {count} instances meets minimum threshold of {min_instances}")
    log_memory_usage()
    return True