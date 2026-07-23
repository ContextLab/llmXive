import json
import os
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from metrics import calculate_dynamic_sample_size
from config import get_config

def load_comparison_logs():
    """Load the logged pairwise comparisons from the pipeline."""
    config = get_config()
    log_path = os.path.join(config.data_dir, 'logs', 'comparisons.json')
    if not os.path.exists(log_path):
        # Fallback to a common location if logs are elsewhere
        log_path = os.path.join(config.data_dir, 'processed', 'comparison_logs.json')
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            return json.load(f)
    return []

def filter_wasted_calls(comparisons: List[Dict[str, Any]]):
    """Filter comparisons that are flagged as 'wasted' (similarity > 0.95)."""
    wasted = []
    for comp in comparisons:
        if comp.get('similarity', 0) > 0.95:
            wasted.append(comp)
    return wasted

def stratify_by_query(comparisons: List[Dict[str, Any]]):
    """Group comparisons by query_id for stratified sampling."""
    buckets = defaultdict(list)
    for comp in comparisons:
        qid = comp.get('query_id', 'unknown')
        buckets[qid].append(comp)
    return buckets

def select_stratified_sample(comparisons: List[Dict[str, Any]], sample_size: int) -> List[int]:
    """Select a stratified random sample from comparisons."""
    if not comparisons:
        return []
    
    random.shuffle(comparisons)
    sample = comparisons[:sample_size]
    return [c.get('index', i) for i, c in enumerate(sample)]

def run_sampling_pipeline():
    """
    Main entry point to generate the consensus sample.
    This ensures data/results/consensus_sample.json is written.
    """
    config = get_config()
    
    # Load comparison logs
    comparisons = load_comparison_logs()
    if not comparisons:
        logging.warning("No comparison logs found. Creating an empty sample.")
        # Create empty sample if no data
        output_path = os.path.join(config.data_dir, 'results', 'consensus_sample.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump([], f)
        return []
    
    # Filter wasted calls
    wasted = filter_wasted_calls(comparisons)
    
    if not wasted:
        logging.warning("No wasted calls found. Creating an empty sample.")
        output_path = os.path.join(config.data_dir, 'results', 'consensus_sample.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump([], f)
        return []
    
    # Calculate dynamic sample size
    sample_size = calculate_dynamic_sample_size(len(wasted))
    sample_size = min(sample_size, len(wasted))
    
    # Stratify and sample
    buckets = stratify_by_query(wasted)
    sample_indices = []
    
    # Simple stratified sampling: take proportional sample from each bucket
    for qid, items in buckets.items():
        n = max(1, int(len(items) * (sample_size / len(wasted))))
        n = min(n, len(items))
        selected = random.sample(items, n)
        sample_indices.extend([item.get('index', i) for i, item in enumerate(selected)])
    
    # Ensure we have exactly sample_size items
    if len(sample_indices) > sample_size:
        sample_indices = random.sample(sample_indices, sample_size)
    
    # Write output
    output_path = os.path.join(config.data_dir, 'results', 'consensus_sample.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(sample_indices, f, indent=2)
    
    logging.info(f"Consensus sample generated: {len(sample_indices)} items -> {output_path}")
    return sample_indices

def main():
    run_sampling_pipeline()

if __name__ == "__main__":
    main()