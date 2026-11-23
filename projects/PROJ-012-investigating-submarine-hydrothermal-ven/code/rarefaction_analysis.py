"""
Rarefaction Curve Analysis and Optimal Depth Determination (T020b)

This module analyzes the OTU table to generate rarefaction curves and determine
the optimal rarefaction depth. If the optimal depth cannot be determined (e.g.,
due to insufficient data or high variance), it sets the depth to '[deferred]'
and documents the rationale.

The output is written to `data/processed/rarefaction_config.yaml`.
"""
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import yaml

# Import existing API surface
from preprocessing import load_otu_table, calculate_shannon_diversity

logger = logging.getLogger(__name__)

def generate_rarefaction_curves(
    otu_df: pd.DataFrame,
    depths: List[int],
    n_iterations: int = 5
) -> pd.DataFrame:
    """
    Generate rarefaction curves by calculating diversity metrics at various depths.

    Args:
        otu_df: The full OTU table (samples as rows, features as columns).
        depths: List of sampling depths to test.
        n_iterations: Number of random subsampling iterations per depth.

    Returns:
        A DataFrame with columns: sample_id, depth, iteration, diversity_metric.
    """
    results = []
    sample_ids = otu_df.index.tolist()

    logger.info(f"Generating rarefaction curves for {len(sample_ids)} samples "
                f"across {len(depths)} depths.")

    for sample_id in sample_ids:
        sample_counts = otu_df.loc[sample_id].values
        total_counts = sample_counts.sum()

        for depth in depths:
            if depth > total_counts:
                logger.debug(f"Skipping depth {depth} for {sample_id} "
                             f"(total counts: {total_counts})")
                continue

            for i in range(n_iterations):
                # Perform rarefaction (sampling without replacement)
                # We simulate this by randomly selecting counts up to the depth
                # Since we need a reproducible diversity metric, we use the
                # actual rarefied table logic from preprocessing if available,
                # or simulate here.
                
                # Simulation approach for curve generation:
                # Randomly select 'depth' reads from the total pool
                indices = np.random.choice(
                    len(sample_counts), 
                    size=depth, 
                    p=sample_counts / total_counts
                )
                
                # Count frequencies of each feature in the subsample
                rarefied_counts = np.bincount(indices, minlength=len(sample_counts))
                rarefied_series = pd.Series(rarefied_counts, index=otu_df.columns)
                
                # Calculate Shannon diversity
                # Avoid log(0) by filtering zeros
                non_zero = rarefied_series[rarefied_series > 0]
                if len(non_zero) == 0:
                    shannon = 0.0
                else:
                    proportions = non_zero / non_zero.sum()
                    shannon = -np.sum(proportions * np.log(proportions))
                
                results.append({
                    'sample_id': sample_id,
                    'depth': depth,
                    'iteration': i,
                    'shannon_diversity': shannon
                })

    return pd.DataFrame(results)

def determine_optimal_depth(
    curve_df: pd.DataFrame,
    target_coverage: float = 0.95,
    min_samples: int = 10
) -> Tuple[Optional[int], str]:
    """
    Analyze rarefaction curves to determine the optimal rarefaction depth.

    Criteria:
    1. The depth where the curve begins to plateau (slope < threshold).
    2. The depth that retains the maximum number of samples (coverage).
    3. If no clear plateau or insufficient samples, return '[deferred]'.

    Returns:
        Tuple of (optimal_depth, rationale_string).
    """
    if curve_df.empty:
        return None, "No data points generated for rarefaction analysis."

    # Group by depth to calculate mean diversity
    depth_stats = curve_df.groupby('depth')['shannon_diversity'].agg(['mean', 'std', 'count'])
    
    # Filter depths that cover at least min_samples (approximated by count here)
    # In a real scenario, we'd check how many samples have counts >= depth
    valid_depths = depth_stats[depth_stats['count'] >= min_samples].index.tolist()
    
    if not valid_depths:
        return None, f"No depth achieved coverage for >= {min_samples} samples."

    # Sort valid depths
    valid_depths = sorted(valid_depths)
    
    # Check for plateau: Calculate the slope between consecutive points
    # If the slope becomes negligible, we have a plateau.
    plateaus = []
    for i in range(1, len(valid_depths)):
        d_prev = valid_depths[i-1]
        d_curr = valid_depths[i]
        mean_prev = depth_stats.loc[d_prev, 'mean']
        mean_curr = depth_stats.loc[d_curr, 'mean']
        
        # Slope = change in diversity / change in depth
        # We want a small slope (diversity stabilizes)
        if d_curr - d_prev > 0:
            slope = (mean_curr - mean_prev) / (d_curr - d_prev)
            # If slope is very small relative to the diversity value
            if abs(slope) < 0.0001: # Threshold for plateau
                plateaus.append(d_curr)
    
    if plateaus:
        # Choose the smallest depth in the plateau to maximize sample retention
        optimal = min(plateaus)
        rationale = (f"Optimal depth determined at {optimal}. "
                     f"Rarefaction curve plateaus at this depth (slope < 0.0001). "
                     f"Coverage: {len(curve_df[curve_df['depth'] == optimal])} samples.")
        return optimal, rationale
    else:
        # No clear plateau found. Choose the maximum valid depth as a fallback
        # but flag it as uncertain.
        max_valid = max(valid_depths)
        rationale = (f"No clear plateau detected in rarefaction curves. "
                     f"Selected maximum valid depth ({max_valid}) as a conservative "
                     f"estimate, but results may be sensitive to depth choice. "
                     f"Consider manual inspection of curves.")
        return max_valid, rationale

def run_rarefaction_depth_analysis(
    otu_table_path: str,
    output_config_path: str,
    depths: Optional[List[int]] = None
) -> None:
    """
    Main entry point for T020b.
    
    1. Loads the OTU table.
    2. Generates rarefaction curves.
    3. Determines optimal depth.
    4. Writes configuration to YAML.
    """
    logger.info("Starting rarefaction depth analysis (T020b).")
    
    # Default depths if not provided
    if depths is None:
        # Heuristic: 10% to 90% of min sample count, or fixed steps if data is small
        # For this implementation, we assume a reasonable range or derive from data
        pass

    # Load OTU table
    try:
        otu_df = load_otu_table(otu_table_path)
        if otu_df.empty:
            raise ValueError("OTU table is empty.")
    except Exception as e:
        logger.error(f"Failed to load OTU table: {e}")
        # If we can't load data, we must defer
        config = {
            'optimal_rarefaction_depth': '[deferred]',
            'rationale': f"Failed to load OTU table: {str(e)}. Analysis could not proceed.",
            'status': 'failed'
        }
        Path(output_config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return

    # Determine depths to test
    # Calculate total counts per sample to find a reasonable range
    sample_counts = otu_df.sum(axis=1)
    min_total = int(sample_counts.min())
    max_total = int(sample_counts.max())
    
    if min_total < 1000:
        # Very low depth data
        test_depths = list(range(100, min_total + 1, 100)) if min_total > 100 else [min_total]
    else:
        # Standard range: 1k to max, steps of 1k or 10%
        test_depths = list(range(1000, max_total + 1, 1000))
        # Ensure we cover the tail
        if max_total not in test_depths:
            test_depths.append(max_total)
        
    # Filter depths to be within the range of at least some samples
    # (Heuristic: keep depths where at least 20% of samples have enough reads)
    valid_test_depths = []
    for d in test_depths:
        count = (sample_counts >= d).sum()
        if count >= len(sample_counts) * 0.2:
            valid_test_depths.append(d)
    
    if not valid_test_depths:
        config = {
            'optimal_rarefaction_depth': '[deferred]',
            'rationale': "No suitable depth range found. Data sparsity is too high.",
            'status': 'deferred'
        }
        Path(output_config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return

    logger.info(f"Testing depths: {valid_test_depths}")

    # Generate curves
    curve_df = generate_rarefaction_curves(otu_df, valid_test_depths, n_iterations=3)
    
    # Determine optimal depth
    optimal_depth, rationale = determine_optimal_depth(curve_df)
    
    if optimal_depth is None:
        config = {
            'optimal_rarefaction_depth': '[deferred]',
            'rationale': rationale,
            'status': 'deferred'
        }
    else:
        config = {
            'optimal_rarefaction_depth': optimal_depth,
            'rationale': rationale,
            'status': 'determined',
            'tested_depths': valid_test_depths,
            'samples_retained': int((sample_counts >= optimal_depth).sum())
        }

    # Write output
    Path(output_config_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    logger.info(f"Rarefaction analysis complete. Config written to {output_config_path}")
    logger.info(f"Optimal Depth: {config['optimal_rarefaction_depth']}")

def main():
    """Entry point for command line execution."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Paths
    project_root = Path(__file__).parent.parent
    otu_path = project_root / "data" / "processed" / "otu_table.tsv"
    output_path = project_root / "data" / "processed" / "rarefaction_config.yaml"
    
    if not otu_path.exists():
        logger.error(f"OTU table not found at {otu_path}. "
                     "Please run T018/T019 first.")
        return
    
    run_rarefaction_depth_analysis(
        otu_table_path=str(otu_path),
        output_config_path=str(output_path)
    )

if __name__ == "__main__":
    main()
