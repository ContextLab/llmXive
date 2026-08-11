import logging
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
from config import get_config, ensure_directories_exist

def load_pair_metrics(input_path: str) -> pd.DataFrame:
    """
    Load pair-level metrics from a parquet file.
    
    Args:
        input_path: Path to the parquet file containing pair metrics.
        
    Returns:
        DataFrame with pair metrics.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Pair metrics file not found: {input_path}")
    
    try:
        df = pd.read_parquet(input_path)
        logging.info(f"Loaded {len(df)} pair metrics from {input_path}")
        return df
    except Exception as e:
        logging.error(f"Failed to load pair metrics: {e}")
        raise

def aggregate_to_project_level(pair_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate pair-level metrics to project-level metrics using median variance.
    
    Per FR-010: Use median of response_time_variance for all pairs in a project.
    
    Args:
        pair_metrics: DataFrame with columns: project_id, pair_id, response_time_variance, mean_delay
        
    Returns:
        DataFrame with project-level metrics: project_id, median_variance, mean_delay, pair_count
    """
    if pair_metrics.empty:
        logging.warning("Empty pair metrics provided for aggregation.")
        return pd.DataFrame(columns=["project_id", "median_variance", "mean_delay", "pair_count"])
    
    # Ensure required columns exist
    required_cols = ["project_id", "response_time_variance", "mean_delay"]
    missing = [c for c in required_cols if c not in pair_metrics.columns]
    if missing:
        raise ValueError(f"Missing required columns in pair metrics: {missing}")
    
    # Group by project_id and aggregate
    # median_variance: median of response_time_variance
    # mean_delay: mean of mean_delay (or median? spec says "include mean_delay as well", usually implies aggregating it too)
    # pair_count: count of pairs
    project_metrics = pair_metrics.groupby("project_id").agg(
        median_variance=("response_time_variance", "median"),
        mean_delay=("mean_delay", "mean"),
        pair_count=("pair_id", "count")
    ).reset_index()
    
    logging.info(f"Aggregated metrics for {len(project_metrics)} projects.")
    return project_metrics

def run_aggregation_pipeline(pair_metrics_path: str, output_path: str) -> None:
    """
    Run the full aggregation pipeline: load pair metrics, aggregate to project level, save.
    
    Args:
        pair_metrics_path: Path to input pair metrics parquet file.
        output_path: Path to output project metrics CSV file.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    ensure_directories_exist(output_dir)
    
    # Load data
    pair_metrics = load_pair_metrics(pair_metrics_path)
    
    # Aggregate
    project_metrics = aggregate_to_project_level(pair_metrics)
    
    # Save
    project_metrics.to_csv(output_path, index=False)
    logging.info(f"Project metrics saved to {output_path}")

def main():
    """Main entry point for the script."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    config = get_config()
    pair_metrics_path = Path(config.get("derived_dir", "data/derived")) / "timestamp_features.parquet"
    output_path = Path(config.get("derived_dir", "data/derived")) / "project_metrics.csv"
    
    # Allow command line overrides
    if len(sys.argv) > 1:
        pair_metrics_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    run_aggregation_pipeline(str(pair_metrics_path), str(output_path))

if __name__ == "__main__":
    main()
