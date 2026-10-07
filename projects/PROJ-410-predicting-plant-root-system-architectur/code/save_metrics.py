import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/save_metrics.log')
    ]
)
logger = logging.getLogger(__name__)

def load_all_model_results(metrics_dir: Path) -> pd.DataFrame:
    """
    Load all model metric CSV files from the metrics directory.
    Expects files like: null_model_metrics.csv, model_metrics_<condition>.csv
    """
    logger.info(f"Scanning directory: {metrics_dir}")
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")

    all_metrics = []
    csv_files = list(metrics_dir.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {metrics_dir}")
        return pd.DataFrame()

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            df['source_file'] = file_path.name
            all_metrics.append(df)
            logger.info(f"Loaded metrics from {file_path.name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            continue

    if not all_metrics:
        logger.warning("No valid metric files could be loaded.")
        return pd.DataFrame()

    combined_df = pd.concat(all_metrics, ignore_index=True)
    logger.info(f"Total combined metrics rows: {len(combined_df)}")
    return combined_df

def calculate_rankings(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate performance rankings per nutrient condition.
    Rankings are based on R² (higher is better), then MAE (lower is better).
    
    Columns expected: 'condition', 'model_type', 'r2_score', 'mae', 'cv_r2_mean'
    """
    if metrics_df.empty:
        logger.warning("Cannot calculate rankings on empty DataFrame.")
        return metrics_df

    # Ensure numeric types for ranking columns
    numeric_cols = ['r2_score', 'mae', 'cv_r2_mean']
    for col in numeric_cols:
        if col in metrics_df.columns:
            metrics_df[col] = pd.to_numeric(metrics_df[col], errors='coerce')

    # Define ranking logic per condition
    ranked_dfs = []
    
    if 'condition' not in metrics_df.columns:
        logger.error("Missing 'condition' column in metrics dataframe. Cannot rank per condition.")
        return metrics_df

    conditions = metrics_df['condition'].unique()
    logger.info(f"Calculating rankings for conditions: {conditions}")

    for condition in conditions:
        subset = metrics_df[metrics_df['condition'] == condition].copy()
        
        if subset.empty:
            continue

        # Sort by R2 (desc) then MAE (asc) to determine rank
        # We use a temporary sort to assign ranks
        # Higher R2 is better -> rank 1
        # Lower MAE is better -> rank 1
        
        # Primary sort: R2 descending
        # Secondary sort: MAE ascending
        subset = subset.sort_values(by=['r2_score', 'mae'], ascending=[False, True])
        
        # Assign ranks
        subset['performance_rank'] = range(1, len(subset) + 1)
        
        # Add condition metadata
        subset['rank_condition'] = condition
        
        ranked_dfs.append(subset)

    if not ranked_dfs:
        logger.warning("No conditions found to rank.")
        return metrics_df

    final_ranked_df = pd.concat(ranked_dfs, ignore_index=True)
    logger.info(f"Rankings calculated for {len(final_ranked_df)} entries.")
    return final_ranked_df

def save_metrics_ranking(ranked_df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the final ranked metrics to a CSV file.
    """
    ensure_directories([output_path.parent])
    
    if ranked_df.empty:
        logger.warning("Ranking DataFrame is empty. Saving empty file.")
        # Still save an empty file with headers if possible, or warn
        ranked_df.to_csv(output_path, index=False)
        return

    # Select relevant columns for the final output
    columns_to_save = [
        'condition', 'model_type', 'performance_rank', 
        'r2_score', 'mae', 'cv_r2_mean', 'source_file'
    ]
    
    # Filter columns that actually exist
    available_cols = [c for c in columns_to_save if c in ranked_df.columns]
    output_df = ranked_df[available_cols]
    
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved performance rankings to {output_path}")
    logger.info(f"Top 5 models:\n{output_df.nsmallest(5, 'performance_rank')}")

def main():
    parser = argparse.ArgumentParser(description="Save model metrics with performance rankings.")
    parser.add_argument(
        "--metrics_dir", 
        type=str, 
        default="data/processed",
        help="Directory containing model metric CSV files."
    )
    parser.add_argument(
        "--output_file", 
        type=str, 
        default="data/processed/model_metrics.csv",
        help="Path to save the ranked metrics CSV."
    )
    args = parser.parse_args()

    metrics_dir = Path(args.metrics_dir)
    output_path = Path(args.output_file)

    try:
        logger.info("Starting metrics aggregation and ranking process...")
        
        # Load all metrics
        all_metrics = load_all_model_results(metrics_dir)
        
        if all_metrics.empty:
            logger.error("No metrics found to process. Aborting.")
            sys.exit(1)

        # Calculate rankings
        ranked_metrics = calculate_rankings(all_metrics)

        # Save results
        save_metrics_ranking(ranked_metrics, output_path)

        logger.info("Process completed successfully.")
        
    except Exception as e:
        logger.error(f"Process failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()