"""
Bin utility functions for threshold detection.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from utils.config import get_project_root, get_path, ensure_dir


def load_bin_counts_from_t19(
    file_path: Union[str, Path]
) -> Dict[str, Dict[str, int]]:
    """
    Load bin counts from T019 output.
    
    Args:
        file_path (Union[str, Path]): Path to the T019 output JSON.
        
    Returns:
        Dict[str, Dict[str, int]]: Bin counts and accuracy.
    """
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    
    with open(path_obj, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_chain_lengths_from_t13(
    file_path: Union[str, Path]
) -> List[int]:
    """
    Load chain lengths from T013 output.
    
    Args:
        file_path (Union[str, Path]): Path to the T013 output CSV.
        
    Returns:
        List[int]: List of chain lengths.
    """
    import csv
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path
    chain_lengths = []
    
    with open(path_obj, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                chain_lengths.append(int(row['chain_length']))
            except (ValueError, KeyError):
                continue
    
    return chain_lengths


def determine_bin_strategy(
    bin_counts: Dict[str, Dict[str, int]],
    min_samples: int = 50
) -> Dict[str, Any]:
    """
    Determine bin strategy based on sample counts.
    
    Args:
        bin_counts (Dict[str, Dict[str, int]]): Bin counts from T019.
        min_samples (int): Minimum samples required per bin.
        
    Returns:
        Dict[str, Any]: Strategy decision.
    """
    strategy = 'keep'
    bins_to_merge = []
    
    # Check for bins with insufficient samples
    for bin_label, stats in bin_counts.items():
        if stats['total'] < min_samples:
            bins_to_merge.append(bin_label)
    
    if bins_to_merge:
        # Attempt to merge with adjacent bins
        sorted_bins = sorted(bin_counts.keys(), key=lambda x: int(x) if x.isdigit() else 999)
        
        if len(sorted_bins) >= 2:
            # Merge the lowest bin with the next one
            strategy = 'merged'
            logging.info(f"Merging bins: {bins_to_merge}")
        else:
            strategy = 'deferred'
            logging.warning("Insufficient data for merging, deferring analysis.")
    
    return {
        'strategy': strategy,
        'bins_to_merge': bins_to_merge,
        'min_samples': min_samples
    }


def save_bin_config(
    config: Dict[str, Any],
    output_path: Union[str, Path]
) -> None:
    """
    Save bin configuration to a JSON file.
    
    Args:
        config (Dict[str, Any]): Bin configuration.
        output_path (Union[str, Path]): Path for the output file.
    """
    output_obj = Path(output_path) if isinstance(output_path, str) else output_path
    ensure_dir(output_obj.parent)
    
    with open(output_obj, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def main() -> None:
    """Main entry point for bin utils module."""
    pass


if __name__ == "__main__":
    main()
