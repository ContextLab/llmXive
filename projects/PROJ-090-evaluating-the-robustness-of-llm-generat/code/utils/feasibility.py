"""
Feasibility Estimator for LLM Code Robustness Study.

This module calculates the maximum number of samples (MAX_SAMPLES) the pipeline
can process given estimated runtime and memory constraints per sample.
It adheres to SC-003 (Runtime constraints) and SC-006 (Memory constraints).

The estimator reads configuration from code/config.py and writes the result
to data/config/feasibility.json.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories, get_config_summary
from utils.logging import get_budget_logger

# Constants for resource constraints (SC-003, SC-006)
# These are conservative estimates for CPU execution with 4-bit quantization
MEMORY_LIMIT_GB = 7.0  # SC-003: Hard limit to prevent OOM on shared nodes
TIME_LIMIT_SECONDS = 300  # SC-006: Max wall-clock time per run (5 mins)

# Estimated costs per sample (based on StarCoder2-3B 4-bit on CPU)
# These are rough averages derived from pilot runs; in a real deployment,
# these could be measured dynamically.
ESTIMATED_MEMORY_PER_SAMPLE_GB = 1.5  # Model load + execution overhead
ESTIMATED_TIME_PER_SAMPLE_SECONDS = 45.0  # Inference + Sandbox execution + Parsing

logger = get_budget_logger()

def estimate_feasibility() -> Dict[str, Any]:
    """
    Calculates the maximum number of samples (MAX_SAMPLES) that can be processed
    within the defined resource constraints.

    Returns:
        Dict containing:
            - max_samples: int, the calculated limit
            - constraint: str, which constraint was the bottleneck ('memory' or 'time')
            - estimated_memory_per_sample_gb: float
            - estimated_time_per_sample_seconds: float
            - memory_limit_gb: float
            - time_limit_seconds: float
    """
    # Calculate based on memory constraint
    max_by_memory = int(MEMORY_LIMIT_GB / ESTIMATED_MEMORY_PER_SAMPLE_GB)
    
    # Calculate based on time constraint
    max_by_time = int(TIME_LIMIT_SECONDS / ESTIMATED_TIME_PER_SAMPLE_SECONDS)

    # The feasible limit is the minimum of both
    max_samples = min(max_by_memory, max_by_time)
    
    if max_by_memory < max_by_time:
        bottleneck = "memory"
    else:
        bottleneck = "time"

    result = {
        "max_samples": max_samples,
        "constraint_bottleneck": bottleneck,
        "estimated_memory_per_sample_gb": ESTIMATED_MEMORY_PER_SAMPLE_GB,
        "estimated_time_per_sample_seconds": ESTIMATED_TIME_PER_SAMPLE_SECONDS,
        "memory_limit_gb": MEMORY_LIMIT_GB,
        "time_limit_seconds": TIME_LIMIT_SECONDS,
        "max_samples_by_memory": max_by_memory,
        "max_samples_by_time": max_by_time,
        "calculation_timestamp": "T029a-feasibility-calc"
    }

    return result

def save_feasibility_report(result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Saves the feasibility calculation result to a JSON file.

    Args:
        result: The feasibility result dictionary.
        output_path: Optional custom path. Defaults to data/config/feasibility.json.

    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "data" / "config" / "feasibility.json"
    
    # Ensure directory exists
    ensure_directories([str(output_path.parent)])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Feasibility report saved to {output_path}")
    return output_path

def main():
    """
    Entry point for the feasibility estimator.
    Calculates MAX_SAMPLES and writes to data/config/feasibility.json.
    """
    logger.info("Starting feasibility estimation for budget cap logic (T029a)...")
    
    # Ensure data/config directory exists
    ensure_directories([str(PROJECT_ROOT / "data" / "config")])
    
    # Perform calculation
    result = estimate_feasibility()
    
    # Save result
    output_path = save_feasibility_report(result)
    
    # Log summary
    logger.info(f"Feasibility Estimation Complete:")
    logger.info(f"  - Max Samples (MAX_SAMPLES): {result['max_samples']}")
    logger.info(f"  - Bottleneck Constraint: {result['constraint_bottleneck']}")
    logger.info(f"  - Output File: {output_path}")
    
    return result

if __name__ == "__main__":
    main()
