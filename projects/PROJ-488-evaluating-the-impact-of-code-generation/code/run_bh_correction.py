"""
Benjamini-Hochberg multiple comparison correction implementation.

This module applies the Benjamini-Hochberg procedure to adjust p-values
from the Mann-Whitney U tests performed in statistical_analysis.py.
The corrected p-values are stored in CSV format in data/metrics/.
"""
import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Import from sibling modules using the provided API surface
from logging_config import get_logger
from state_tracker import update_state_with_artifact, load_state_file, save_state_file

# Configure logger
logger = get_logger("run_bh_correction")

def load_metrics_data(metrics_dir: Path) -> pd.DataFrame:
    """
    Load all metric CSV files from the metrics directory and combine them.
    
    Expects files like:
    - data/metrics/metric_cyclomatic.csv
    - data/metrics/metric_maintainability.csv
    - etc.
    
    Each file should have columns: group, metric_value, p_value (from Mann-Whitney U)
    """
    all_metrics = []
    metric_files = list(metrics_dir.glob("metric_*.csv"))
    
    if not metric_files:
        raise FileNotFoundError(f"No metric CSV files found in {metrics_dir}")
    
    for file_path in metric_files:
        try:
            df = pd.read_csv(file_path)
            # Extract metric name from filename
            metric_name = file_path.stem.replace("metric_", "")
            df["metric_name"] = metric_name
            all_metrics.append(df)
            logger.info(f"Loaded {len(df)} rows from {file_path.name}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise
    
    if not all_metrics:
        raise ValueError("No valid metric data loaded")
    
    combined_df = pd.concat(all_metrics, ignore_index=True)
    return combined_df

def run_bh_correction(p_values: list) -> list:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    The Benjamini-Hochberg procedure controls the False Discovery Rate (FDR).
    Steps:
    1. Sort p-values in ascending order
    2. For each p-value at rank i (1-indexed), compute adjusted p-value:
       p_adj[i] = p[i] * n / i
    3. Ensure monotonicity: p_adj[i] = min(p_adj[i], p_adj[i+1])
    4. Clip to [0, 1]
    
    Args:
        p_values: List of raw p-values from statistical tests
        
    Returns:
        List of adjusted p-values in the same order as input
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    # Compute BH adjusted p-values
    # p_adj[i] = p[i] * n / (i + 1) where i is 0-indexed rank
    ranks = np.arange(1, n + 1)
    adjusted_sorted = sorted_p_values * n / ranks
    
    # Ensure monotonicity (cumulative minimum from the end)
    adjusted_sorted = np.minimum.accumulate(adjusted_sorted[::-1])[::-1]
    
    # Clip to [0, 1]
    adjusted_sorted = np.clip(adjusted_sorted, 0, 1)
    
    # Map back to original order
    adjusted_p_values = np.empty(n)
    adjusted_p_values[sorted_indices] = adjusted_sorted
    
    return adjusted_p_values.tolist()

def run_bh_correction_pipeline(metrics_dir: Path, output_dir: Path, state_file_path: Path) -> dict:
    """
    Run the full Benjamini-Hochberg correction pipeline.
    
    1. Load all metric data
    2. Group by metric name
    3. Apply BH correction to p-values for each metric
    4. Save results to CSV files
    5. Update state file with artifact information
    
    Args:
        metrics_dir: Path to directory containing metric CSV files
        output_dir: Path to directory where corrected results will be saved
        state_file_path: Path to the project state YAML file
        
    Returns:
        Dictionary containing summary of results
    """
    logger.info("Starting Benjamini-Hochberg correction pipeline")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all metric data
    combined_df = load_metrics_data(metrics_dir)
    
    # Group by metric name and apply correction
    results_summary = {}
    
    for metric_name, group_df in combined_df.groupby("metric_name"):
        logger.info(f"Processing metric: {metric_name}")
        
        # Get p-values for this metric
        p_values = group_df["p_value"].tolist()
        
        # Apply BH correction
        adjusted_p_values = run_bh_correction(p_values)
        
        # Create result dataframe
        result_df = group_df.copy()
        result_df["adjusted_p_value"] = adjusted_p_values
        result_df["correction_method"] = "Benjamini-Hochberg"
        
        # Save to CSV
        output_file = output_dir / f"metric_{metric_name}_corrected.csv"
        result_df.to_csv(output_file, index=False)
        logger.info(f"Saved corrected results to {output_file}")
        
        # Record summary
        significant_count = sum(1 for p in adjusted_p_values if p < 0.05)
        results_summary[metric_name] = {
            "raw_p_values": p_values,
            "adjusted_p_values": adjusted_p_values,
            "significant_at_0.05": significant_count,
            "total_tests": len(p_values),
            "output_file": str(output_file)
        }
    
    # Save summary JSON
    summary_file = output_dir / "bh_correction_summary.json"
    with open(summary_file, "w") as f:
        json.dump(results_summary, f, indent=2, default=str)
    logger.info(f"Saved summary to {summary_file}")
    
    # Update state file
    try:
        state = load_state_file(state_file_path)
        update_state_with_artifact(
            state,
            artifact_type="statistical_correction",
            artifact_path=str(output_dir),
            description="Benjamini-Hochberg corrected p-values for all metrics"
        )
        save_state_file(state_file_path, state)
        logger.info("Updated state file with BH correction results")
    except Exception as e:
        logger.warning(f"Could not update state file: {e}")
    
    return results_summary

def main():
    """Main entry point for the BH correction pipeline."""
    # Define paths
    project_root = Path(__file__).parent.parent
    metrics_dir = project_root / "data" / "metrics"
    output_dir = project_root / "data" / "metrics"
    state_file_path = project_root / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"
    
    # Check if metrics directory exists
    if not metrics_dir.exists():
        logger.error(f"Metrics directory not found: {metrics_dir}")
        sys.exit(1)
    
    # Check if state file exists
    if not state_file_path.exists():
        logger.error(f"State file not found: {state_file_path}")
        sys.exit(1)
    
    try:
        results = run_bh_correction_pipeline(
            metrics_dir=metrics_dir,
            output_dir=output_dir,
            state_file_path=state_file_path
        )
        
        logger.info("Benjamini-Hochberg correction completed successfully")
        logger.info(f"Processed {len(results)} metrics")
        
        # Print summary
        for metric_name, summary in results.items():
            logger.info(f"  {metric_name}: {summary['significant_at_0.05']}/{summary['total_tests']} significant (p < 0.05)")
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
