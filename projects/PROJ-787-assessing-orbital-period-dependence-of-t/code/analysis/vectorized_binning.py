"""
Vectorized implementation of binning operations for performance optimization.
Replaces iterative pandas operations with numpy vectorized operations.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_log_bins_vectorized(
    min_period: float,
    max_period: float,
    n_bins: int
) -> np.ndarray:
    """
    Create log-spaced bins using numpy vectorized operations.
    
    Args:
        min_period: Minimum period in days
        max_period: Maximum period in days
        n_bins: Number of bins to create
        
    Returns:
        numpy array of bin edges
    """
    logger.info(f"Creating {n_bins} log-spaced bins from {min_period} to {max_period} days")
    log_min = np.log10(min_period)
    log_max = np.log10(max_period)
    log_edges = np.linspace(log_min, log_max, n_bins + 1)
    edges = np.power(10, log_edges)
    return edges

def assign_bin_index_vectorized(
    periods: np.ndarray,
    bin_edges: np.ndarray
) -> np.ndarray:
    """
    Assign bin indices to periods using numpy digitize (vectorized).
    
    Args:
        periods: Array of orbital periods
        bin_edges: Array of bin edges
        
    Returns:
        Array of bin indices (0-indexed)
    """
    # np.digitize returns 1-indexed bins, subtract 1 for 0-indexed
    bin_indices = np.digitize(periods, bin_edges) - 1
    # Clip to valid range (in case of floating point edge cases)
    bin_indices = np.clip(bin_indices, 0, len(bin_edges) - 2)
    return bin_indices

def merge_small_bins_vectorized(
    bin_counts: np.ndarray,
    bin_edges: np.ndarray,
    min_count: int = 30
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Merge bins with fewer than min_count planets with adjacent bins.
    Uses vectorized operations to identify and merge small bins.
    
    Args:
        bin_counts: Number of planets in each bin
        bin_edges: Bin edges array
        min_count: Minimum number of planets required per bin
        
    Returns:
        Tuple of (merged_bin_edges, merged_bin_indices, merge_map)
    """
    logger.info(f"Merging bins with < {min_count} planets")
    
    n_bins = len(bin_counts)
    if n_bins == 0:
        return bin_edges, np.array([]), np.array([])
    
    # Identify bins that need merging
    needs_merge = bin_counts < min_count
    
    if not np.any(needs_merge):
        logger.info("No bins need merging")
        return bin_edges, np.arange(n_bins), np.arange(n_bins)
    
    # Build merge map: for each bin, which final bin index it maps to
    merge_map = np.arange(n_bins)
    current_final_idx = 0
    i = 0
    
    while i < n_bins:
        if needs_merge[i]:
            # Find adjacent bin with closest period (prefer right, then left)
            # For simplicity, merge with right neighbor if exists, else left
            if i < n_bins - 1 and not needs_merge[i + 1]:
                # Merge with right
                merge_map[i] = merge_map[i + 1]
            elif i > 0 and not needs_merge[i - 1]:
                # Merge with left
                merge_map[i] = merge_map[i - 1]
            else:
                # Both neighbors need merging or boundary case
                # Merge with the one that has more planets
                if i < n_bins - 1:
                    merge_map[i] = merge_map[i + 1]
                elif i > 0:
                    merge_map[i] = merge_map[i - 1]
        else:
            current_final_idx += 1
        i += 1
    
    # Recalculate merge_map to be contiguous
    unique_final = np.unique(merge_map)
    final_map = np.zeros_like(merge_map)
    for idx, val in enumerate(unique_final):
        final_map[merge_map == val] = idx
    
    # Create merged bin edges by removing edges of merged bins
    # Keep edges where the bin index changes
    edge_keep = np.concatenate([[True], final_map[:-1] != final_map[1:], [True]])
    merged_edges = bin_edges[edge_keep]
    
    logger.info(f"Merged {n_bins} bins into {len(merged_edges) - 1} bins")
    
    return merged_edges, final_map, merge_map

def bin_planets_vectorized(
    df: pd.DataFrame,
    period_col: str = 'period',
    min_bins: int = 10,
    max_bins: int = 50,
    min_count_per_bin: int = 30
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Vectorized binning of planets by orbital period.
    
    Args:
        df: DataFrame containing planet data
        period_col: Name of the period column
        min_bins: Minimum number of initial bins
        max_bins: Maximum number of initial bins
        min_count_per_bin: Minimum planets per bin after merging
        
    Returns:
        Tuple of (binned_df, bin_edges)
    """
    logger.info(f"Starting vectorized binning with {len(df)} planets")
    
    periods = df[period_col].values
    min_period = periods.min()
    max_period = periods.max()
    
    # Adaptive bin count based on data size
    n_initial_bins = min(max_bins, max(min_bins, int(np.sqrt(len(df)))))
    
    # Create initial bins
    bin_edges = create_log_bins_vectorized(min_period, max_period, n_initial_bins)
    
    # Assign initial bins
    initial_bin_indices = assign_bin_index_vectorized(periods, bin_edges)
    
    # Count planets per bin
    bin_counts = np.bincount(initial_bin_indices, minlength=len(bin_edges) - 1)
    
    # Merge small bins
    merged_edges, final_indices, _ = merge_small_bins_vectorized(
        bin_counts, bin_edges, min_count_per_bin
    )
    
    # Re-assign bins using merged edges
    final_bin_indices = assign_bin_index_vectorized(periods, merged_edges)
    
    # Add bin information to DataFrame
    df_out = df.copy()
    df_out['bin_index'] = final_bin_indices
    df_out['bin_edge_low'] = merged_edges[final_bin_indices]
    df_out['bin_edge_high'] = merged_edges[final_bin_indices + 1]
    df_out['bin_center'] = np.sqrt(df_out['bin_edge_low'] * df_out['bin_edge_high'])
    
    logger.info(f"Final binning: {len(merged_edges) - 1} bins")
    
    return df_out, merged_edges

def save_binned_data_vectorized(
    df: pd.DataFrame,
    bin_edges: np.ndarray,
    output_path: str
) -> None:
    """
    Save binned data to CSV with metadata.
    
    Args:
        df: DataFrame with bin information
        bin_edges: Final bin edges
        output_path: Output file path
    """
    logger.info(f"Saving binned data to {output_path}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save data
    df.to_csv(output_path, index=False)
    
    # Save bin metadata
    metadata_path = str(output_path).replace('.csv', '_metadata.json')
    metadata = {
        'n_bins': len(bin_edges) - 1,
        'bin_edges': bin_edges.tolist(),
        'min_period': bin_edges[0],
        'max_period': bin_edges[-1]
    }
    
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved {len(df)} planets into {len(bin_edges) - 1} bins")

def main() -> None:
    """
    Main entry point for vectorized binning.
    Reads from data/processed/filtered_planets.csv and outputs to data/processed/binned_planets.csv
    """
    logger.info("Starting vectorized binning pipeline")
    
    # Input/Output paths
    input_path = Path("data/processed/filtered_planets.csv")
    output_path = Path("data/processed/binned_planets.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'period' not in df.columns:
        logger.error("Missing 'period' column in input data")
        sys.exit(1)
    
    # Filter out invalid periods
    df = df[df['period'] > 0].copy()
    
    if len(df) == 0:
        logger.error("No valid planets with positive periods")
        sys.exit(1)
    
    # Perform vectorized binning
    binned_df, bin_edges = bin_planets_vectorized(
        df,
        period_col='period',
        min_bins=10,
        max_bins=50,
        min_count_per_bin=30
    )
    
    # Save results
    save_binned_data_vectorized(binned_df, bin_edges, str(output_path))
    
    logger.info("Vectorized binning completed successfully")

if __name__ == "__main__":
    main()
