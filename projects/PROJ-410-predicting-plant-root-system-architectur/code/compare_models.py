import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
import numpy as np

# Ensure we can import from the project root if run as a script
# (though typically this is imported as a module or run via the project's entry point)
# The prompt indicates this file is at code/compare_models.py

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_null_metrics(filepath: str = "data/processed/null_model_metrics.csv") -> pd.DataFrame:
    """
    Load null model metrics from the specified CSV file.

    Args:
        filepath: Path to the null model metrics CSV.

    Returns:
        DataFrame containing null model metrics.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no rows.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Null model metrics file not found at {filepath}")

    df = pd.read_csv(filepath)

    if df.empty:
        raise ValueError(f"Null model metrics file at {filepath} is empty.")

    logger.info(f"Loaded {len(df)} null model metric rows from {filepath}")
    return df

def load_trained_metrics(filepath: str = "data/processed/model_metrics.csv") -> pd.DataFrame:
    """
    Load trained model metrics from the specified CSV file.

    Args:
        filepath: Path to the trained model metrics CSV.

    Returns:
        DataFrame containing trained model metrics.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no rows.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Trained model metrics file not found at {filepath}")

    df = pd.read_csv(filepath)

    if df.empty:
        raise ValueError(f"Trained model metrics file at {filepath} is empty.")

    logger.info(f"Loaded {len(df)} trained model metric rows from {filepath}")
    return df

def compare_models(null_df: pd.DataFrame, trained_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare trained models against the null model baseline.

    This function merges null and trained metrics by 'nutrient_condition' and 'metric_name'
    (or similar identifiers) to calculate the improvement (e.g., delta R²).

    Args:
        null_df: DataFrame of null model metrics.
        trained_df: DataFrame of trained model metrics.

    Returns:
        DataFrame containing the comparison results (merged metrics with deltas).
    """
    # Ensure we are comparing the right columns.
    # Expected columns in null_df: 'nutrient_condition', 'metric_name', 'value' (or 'score')
    # Expected columns in trained_df: 'nutrient_condition', 'model_name', 'metric_name', 'value' (or 'score')

    # Normalize column names to be safe
    null_cols = null_df.columns.tolist()
    trained_cols = trained_df.columns.tolist()

    # Determine the score column name (could be 'value', 'score', 'r2', etc.)
    score_col = None
    for candidate in ['value', 'score', 'r2', 'R2', 'mae', 'MAE']:
        if candidate in null_cols:
            score_col = candidate
            break
    
    if score_col is None:
        # Fallback to the last numeric column if not found
        numeric_cols = null_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            score_col = numeric_cols[-1]
        else:
            raise ValueError("Could not identify a score/value column in null model metrics.")

    # Pivot null_df to have one row per condition, with metric names as columns
    # We expect the null model to be consistent across conditions or specific per condition.
    # Assuming structure: nutrient_condition, metric_name, value
    if 'nutrient_condition' in null_cols and 'metric_name' in null_cols:
        null_pivot = null_df.pivot_table(
            index='nutrient_condition', 
            columns='metric_name', 
            values=score_col, 
            aggfunc='first' # In case of duplicates, take first
        ).reset_index()
        null_pivot.columns = ['nutrient_condition'] + [f'null_{col}' for col in null_pivot.columns[1:]]
    else:
        # Fallback if structure is different: assume single row or global null
        logger.warning("Null metrics do not have expected 'nutrient_condition'/'metric_name' structure. Attempting global comparison.")
        null_pivot = null_df.copy()
        if 'nutrient_condition' not in null_pivot.columns:
            null_pivot['nutrient_condition'] = 'global'

    # Pivot trained_df similarly
    if 'nutrient_condition' in trained_cols and 'metric_name' in trained_cols and 'model_name' in trained_cols:
        # We want to keep model_name as a column, pivot metric_name
        # Group by condition and model, then pivot metrics
        trained_pivot = trained_df.pivot_table(
            index=['nutrient_condition', 'model_name'],
            columns='metric_name',
            values=score_col,
            aggfunc='first'
        ).reset_index()
        
        # Flatten column names
        trained_pivot.columns = ['nutrient_condition', 'model_name'] + [f'trained_{col}' for col in trained_pivot.columns[2:]]
    else:
        raise ValueError("Trained metrics do not have expected structure ('nutrient_condition', 'model_name', 'metric_name').")

    # Merge
    # Left join on nutrient_condition. If null is global, we might need to merge differently,
    # but assuming per-condition nulls based on T027 description.
    comparison = pd.merge(trained_pivot, null_pivot, on='nutrient_condition', how='left')

    # Calculate deltas for common metrics (e.g., R2, MAE)
    # Identify columns that start with 'trained_' and 'null_'
    trained_metrics = [c for c in comparison.columns if c.startswith('trained_')]
    null_metrics = [c for c in comparison.columns if c.startswith('null_')]

    # Map trained metric to null metric (remove prefixes)
    metric_map = {}
    for tm in trained_metrics:
        base_name = tm.replace('trained_', '')
        nm = f'null_{base_name}'
        if nm in null_metrics:
            metric_map[tm] = nm

    for tm, nm in metric_map.items():
        base = tm.replace('trained_', '')
        delta_col = f'delta_{base}'
        # Calculate improvement: Trained - Null (for R2, higher is better; for MAE, lower is better)
        # For R2: delta = R2_trained - R2_null (positive is good)
        # For MAE: delta = MAE_null - MAE_trained (positive is good, since we want error to decrease)
        # Let's standardize on "Improvement" where positive is better.
        # If metric is R2: Improvement = Trained - Null
        # If metric is MAE: Improvement = Null - Trained
        
        if 'mae' in base.lower() or 'error' in base.lower():
            comparison[delta_col] = comparison[nm] - comparison[tm]
        else:
            comparison[delta_col] = comparison[tm] - comparison[nm]

    logger.info(f"Generated comparison dataframe with {len(comparison)} rows.")
    return comparison

def save_comparison_results(comparison_df: pd.DataFrame, output_path: str = "data/processed/model_comparison.csv"):
    """
    Save the comparison results to a CSV file.

    Args:
        comparison_df: DataFrame containing the comparison results.
        output_path: Path to save the CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    comparison_df.to_csv(output_path, index=False)
    logger.info(f"Saved comparison results to {output_path}")

def main(args=None):
    parser = argparse.ArgumentParser(description="Compare trained models against null model baseline.")
    parser.add_argument(
        "--null-path", 
        type=str, 
        default="data/processed/null_model_metrics.csv",
        help="Path to null model metrics CSV."
    )
    parser.add_argument(
        "--trained-path", 
        type=str, 
        default="data/processed/model_metrics.csv",
        help="Path to trained model metrics CSV."
    )
    parser.add_argument(
        "--output-path", 
        type=str, 
        default="data/processed/model_comparison.csv",
        help="Path to save comparison results CSV."
    )
    
    parsed_args = parser.parse_args(args)

    try:
        logger.info("Loading null model metrics...")
        null_df = load_null_metrics(parsed_args.null_path)
        
        logger.info("Loading trained model metrics...")
        trained_df = load_trained_metrics(parsed_args.trained_path)
        
        logger.info("Comparing models...")
        comparison_df = compare_models(null_df, trained_df)
        
        logger.info("Saving comparison results...")
        save_comparison_results(comparison_df, parsed_args.output_path)
        
        logger.info("Comparison complete.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during comparison: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())