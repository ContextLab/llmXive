import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

from analysis.stability_check import load_raw_logs
from analysis.stats import load_latency_data, compute_block_averages
from analysis.viz import load_stability_metrics, generate_pareto_final

logger = logging.getLogger(__name__)

def aggregate_results() -> pd.DataFrame:
    """
    Aggregates latency and stability data into a single DataFrame.
    
    Reads:
      - data/intermediates/raw_logs/*.jsonl (latency)
      - data/results/stability_metrics.csv (stability)
    
    Returns:
      DataFrame with columns: config_id, kernel_type, median_latency, 
      p95_latency, l2_error, max_diff, status, is_stable
    """
    raw_logs_path = Path("data/intermediates/raw_logs")
    stability_path = Path("data/results/stability_metrics.csv")
    
    if not raw_logs_path.exists() or not list(raw_logs_path.glob("*.jsonl")):
        raise FileNotFoundError(f"Raw logs not found in {raw_logs_path}. Run T015 first.")
    if not stability_path.exists():
        raise FileNotFoundError(f"Stability metrics not found at {stability_path}. Run T023 first.")
    
    # Load stability metrics
    stability_df = pd.read_csv(stability_path)
    stability_df['config_id'] = stability_df['config_id'].astype(str)
    
    # Load latency data from raw logs
    latency_data = []
    for log_file in raw_logs_path.glob("*.jsonl"):
        try:
            df = load_latency_data(log_file)
            if df is not None and not df.empty:
                latency_data.append(df)
        except Exception as e:
            logger.warning(f"Could not load {log_file}: {e}")
    
    if not latency_data:
        raise RuntimeError("No valid latency data found in raw logs.")
    
    latency_df = pd.concat(latency_data, ignore_index=True)
    latency_df['config_id'] = latency_df['config_id'].astype(str)
    
    # Merge on config_id
    merged = pd.merge(
        latency_df,
        stability_df[['config_id', 'kernel_type', 'l2_error', 'max_diff', 'status']],
        on=['config_id', 'kernel_type'],
        how='inner'
    )
    
    # Compute is_stable flag
    merged['is_stable'] = merged['status'] == 'stable'
    
    # Ensure numeric types
    numeric_cols = ['median_latency', 'p95_latency', 'l2_error', 'max_diff']
    for col in numeric_cols:
        merged[col] = pd.to_numeric(merged[col], errors='coerce')
    
    logger.info(f"Aggregated {len(merged)} rows into aggregated.csv")
    return merged

def generate_final_pareto(agg_df: pd.DataFrame, output_path: Optional[str] = None):
    """
    Generates the final Pareto frontier plot and saves the aggregated CSV.
    
    Args:
        agg_df: The aggregated DataFrame from aggregate_results()
        output_path: Optional path for the aggregated CSV. Defaults to data/results/aggregated.csv
    """
    if output_path is None:
        output_path = "data/results/aggregated.csv"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save aggregated CSV
    agg_df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated results to {output_path}")
    
    # Generate Pareto Final Plot
    # Filter for stable configurations only (error <= 1e-5)
    stable_df = agg_df[agg_df['is_stable'] == True]
    
    if stable_df.empty:
        logger.warning("No stable configurations found. Skipping Pareto Final plot.")
        return
    
    plot_path = Path("data/results/pareto_frontier_final.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    
    generate_pareto_final(stable_df, str(plot_path))
    logger.info(f"Saved final Pareto frontier to {plot_path}")

def main():
    """Main entry point for T032."""
    setup_logger = logging.getLogger(__name__)
    setup_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    setup_logger.addHandler(handler)
    
    try:
        logger.info("Starting T032: Aggregation and Final Pareto Generation")
        
        # Step 1: Aggregate results
        agg_df = aggregate_results()
        
        # Step 2: Generate outputs
        generate_final_pareto(agg_df)
        
        logger.info("T032 completed successfully.")
        
    except Exception as e:
        logger.error(f"T032 failed: {e}")
        raise

if __name__ == "__main__":
    main()
