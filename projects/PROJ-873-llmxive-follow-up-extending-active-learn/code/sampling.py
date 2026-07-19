import json
import os
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from metrics import load_results_from_json

logger = logging.getLogger(__name__)

def load_comparison_logs(log_path: str) -> List[Dict[str, Any]]:
    """
    Load pairwise comparison logs from a JSON file.
    
    Args:
        log_path: Path to the JSON file containing comparison logs.
        
    Returns:
        List of comparison records.
    """
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Comparison log file not found: {log_path}")
    
    with open(log_path, 'r') as f:
        data = json.load(f)
        
    # Handle different possible structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'comparisons' in data:
        return data['comparisons']
    else:
        # Try to extract list from nested structure
        for key in data:
            if isinstance(data[key], list):
                return data[key]
        raise ValueError(f"Could not find comparison list in {log_path}")

def filter_wasted_calls(comparisons: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """
    Filter comparisons to keep only those with similarity > threshold (wasted calls).
    
    Args:
        comparisons: List of comparison records.
        threshold: Similarity threshold for filtering.
        
    Returns:
        List of comparisons with similarity > threshold.
    """
    wasted = []
    for comp in comparisons:
        sim = comp.get('similarity', comp.get('cosine_similarity', 0.0))
        if sim > threshold:
            wasted.append(comp)
    return wasted

def stratify_by_query(comparisons: List[Dict[str, Any]], n_bins: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Stratify comparisons by similarity score bins.
    
    Args:
        comparisons: List of comparison records.
        n_bins: Number of bins to create.
        
    Returns:
        Dictionary mapping bin labels to lists of comparisons.
    """
    if not comparisons:
        return {}
        
    # Extract similarities
    similarities = [comp.get('similarity', comp.get('cosine_similarity', 0.0)) for comp in comparisons]
    min_sim = min(similarities)
    max_sim = max(similarities)
    
    # Ensure we cover the range from 0.95 to 1.0 if possible
    if min_sim < 0.95:
        min_sim = 0.95
        
    bin_width = (max_sim - min_sim) / n_bins if max_sim > min_sim else 0.001
    
    # Create bins
    bins = defaultdict(list)
    for comp in comparisons:
        sim = comp.get('similarity', comp.get('cosine_similarity', 0.0))
        if sim < 0.95:
            continue  # Skip if below threshold
            
        # Determine bin index
        if bin_width > 0:
            bin_idx = min(int((sim - min_sim) / bin_width), n_bins - 1)
        else:
            bin_idx = 0
            
        bin_label = f"bin_{bin_idx:02d}_{min_sim + bin_idx * bin_width:.3f}_{min_sim + (bin_idx + 1) * bin_width:.3f}"
        bins[bin_label].append(comp)
        
    return dict(bins)

def select_stratified_sample(
    bins: Dict[str, List[Dict[str, Any]]], 
    sample_size: int
) -> List[int]:
    """
    Select a stratified random sample from the bins.
    
    Args:
        bins: Dictionary mapping bin labels to lists of comparisons.
        sample_size: Total number of samples to select.
        
    Returns:
        List of indices into the original comparison list.
    """
    if not bins:
        return []
        
    # Calculate samples per bin proportionally
    total_in_bins = sum(len(items) for items in bins.values())
    if total_in_bins == 0:
        return []
        
    # Assign samples to bins proportionally
    samples_per_bin = {}
    remaining = sample_size
    sorted_bins = sorted(bins.keys(), key=lambda x: len(bins[x]), reverse=True)
    
    for i, bin_label in enumerate(sorted_bins):
        if i == len(sorted_bins) - 1:
            # Last bin gets remaining samples
            count = min(remaining, len(bins[bin_label]))
        else:
            # Proportional allocation
            prop = len(bins[bin_label]) / total_in_bins
            count = int(prop * sample_size)
            remaining -= count
            count = min(count, len(bins[bin_label]))
            
        samples_per_bin[bin_label] = count
        
    # Select samples
    selected_indices = []
    for bin_label, count in samples_per_bin.items():
        if count > 0:
            indices = list(range(len(bins[bin_label])))
            selected = random.sample(indices, min(count, len(indices)))
            selected_indices.extend(selected)
            
    return selected_indices

def run_sampling_pipeline(
    log_path: str,
    sample_config_path: str,
    output_path: str,
    similarity_threshold: float = 0.95
) -> List[int]:
    """
    Run the full sampling pipeline: load logs, filter wasted calls,
    stratify, and select sample.
    
    Args:
        log_path: Path to comparison logs.
        sample_config_path: Path to sample configuration JSON.
        output_path: Path to write the sample indices.
        similarity_threshold: Threshold for identifying wasted calls.
        
    Returns:
        List of selected sample indices.
    """
    # Load sample configuration
    if not os.path.exists(sample_config_path):
        raise FileNotFoundError(f"Sample config not found: {sample_config_path}")
        
    with open(sample_config_path, 'r') as f:
        config = json.load(f)
        
    sample_size = config.get('sample_size', 20)
    
    # Load comparison logs
    comparisons = load_comparison_logs(log_path)
    logger.info(f"Loaded {len(comparisons)} comparison records")
    
    # Filter for wasted calls (similarity > threshold)
    wasted = filter_wasted_calls(comparisons, similarity_threshold)
    logger.info(f"Found {len(wasted)} wasted calls (similarity > {similarity_threshold})")
    
    if not wasted:
        logger.warning("No wasted calls found. Returning empty sample.")
        selected_indices = []
    else:
        # Stratify by similarity bins
        bins = stratify_by_query(wasted)
        logger.info(f"Stratified into {len(bins)} bins")
        
        # Select stratified sample
        selected_indices = select_stratified_sample(bins, sample_size)
        logger.info(f"Selected {len(selected_indices)} samples")
        
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(selected_indices, f, indent=2)
        
    logger.info(f"Sample indices written to {output_path}")
    return selected_indices

def main():
    """Main entry point for the sampling pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run stratified sampling for consensus validation')
    parser.add_argument('--log-path', type=str, required=True,
                      help='Path to comparison logs JSON')
    parser.add_argument('--sample-config', type=str, required=True,
                      help='Path to sample configuration JSON')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to write sample indices')
    parser.add_argument('--threshold', type=float, default=0.95,
                      help='Similarity threshold for wasted calls')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    run_sampling_pipeline(
        log_path=args.log_path,
        sample_config_path=args.sample_config,
        output_path=args.output,
        similarity_threshold=args.threshold
    )
