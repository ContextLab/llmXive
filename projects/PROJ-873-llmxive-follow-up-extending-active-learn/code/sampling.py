"""
Sampling module for stratified selection of consensus validation samples.
Implements FR-003: Select stratified random sample of flagged pairs for LLM validation.
"""

import json
import os
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Import from existing API surface
from config import get_config

logger = logging.getLogger(__name__)

def load_comparison_logs(comparison_log_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load pairwise comparison logs from the JSON file.

    Args:
        comparison_log_path: Path to the comparison log file. If None, uses config default.

    Returns:
        List of comparison records.
    """
    config = get_config()
    if comparison_log_path is None:
        comparison_log_path = os.path.join(config.data_dir, 'results', 'flagged_pairs_count.json')
    
    # Handle case where file might not exist yet (T013a hasn't run)
    if not os.path.exists(comparison_log_path):
        logger.warning(f"Comparison log not found at {comparison_log_path}. Returning empty list.")
        return []

    with open(comparison_log_path, 'r') as f:
        data = json.load(f)
    
    # The file structure from T013a is expected to be a list of flagged pairs
    # with their similarity scores and metadata
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'flagged_pairs' in data:
        return data['flagged_pairs']
    else:
        logger.error(f"Unexpected data structure in {comparison_log_path}")
        return []

def filter_wasted_calls(comparisons: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """
    Filter comparisons to keep only those with similarity > threshold.

    Args:
        comparisons: List of comparison records.
        threshold: Similarity threshold for "wasted" calls.

    Returns:
        Filtered list of comparisons.
    """
    return [
        comp for comp in comparisons 
        if comp.get('similarity', 0) > threshold
    ]

def stratify_by_query(comparisons: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group comparisons by query_id for stratification.

    Args:
        comparisons: List of comparison records.

    Returns:
        Dictionary mapping query_id to list of comparisons.
    """
    strata = defaultdict(list)
    for comp in comparisons:
        query_id = comp.get('query_id', 'unknown')
        strata[query_id].append(comp)
    return dict(strata)

def select_stratified_sample(
    strata: Dict[str, List[Dict[str, Any]]], 
    sample_size: int
) -> List[Dict[str, Any]]:
    """
    Select a stratified random sample from the comparisons.
    Proportionally allocates sample size across strata.

    Args:
        strata: Dictionary mapping query_id to list of comparisons.
        sample_size: Total number of samples to select.

    Returns:
        List of selected comparison records with their indices.
    """
    if not strata:
        return []

    # Calculate total items across all strata
    total_items = sum(len(items) for items in strata.values())
    
    if total_items <= sample_size:
        # If we have fewer items than sample size, return all with their original indices
        result = []
        global_idx = 0
        for query_id, items in strata.items():
            for item in items:
                item_with_idx = item.copy()
                item_with_idx['sample_index'] = global_idx
                result.append(item_with_idx)
                global_idx += 1
        return result

    # Calculate proportional allocation per stratum
    sample_allocation = {}
    for query_id, items in strata.items():
        proportion = len(items) / total_items
        allocated = max(1, int(round(proportion * sample_size)))
        # Ensure we don't allocate more than available
        allocated = min(allocated, len(items))
        sample_allocation[query_id] = allocated

    # Adjust allocation if sum exceeds sample_size (due to rounding)
    current_sum = sum(sample_allocation.values())
    if current_sum > sample_size:
        # Remove excess from largest strata
        excess = current_sum - sample_size
        sorted_strata = sorted(sample_allocation.items(), key=lambda x: x[1], reverse=True)
        for i in range(excess):
            query_id, _ = sorted_strata[i]
            if sample_allocation[query_id] > 1:
                sample_allocation[query_id] -= 1

    # Select samples from each stratum
    selected_samples = []
    global_idx = 0
    
    # Sort strata by query_id for deterministic ordering
    for query_id in sorted(strata.keys()):
        items = strata[query_id]
        n_select = sample_allocation.get(query_id, 0)
        
        # Randomly select indices
        selected_indices = random.sample(range(len(items)), n_select)
        
        for idx in selected_indices:
            item = items[idx]
            item_with_idx = item.copy()
            item_with_idx['sample_index'] = global_idx
            item_with_idx['original_stratum'] = query_id
            selected_samples.append(item_with_idx)
            global_idx += 1

    # Shuffle the final result to mix strata
    random.shuffle(selected_samples)
    
    # Re-assign sequential indices after shuffle
    for i, item in enumerate(selected_samples):
        item['sample_index'] = i

    return selected_samples

def run_sampling_pipeline(
    comparison_log_path: Optional[str] = None,
    sample_config_path: Optional[str] = None,
    output_path: Optional[str] = None,
    similarity_threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Run the complete sampling pipeline:
    1. Load comparison logs
    2. Filter for wasted calls (similarity > threshold)
    3. Stratify by query
    4. Select stratified random sample
    5. Write sample indices to output file

    Args:
        comparison_log_path: Path to comparison logs (T013a output)
        sample_config_path: Path to sample config (T013c output)
        output_path: Path to write consensus sample (T013b output)
        similarity_threshold: Threshold for wasted call detection

    Returns:
        Dictionary with sampling results and statistics.
    """
    config = get_config()
    
    # Set defaults if not provided
    if comparison_log_path is None:
        comparison_log_path = os.path.join(config.data_dir, 'results', 'flagged_pairs_count.json')
    if sample_config_path is None:
        sample_config_path = os.path.join(config.data_dir, 'results', 'sample_config.json')
    if output_path is None:
        output_path = os.path.join(config.data_dir, 'results', 'consensus_sample.json')

    logger.info(f"Loading comparison logs from {comparison_log_path}")
    comparisons = load_comparison_logs(comparison_log_path)
    
    if not comparisons:
        logger.warning("No comparisons found. Creating empty sample.")
        result = {
            'sample': [],
            'total_flagged': 0,
            'sample_size': 0,
            'strata_count': 0
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result

    logger.info(f"Loaded {len(comparisons)} comparisons")

    # Read sample size from config
    sample_size = 20  # Default
    if os.path.exists(sample_config_path):
        with open(sample_config_path, 'r') as f:
            sample_config = json.load(f)
            sample_size = sample_config.get('sample_size', 20)
            logger.info(f"Using sample size {sample_size} from {sample_config_path}")

    # Filter for wasted calls
    wasted_calls = filter_wasted_calls(comparisons, threshold=similarity_threshold)
    logger.info(f"Found {len(wasted_calls)} wasted calls (similarity > {similarity_threshold})")

    if not wasted_calls:
        logger.warning("No wasted calls found after filtering. Creating empty sample.")
        result = {
            'sample': [],
            'total_flagged': 0,
            'sample_size': 0,
            'strata_count': 0
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result

    # Stratify by query
    strata = stratify_by_query(wasted_calls)
    logger.info(f"Stratified into {len(strata)} query groups")

    # Select stratified sample
    selected_sample = select_stratified_sample(strata, sample_size)
    logger.info(f"Selected {len(selected_sample)} samples for consensus validation")

    # Prepare output
    result = {
        'sample': selected_sample,
        'total_flagged': len(wasted_calls),
        'sample_size': len(selected_sample),
        'strata_count': len(strata),
        'sample_config': {
            'requested_size': sample_size,
            'threshold': similarity_threshold,
            'allocation_method': 'proportional_stratified'
        }
    }

    # Write output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Consensus sample written to {output_path}")
    
    return result

def main():
    """Main entry point for running the sampling pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run stratified sampling for consensus validation.")
    parser.add_argument(
        '--comparison-log', 
        type=str, 
        default=None,
        help='Path to comparison logs (default: from config)'
    )
    parser.add_argument(
        '--sample-config',
        type=str,
        default=None,
        help='Path to sample config (default: from config)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output consensus sample (default: from config)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.95,
        help='Similarity threshold for wasted calls (default: 0.95)'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = run_sampling_pipeline(
        comparison_log_path=args.comparison_log,
        sample_config_path=args.sample_config,
        output_path=args.output,
        similarity_threshold=args.threshold
    )
    
    print(f"Sampling complete: {result['sample_size']} samples selected from {result['total_flagged']} flagged calls")
    return 0

if __name__ == '__main__':
    exit(main())
