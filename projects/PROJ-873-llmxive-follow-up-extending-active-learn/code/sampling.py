import json
import os
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

def load_comparison_logs(path: str) -> List[Dict[str, Any]]:
    """Load comparison logs from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Comparison logs not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def filter_wasted_calls(logs: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """Filter logs to include only wasted calls (similarity > threshold)."""
    return [log for log in logs if log.get("similarity", 0.0) > threshold]

def stratify_by_similarity(logs: List[Dict[str, Any]], bins: int = 5) -> Dict[float, List[int]]:
    """
    Stratify logs by similarity score into bins.
    
    Returns a dictionary mapping bin center to list of indices.
    """
    if not logs:
        return {}
    
    # Determine range
    similarities = [log.get("similarity", 0.0) for log in logs]
    min_sim = min(similarities)
    max_sim = max(similarities)
    
    # Create bins
    bin_width = (max_sim - min_sim) / bins if max_sim > min_sim else 1.0
    bins_dict = defaultdict(list)
    
    for idx, log in enumerate(logs):
        sim = log.get("similarity", 0.0)
        # Calculate bin index
        bin_idx = int((sim - min_sim) / bin_width) if bin_width > 0 else 0
        bin_idx = min(bin_idx, bins - 1)  # Ensure within bounds
        bin_center = min_sim + bin_idx * bin_width + bin_width / 2
        bins_dict[bin_center].append(idx)
    
    return dict(bins_dict)

def select_stratified_sample(
    logs: List[Dict[str, Any]],
    sample_size: int,
    bins: int = 5
) -> List[int]:
    """
    Select a stratified random sample from logs.
    
    Args:
        logs: List of comparison logs
        sample_size: Total number of samples to select
        bins: Number of similarity bins for stratification
    
    Returns:
        List of indices selected for the sample
    """
    if not logs:
        return []
    
    # Filter for wasted calls
    wasted_logs = filter_wasted_calls(logs)
    if not wasted_logs:
        logger.warning("No wasted calls found for sampling")
        return []
    
    # Stratify
    strata = stratify_by_similarity(wasted_logs, bins)
    
    # Calculate proportional sample size per stratum
    total_wasted = len(wasted_logs)
    sample_indices = []
    
    for bin_center, indices in strata.items():
        # Proportional allocation
        prop = len(indices) / total_wasted
        n = max(1, int(prop * sample_size))  # At least 1 per stratum if possible
        
        # Ensure we don't exceed available
        n = min(n, len(indices))
        
        # Random sample from this stratum
        selected = random.sample(indices, n)
        sample_indices.extend(selected)
    
    # If we need more samples, fill from the largest strata
    while len(sample_indices) < sample_size and strata:
        # Find largest stratum not fully sampled
        for bin_center, indices in sorted(strata.items(), key=lambda x: len(x[1]), reverse=True):
            remaining = [i for i in indices if i not in sample_indices]
            if remaining:
                needed = sample_size - len(sample_indices)
                sample_indices.extend(random.sample(remaining, min(needed, len(remaining))))
                break
        else:
            break  # No more available
    
    return sample_indices[:sample_size]

def run_sampling_pipeline(
    logs_path: str,
    config_path: str,
    output_path: str
) -> None:
    """
    Run the full sampling pipeline.
    
    1. Load logs
    2. Load config (sample size)
    3. Select stratified sample
    4. Write output
    """
    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    sample_size = config.get("sample_size", 50)
    
    # Load logs
    logs = load_comparison_logs(logs_path)
    
    # Select sample
    sample_indices = select_stratified_sample(logs, sample_size)
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(sample_indices, f, indent=2)
    
    logger.info(f"Selected {len(sample_indices)} samples. Output: {output_path}")
    return sample_indices

def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    run_sampling_pipeline(
        logs_path="data/processed/comparison_logs.json",
        config_path="data/results/sample_config.json",
        output_path="data/results/consensus_sample.json"
    )

if __name__ == "__main__":
    main()