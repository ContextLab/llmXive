import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Import from existing API surface
from config import ensure_directories
from evaluate import load_model, load_split_data, compute_cv_scores, evaluate_model_cv, run_cv_for_all_models
from compare_models import load_null_metrics, load_trained_metrics, compare_models, save_comparison_results

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_all_model_results(processed_dir: Path) -> pd.DataFrame:
    """
    Loads the trained model metrics (from T035 output) and null model metrics.
    Merges them to create a comprehensive ranking dataframe.
    
    Expected inputs based on previous tasks:
    - data/processed/model_scores_cv.csv (output from T035/evaluate.py run_cv_for_all_models)
    - data/processed/null_model_metrics.csv (output from T027)
    """
    cv_metrics_path = processed_dir / "model_scores_cv.csv"
    null_metrics_path = processed_dir / "null_model_metrics.csv"

    if not cv_metrics_path.exists():
        raise FileNotFoundError(f"Trained model metrics not found at {cv_metrics_path}. "
                                "Please run T035 (evaluate.py) first.")
    
    df_cv = pd.read_csv(cv_metrics_path)
    
    # Ensure required columns exist for ranking
    required_cols = ['nutrient_condition', 'model_type', 'r2_mean', 'mae_mean']
    for col in required_cols:
        if col not in df_cv.columns:
            raise ValueError(f"Column '{col}' missing in {cv_metrics_path}. "
                             "Check T035 implementation.")

    df_null = None
    if null_metrics_path.exists():
        df_null = pd.read_csv(null_metrics_path)
        logger.info(f"Loaded null model metrics from {null_metrics_path}")
    else:
        logger.warning(f"Null model metrics not found at {null_metrics_path}. "
                       "Proceeding without baseline comparison.")

    return df_cv, df_null

def calculate_rankings(df_cv: pd.DataFrame, df_null: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculates performance rankings per nutrient condition.
    Adds columns: 'rank_r2', 'rank_mae', 'beats_null' (if null data exists).
    """
    # Sort by condition, then by R2 descending (higher is better)
    # If R2 is equal, use MAE ascending (lower is better)
    df_sorted = df_cv.sort_values(
        by=['nutrient_condition', 'r2_mean', 'mae_mean'], 
        ascending=[True, False, True]
    )

    # Calculate rank within each condition
    # rank='dense' or 'min' works, but we want 1 to be best
    df_sorted['rank_r2'] = df_sorted.groupby('nutrient_condition')['r2_mean'].rank(ascending=False, method='min').astype(int)
    df_sorted['rank_mae'] = df_sorted.groupby('nutrient_condition')['mae_mean'].rank(ascending=True, method='min').astype(int)

    # Determine if model beats the null model
    if df_null is not None and not df_null.empty:
        # Merge null metrics on condition
        # Assuming null metrics has columns: ['nutrient_condition', 'r2_mean', 'model_type']
        # We need to align the null R2 for each condition
        null_r2_map = df_null.set_index('nutrient_condition')['r2_mean'].to_dict()
        
        df_sorted['null_r2'] = df_sorted['nutrient_condition'].map(null_r2_map)
        df_sorted['beats_null'] = df_sorted['r2_mean'] > df_sorted['null_r2']
        df_sorted['r2_improvement'] = df_sorted['r2_mean'] - df_sorted['null_r2']
    else:
        df_sorted['beats_null'] = None
        df_sorted['r2_improvement'] = None

    return df_sorted

def save_metrics_ranking(df_ranked: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the final ranked metrics to data/processed/model_metrics.csv
    """
    # Ensure output directory exists
    ensure_directories()
    
    # Sort final output for readability
    df_final = df_ranked.sort_values(
        by=['nutrient_condition', 'rank_r2', 'rank_mae']
    )
    
    # Select and reorder columns for the final report
    # Keep core metrics and rankings
    final_columns = [
        'nutrient_condition', 
        'model_type', 
        'r2_mean', 'r2_std', 
        'mae_mean', 'mae_std',
        'rank_r2', 'rank_mae',
        'beats_null', 'r2_improvement'
    ]
    
    # Filter columns that actually exist (some might be None if null data missing)
    existing_cols = [c for c in final_columns if c in df_final.columns]
    
    df_final = df_final[existing_cols]
    
    df_final.to_csv(output_path, index=False)
    logger.info(f"Successfully saved model metrics rankings to {output_path}")
    logger.info(f"Shape of output: {df_final.shape}")
    
    # Log a summary
    for condition in df_final['nutrient_condition'].unique():
        best_model = df_final[df_final['nutrient_condition'] == condition].iloc[0]
        logger.info(f"Condition '{condition}': Best model is {best_model['model_type']} (R2={best_model['r2_mean']:.4f})")

def main():
    parser = argparse.ArgumentParser(description="Save and rank model metrics.")
    parser.add_argument(
        "--data-dir", 
        type=str, 
        default="data/processed",
        help="Path to processed data directory"
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_file = data_dir / "model_metrics.csv"

    try:
        # 1. Load data
        df_cv, df_null = load_all_model_results(data_dir)

        # 2. Calculate rankings
        df_ranked = calculate_rankings(df_cv, df_null)

        # 3. Save output
        save_metrics_ranking(df_ranked, output_file)

        print(f"Task T036 completed: {output_file} created.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error processing metrics: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())