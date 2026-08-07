"""
sampling.py - Sampling pipeline for LLM consensus validation.

This module implements the sampling logic required for T013c:
- Filter logged comparisons for similarity > 0.95
- Select a simple random sample based on sample_config.json
- Write sample indices to consensus_sample.json
"""
import json
import os
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from pathlib import Path

from config import get_config

logger = logging.getLogger(__name__)

def load_comparison_logs():
    """Load the comparison log from data/processed/comparison_log.json."""
    config = get_config()
    log_path = Path(config.data_dir) / "processed" / "comparison_log.json"
    
    if not log_path.exists():
        raise FileNotFoundError(f"Comparison log not found: {log_path}")
    
    comparisons = []
    with open(log_path, 'r') as f:
        for line in f:
            if line.strip():
                comparisons.append(json.loads(line))
    
    return comparisons

def filter_wasted_calls(comparisons: List[Dict], threshold: float = 0.95):
    """
    Filter comparisons to find 'wasted' calls (similarity > threshold).
    
    Args:
        comparisons: List of comparison records
        threshold: Similarity threshold for wasted calls
        
    Returns:
        List of indices of wasted comparisons
    """
    wasted_indices = []
    for i, comp in enumerate(comparisons):
        if comp.get("cosine_sim", 0) > threshold:
            wasted_indices.append(i)
    
    return wasted_indices

def stratify_by_similarity(comparisons: List[Dict]):
    """Stratify comparisons by similarity buckets."""
    buckets = defaultdict(list)
    for i, comp in enumerate(comparisons):
        sim = comp.get("cosine_sim", 0)
        if sim > 0.95:
            bucket = "high"
        elif sim > 0.8:
            bucket = "medium"
        else:
            bucket = "low"
        buckets[bucket].append(i)
    
    return dict(buckets)

def select_stratified_sample(comparisons: List[Dict], sample_size: int):
    """
    Select a simple random sample from wasted calls.
    
    Args:
        comparisons: Full list of comparisons
        sample_size: Number of samples to select
        
    Returns:
        List of selected indices
    """
    wasted_indices = filter_wasted_calls(comparisons)
    
    if len(wasted_indices) <= sample_size:
        return wasted_indices
    
    return random.sample(wasted_indices, sample_size)

def load_sample_config():
    """Load sample configuration from data/results/sample_config.json."""
    config = get_config()
    config_path = Path(config.data_dir) / "results" / "sample_config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Sample config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def run_sampling_pipeline():
    """
    Main sampling pipeline for T013c.
    
    1. Load comparison logs
    2. Filter for wasted calls (sim > 0.95)
    3. Load sample config
    4. Select random sample
    5. Write to consensus_sample.json
    """
    config = get_config()
    results_dir = Path(config.data_dir) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load comparison logs
    logger.info("Loading comparison logs")
    comparisons = load_comparison_logs()
    logger.info(f"Loaded {len(comparisons)} comparisons")
    
    # Load sample config
    logger.info("Loading sample configuration")
    sample_config = load_sample_config()
    sample_size = sample_config["sample_size"]
    logger.info(f"Selected sample size: {sample_size}")
    
    # Select sample
    logger.info("Selecting random sample")
    sample_indices = select_stratified_sample(comparisons, sample_size)
    logger.info(f"Selected {len(sample_indices)} indices")
    
    # Write to consensus_sample.json
    output_path = results_dir / "consensus_sample.json"
    with open(output_path, 'w') as f:
        json.dump(sample_indices, f, indent=2)
    
    logger.info(f"Sample written to {output_path}")
    return sample_indices

def main():
    """Entry point for sampling pipeline."""
    init_logging()
    run_sampling_pipeline()

if __name__ == "__main__":
    main()
