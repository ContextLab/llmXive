"""
Query module for LatentSkill retrieval and interpolation.

This module handles:
1. Generating query vectors from text using all-MiniLM-L6-v2.
2. Retrieving nearest neighbors from the skill index.
3. Interpolating LoRA adapters (unweighted mean, cosine-weighted average).
4. Measuring and logging latency metrics.
5. Calculating computational savings compared to baseline hypernetwork.
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

# Local imports matching API surface
from src.utils.config import get_project_root, get_results_path, set_seed
from src.retrieval.strategies import (
    load_skill_index,
    single_nearest_neighbor,
    unweighted_mean,
    cosine_weighted_average
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "all-MiniLM-L6-v2"
LATENCY_METRICS_FILE = "latency_metrics.json"

def load_baseline_latency() -> Optional[float]:
    """
    Load baseline latency from the latency metrics file.
    
    Returns:
        float: baseline_latency_ms if found, None otherwise.
    """
    project_root = get_project_root()
    results_path = get_results_path(project_root)
    metrics_file = results_path / LATENCY_METRICS_FILE
    
    if not metrics_file.exists():
        logger.warning(f"Latency metrics file not found: {metrics_file}")
        return None
        
    try:
        with open(metrics_file, 'r') as f:
            data = json.load(f)
            return data.get('baseline_latency_ms')
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read baseline latency: {e}")
        return None

def calculate_computational_savings(baseline_latency: Optional[float], total_selection_latency: float) -> Optional[float]:
    """
    Calculate computational savings: baseline_latency - total_skill_selection_latency.
    
    Args:
        baseline_latency (Optional[float]): Baseline hypernetwork latency in ms.
        total_selection_latency (float): Total skill selection latency in ms.
        
    Returns:
        Optional[float]: Savings in ms, or None if baseline is NaN/None.
    """
    if baseline_latency is None or (isinstance(baseline_latency, float) and np.isnan(baseline_latency)):
        logger.warning("Baseline latency is NaN or None. Setting savings to NaN.")
        return float('nan')
        
    return baseline_latency - total_selection_latency

def save_latency_metrics(metrics: Dict[str, Any], project_root: Path) -> None:
    """
    Save latency metrics to the results directory.
    
    Args:
        metrics (Dict[str, Any]): Dictionary containing latency metrics.
        project_root (Path): Project root directory.
    """
    results_path = get_results_path(project_root)
    metrics_file = results_path / LATENCY_METRICS_FILE
    
    # Load existing metrics if present to append
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                existing_data = json.load(f)
                existing_data.update(metrics)
                metrics = existing_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing metrics, overwriting: {e}")
    
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved latency metrics to {metrics_file}")

def main():
    """
    Main entry point for T059c: Calculate computational savings.
    
    This function:
    1. Loads baseline latency from previous runs.
    2. Reads total_skill_selection_latency from existing metrics (from T019).
    3. Calculates savings = baseline - total_selection.
    4. Appends 'computational_savings_ms' to latency_metrics.json.
    """
    parser = argparse.ArgumentParser(description="Calculate computational savings for LatentSkill retrieval.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to configuration file.")
    args = parser.parse_args()
    
    project_root = get_project_root()
    set_seed(42)
    
    logger.info("Starting computational savings calculation (T059c).")
    
    # 1. Load baseline latency (from T059)
    baseline_latency = load_baseline_latency()
    
    # 2. Load total_skill_selection_latency from existing metrics (from T019)
    results_path = get_results_path(project_root)
    metrics_file = results_path / LATENCY_METRICS_FILE
    
    total_selection_latency = None
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                data = json.load(f)
                total_selection_latency = data.get('total_skill_selection_latency_ms')
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read total_skill_selection_latency: {e}")
    
    if total_selection_latency is None:
        logger.error("total_skill_selection_latency_ms not found in metrics. Cannot calculate savings.")
        # Create a minimal metrics file indicating failure if it doesn't exist
        if not metrics_file.exists():
            save_latency_metrics({'computational_savings_ms': float('nan'), 'error': 'Missing total_skill_selection_latency'}, project_root)
        return
    
    logger.info(f"Baseline Latency: {baseline_latency} ms")
    logger.info(f"Total Selection Latency: {total_selection_latency} ms")
    
    # 3. Calculate savings
    savings = calculate_computational_savings(baseline_latency, total_selection_latency)
    
    # 4. Save result
    metrics_to_save = {
        'computational_savings_ms': savings
    }
    
    save_latency_metrics(metrics_to_save, project_root)
    
    logger.info(f"Computational savings calculated: {savings} ms")
    logger.info("T059c completed successfully.")

if __name__ == "__main__":
    main()