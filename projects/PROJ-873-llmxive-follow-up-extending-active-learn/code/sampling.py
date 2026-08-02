"""
Sampling module for T013b: Stratified sampling of flagged comparisons.

Filters logged comparisons for similarity > 0.95, reads sample size from
data/results/sample_config.json, and selects a stratified random sample
based on cosine similarity score bins.
"""
import json
import os
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Constants
COMPARISON_LOG_PATH = "data/processed/comparison_log.json"
SAMPLE_CONFIG_PATH = "data/results/sample_config.json"
CONSENSUS_SAMPLE_PATH = "data/results/consensus_sample.json"
SIMILARITY_THRESHOLD = 0.95
BIN_WIDTH = 0.01  # e.g., [0.95, 0.96), [0.96, 0.97), ...

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_comparison_logs(log_path: str = COMPARISON_LOG_PATH) -> List[Dict[str, Any]]:
    """Load comparison logs from JSON file."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Comparison log file not found: {log_path}")
    
    with open(log_path, "r", encoding="utf-8") as f:
        logs = json.load(f)
    
    logger.info(f"Loaded {len(logs)} comparison logs from {log_path}")
    return logs


def filter_wasted_calls(logs: List[Dict[str, Any]], threshold: float = SIMILARITY_THRESHOLD) -> List[Dict[str, Any]]:
    """Filter logs for pairs with similarity > threshold (wasted calls)."""
    wasted = [log for log in logs if log.get("similarity", 0.0) > threshold]
    logger.info(f"Filtered {len(wasted)} wasted calls (similarity > {threshold})")
    return wasted


def stratify_by_similarity(
    wasted_calls: List[Dict[str, Any]], 
    bin_width: float = BIN_WIDTH,
    threshold: float = SIMILARITY_THRESHOLD
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Stratify wasted calls by cosine similarity score bins.
    
    Bins are of fixed width (e.g., 0.01), starting from the threshold.
    e.g., [0.95, 0.96), [0.96, 0.97), ...
    """
    bins = defaultdict(list)
    
    for call in wasted_calls:
        sim = call.get("similarity", 0.0)
        # Calculate bin index
        bin_idx = int((sim - threshold) / bin_width)
        bin_label = f"[{threshold + bin_idx * bin_width:.2f}, {threshold + (bin_idx + 1) * bin_width:.2f})"
        bins[bin_label].append(call)
    
    logger.info(f"Stratified into {len(bins)} bins: {list(bins.keys())}")
    for bin_label, items in bins.items():
        logger.debug(f"  {bin_label}: {len(items)} items")
    
    return dict(bins)


def select_stratified_sample(
    stratified_bins: Dict[str, List[Dict[str, Any]]], 
    sample_size: int
) -> List[int]:
    """
    Select a stratified random sample from bins.
    
    Allocation: proportional to bin size, with at least 1 item per non-empty bin
    if sample_size allows.
    """
    total_items = sum(len(items) for items in stratified_bins.values())
    
    if total_items == 0:
        logger.warning("No items in any bin; returning empty sample")
        return []
    
    if sample_size > total_items:
        logger.warning(f"Requested sample_size ({sample_size}) > total items ({total_items}); using all items")
        sample_size = total_items
    
    # Calculate proportional allocation
    bin_sizes = {k: len(v) for k, v in stratified_bins.items()}
    allocations = {}
    remaining = sample_size
    
    # First pass: proportional allocation
    for bin_label, size in bin_sizes.items():
        if size == 0:
            allocations[bin_label] = 0
            continue
        
        # Proportional share
        share = int((size / total_items) * sample_size)
        # Ensure at least 1 if bin is non-empty and we have budget
        if share == 0 and remaining > 0:
            share = 1
        
        allocations[bin_label] = min(share, size)
        remaining -= allocations[bin_label]
    
    # Second pass: distribute remaining items
    non_empty_bins = [k for k, v in bin_sizes.items() if v > 0 and allocations[k] < v]
    while remaining > 0 and non_empty_bins:
        bin_label = random.choice(non_empty_bins)
        if allocations[bin_label] < bin_sizes[bin_label]:
            allocations[bin_label] += 1
            remaining -= 1
        else:
            non_empty_bins.remove(bin_label)
    
    # Select items
    selected_indices = []
    for bin_label, count in allocations.items():
        items = stratified_bins[bin_label]
        if count > 0:
            indices = [item["index"] for item in random.sample(items, count)]
            selected_indices.extend(indices)
    
    logger.info(f"Selected {len(selected_indices)} samples from {len(stratified_bins)} bins")
    return selected_indices


def load_sample_config(config_path: str = SAMPLE_CONFIG_PATH) -> Dict[str, Any]:
    """Load sample configuration from JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Sample config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    logger.info(f"Loaded sample config: {config}")
    return config


def run_sampling_pipeline(
    log_path: str = COMPARISON_LOG_PATH,
    config_path: str = SAMPLE_CONFIG_PATH,
    output_path: str = CONSENSUS_SAMPLE_PATH,
    threshold: float = SIMILARITY_THRESHOLD,
    bin_width: float = BIN_WIDTH
) -> List[int]:
    """
    Run the full sampling pipeline:
    1. Load comparison logs
    2. Filter for wasted calls (similarity > threshold)
    3. Stratify by similarity bins
    4. Select stratified random sample
    5. Save sample indices to output file
    """
    # Step 1: Load logs
    logs = load_comparison_logs(log_path)
    
    # Step 2: Filter wasted calls
    wasted_calls = filter_wasted_calls(logs, threshold)
    
    if not wasted_calls:
        logger.warning("No wasted calls found; writing empty sample")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        return []
    
    # Step 3: Stratify
    stratified_bins = stratify_by_similarity(wasted_calls, bin_width, threshold)
    
    # Step 4: Load config and select sample
    config = load_sample_config(config_path)
    sample_size = config.get("sample_size", 10)
    
    selected_indices = select_stratified_sample(stratified_bins, sample_size)
    
    # Step 5: Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(selected_indices, f, indent=2)
    
    logger.info(f"Wrote {len(selected_indices)} sample indices to {output_path}")
    return selected_indices


def main():
    """CLI entry point for sampling pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run stratified sampling on flagged comparisons")
    parser.add_argument("--log-path", type=str, default=COMPARISON_LOG_PATH,
                        help="Path to comparison log file")
    parser.add_argument("--config-path", type=str, default=SAMPLE_CONFIG_PATH,
                        help="Path to sample config file")
    parser.add_argument("--output-path", type=str, default=CONSENSUS_SAMPLE_PATH,
                        help="Path to write sample indices")
    parser.add_argument("--threshold", type=float, default=SIMILARITY_THRESHOLD,
                        help="Similarity threshold for wasted calls")
    parser.add_argument("--bin-width", type=float, default=BIN_WIDTH,
                        help="Width of similarity bins")
    
    args = parser.parse_args()
    
    sample_indices = run_sampling_pipeline(
        log_path=args.log_path,
        config_path=args.config_path,
        output_path=args.output_path,
        threshold=args.threshold,
        bin_width=args.bin_width
    )
    
    print(f"Selected {len(sample_indices)} samples. Output written to {args.output_path}")


if __name__ == "__main__":
    main()
