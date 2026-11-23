"""
T021: Execute/Calculate baseline R² using mean-prediction model.

This script calculates the baseline R² score for a 'mean-prediction' model
on each held-out test fold of the Leave-One-Species-Out (LOSO) cross-validation.
It loads the merged dataset, performs LOSO splits, trains a mean-predictor
on the training fold, evaluates on the test fold, and writes the results
to artifacts/baseline_metrics.json.

Output Schema:
{
    "mean_baseline_r2": float,
    "per_fold_baseline_r2": [float]
}
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "merged_dataset.csv"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
OUTPUT_PATH = ARTIFACTS_DIR / "baseline_metrics.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_merged_data() -> pd.DataFrame:
    """Load the merged dataset produced by T017."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Required input file not found: {DATA_PATH}. "
            "Ensure T017 has been executed successfully."
        )
    logger.info(f"Loading merged dataset from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    
    # Verify required columns exist
    required_cols = ['root_depth', 'root_diameter', 'N', 'P', 'K', 'pH', 'species']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    # Drop rows with NaN in target or features
    df = df.dropna(subset=['root_depth', 'root_diameter', 'N', 'P', 'K', 'pH', 'species'])
    logger.info(f"Loaded {len(df)} valid records for baseline calculation.")
    return df

def calculate_mean_baseline_r2(
    y_train: np.ndarray, 
    y_test: np.ndarray
) -> float:
    """
    Calculate R² for a model that predicts the mean of y_train for all test samples.
    
    Args:
        y_train: Training target values
        y_test: Test target values
        
    Returns:
        R² score of the mean-prediction model
    """
    if len(y_train) == 0:
        return np.nan
    
    mean_pred = np.mean(y_train)
    y_pred_test = np.full_like(y_test, mean_pred, dtype=float)
    
    return r2_score(y_test, y_pred_test)

def run_loso_baseline_analysis(df: pd.DataFrame, target_col: str = 'root_depth') -> Dict[str, Any]:
    """
    Perform LOSO cross-validation with a mean-prediction baseline.
    
    Args:
        df: DataFrame with features, targets, and species column
        target_col: Name of the target column (default: 'root_depth')
        
    Returns:
        Dictionary with baseline metrics
    """
    # Prepare features and targets
    # We use all available soil features for the baseline calculation context
    feature_cols = ['N', 'P', 'K', 'pH']
    X = df[feature_cols].values
    y = df[target_col].values
    groups = df['species'].values

    # Setup GroupKFold for LOSO (each species is a fold)
    unique_species = np.unique(groups)
    n_folds = len(unique_species)
    logger.info(f"Performing LOSO CV with {n_folds} species folds.")

    gkf = GroupKFold(n_splits=n_folds)
    per_fold_r2 = []

    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        y_train = y[train_idx]
        y_test = y[test_idx]
        
        # Calculate baseline R²
        fold_r2 = calculate_mean_baseline_r2(y_train, y_test)
        per_fold_r2.append(fold_r2)
        
        logger.info(f"Fold {fold_idx+1}/{n_folds}: Baseline R² = {fold_r2:.4f}")

    # Filter out NaN values if any fold had insufficient data
    valid_r2_scores = [r for r in per_fold_r2 if not np.isnan(r)]
    
    if not valid_r2_scores:
        logger.warning("No valid baseline R² scores calculated.")
        mean_baseline_r2 = np.nan
    else:
        mean_baseline_r2 = float(np.mean(valid_r2_scores))

    return {
        "mean_baseline_r2": mean_baseline_r2,
        "per_fold_baseline_r2": [float(r) if not np.isnan(r) else None for r in per_fold_r2]
    }

def main():
    """Main entry point for T021."""
    try:
        # Ensure artifacts directory exists
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

        # Load data
        df = load_merged_data()

        # Calculate baseline for root_depth (primary target)
        logger.info("Calculating baseline R² for root_depth...")
        metrics = run_loso_baseline_analysis(df, target_col='root_depth')

        # Write output
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Baseline metrics written to {OUTPUT_PATH}")
        logger.info(f"Mean Baseline R²: {metrics['mean_baseline_r2']:.4f}")

    except FileNotFoundError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during baseline calculation: {e}")
        raise

if __name__ == "__main__":
    main()