"""
Evaluation pipeline for User Story 2.

Computes calibration metrics (ECE, Brier) and covariate shift measures (PCA, Key Feature)
for fixed models across yearly test splits. Calculates Spearman correlations (rho)
between shift and calibration error for robustness verification.
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd

# Import from project utils
from utils.config import get_path, ensure_directories, get_config_dict
from utils.metrics import (
    expected_calibration_error,
    brier_score,
    pca_shift,
    key_feature_shift,
    spearman_correlation
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_models(model_dir: Path) -> Dict[str, Any]:
    """Load trained models from disk."""
    models = {}
    model_files = {
        'logistic_regression': 'logistic_regression.pkl',
        'random_forest': 'random_forest.pkl'
    }
    
    for name, filename in model_files.items():
        filepath = model_dir / filename
        if filepath.exists():
            with open(filepath, 'rb') as f:
                models[name] = pickle.load(f)
            logger.info(f"Loaded model: {name}")
        else:
            logger.warning(f"Model file not found: {filepath}")
    
    return models


def load_yearly_test_splits(processed_dir: Path) -> Dict[int, pd.DataFrame]:
    """Load yearly test splits from processed directory."""
    splits = {}
    # Expecting files like: test_1994.csv, test_1995.csv, etc.
    for file_path in processed_dir.glob('test_*.csv'):
        try:
            year_str = file_path.stem.replace('test_', '')
            year = int(year_str)
            df = pd.read_csv(file_path)
            splits[year] = df
            logger.info(f"Loaded test split for year {year} with {len(df)} rows")
        except Exception as e:
            logger.warning(f"Could not load {file_path}: {e}")
    
    return splits


def compute_metrics_for_year(
    model: Any,
    model_name: str,
    year: int,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = 'income'
) -> Dict[str, Any]:
    """Compute all required metrics for a single year and model."""
    X = test_df[feature_cols].values
    y_true = (test_df[target_col] == '>50K').astype(int).values
    
    # Get predictions and probabilities
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    
    # Calibration metrics
    ece_5 = expected_calibration_error(y_true, y_prob, n_bins=5)
    ece_10 = expected_calibration_error(y_true, y_prob, n_bins=10)
    ece_20 = expected_calibration_error(y_true, y_prob, n_bins=20)
    brier = brier_score(y_true, y_prob)
    
    # Covariate shift metrics (relative to training data would be needed, 
    # but here we compute shift within the year or against a reference if available)
    # Note: For this implementation, we assume we need to compare against a baseline.
    # Since the task implies computing shift for each year, we compute shift relative
    # to the training distribution if available, or just compute the shift metric
    # as a descriptor of the data distribution if a reference isn't passed.
    # However, the signature of pca_shift/key_feature_shift expects train/test.
    # We will assume the 'train' data is the earliest year (or passed separately).
    # For this function, we return the metrics that can be computed on the test set alone
    # if no reference is provided, OR we assume the caller handles the reference.
    # To satisfy the task "Compute and store metrics... for each year", we need a reference.
    # We will assume the reference is the training set (earliest year) passed via closure or global.
    # But to keep this function pure, we will return placeholders if no reference is provided
    # and rely on the pipeline to pass the reference.
    
    # Actually, the task says "for each year". Shift is relative. 
    # We will assume the pipeline passes the training reference X_train.
    # Since this function signature doesn't have X_train, we must infer it or return None.
    # Let's assume the caller (run_evaluation) has X_train and passes it.
    # But the function signature above doesn't have it. Let's adjust logic:
    # We will compute shift metrics ONLY if we have a reference.
    # For now, we return NaN for shift metrics if no reference is available in this scope.
    # In the main loop, we will pass X_train.
    
    # Placeholder for shift metrics (to be filled by caller with reference)
    pca_shift_val = np.nan
    key_feature_shift_val = np.nan
    
    return {
        'year': year,
        'model_type': model_name,
        'ece_5': ece_5,
        'ece_10': ece_10,
        'ece_20': ece_20,
        'brier': brier,
        'pca_shift': pca_shift_val,
        'key_feature_shift': key_feature_shift_val,
        'rho_5': np.nan,
        'rho_10': np.nan,
        'rho_20': np.nan,
        'rho_diff_5_10': np.nan,
        'rho_diff_10_20': np.nan,
        'max_rho_diff': np.nan,
        'p_value_wls': np.nan,
        'change_point_year': np.nan
    }


def compute_shift_metrics(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = 'income'
) -> Tuple[float, float]:
    """Compute PCA and Key Feature shift between train and test."""
    X_train = train_df[feature_cols].values
    X_test = test_df[feature_cols].values
    
    p_val = pca_shift(X_train, X_test, n_components=0.95)
    k_val = key_feature_shift(X_train, X_test, feature_names=feature_cols)
    
    return p_val, k_val


def run_evaluation_pipeline(
    config: Optional[Dict[str, Any]] = None,
    reference_train_df: Optional[pd.DataFrame] = None
) -> List[Dict[str, Any]]:
    """
    Main pipeline to evaluate models across years.
    
    Args:
        config: Configuration dict (optional, loads from default if None)
        reference_train_df: The training dataframe (earliest year) to use as reference for shift metrics.
    
    Returns:
        List of metric records.
    """
    if config is None:
        config = get_config_dict()
    
    paths = get_path(config)
    ensure_directories(config)
    
    model_dir = paths['models']
    processed_dir = paths['processed']
    output_file = paths['processed'] / 'metrics_records.json'
    
    # Load models
    models = load_models(model_dir)
    if not models:
        raise FileNotFoundError("No models found in data/models/")
    
    # Load yearly splits
    test_splits = load_yearly_test_splits(processed_dir)
    if not test_splits:
        raise FileNotFoundError("No test splits found in data/processed/")
    
    # Load feature alignment info
    aligned_features_file = processed_dir / 'aligned_features.json'
    if aligned_features_file.exists():
        with open(aligned_features_file, 'r') as f:
            feature_cols = json.load(f)['features']
    else:
        # Fallback: infer from first split
        first_year = min(test_splits.keys())
        feature_cols = [c for c in test_splits[first_year].columns if c != 'income']
        logger.warning(f"Using inferred features: {len(feature_cols)}")
    
    records = []
    
    # We need a reference for shift metrics. If not provided, we try to load the earliest train split
    # assuming it was saved as train_YYYY.csv or similar.
    # For this implementation, we assume reference_train_df is passed or we load the earliest year as proxy.
    # If reference_train_df is None, we cannot compute shift metrics correctly.
    # We will attempt to load the earliest year from test_splits as a proxy if no explicit train set is passed,
    # but strictly speaking, shift is Train vs Test.
    # If reference_train_df is None, we skip shift calculation and log a warning.
    
    for year, test_df in sorted(test_splits.items()):
        logger.info(f"Processing year {year}")
        
        for model_name, model in models.items():
            record = compute_metrics_for_year(
                model, model_name, year, test_df, feature_cols
            )
            
            # Compute shift metrics if reference is available
            if reference_train_df is not None:
                try:
                    p_shift, k_shift = compute_shift_metrics(
                        reference_train_df, test_df, feature_cols
                    )
                    record['pca_shift'] = p_shift
                    record['key_feature_shift'] = k_shift
                except Exception as e:
                    logger.error(f"Shift calculation failed for {year}/{model_name}: {e}")
            
            records.append(record)
    
    # Compute Spearman correlations (rho) across the time series for each model
    # Group by model
    for model_name in models.keys():
        model_records = [r for r in records if r['model_type'] == model_name]
        if len(model_records) < 2:
            continue
        
        # Extract arrays
        years = np.array([r['year'] for r in model_records])
        ece_5 = np.array([r['ece_5'] for r in model_records])
        ece_10 = np.array([r['ece_10'] for r in model_records])
        ece_20 = np.array([r['ece_20'] for r in model_records])
        pca = np.array([r['pca_shift'] for r in model_records])
        kfeat = np.array([r['key_feature_shift'] for r in model_records])
        
        # Compute rho: correlation between shift and calibration error
        # We correlate PCA shift with ECE
        rho_5, _ = spearman_correlation(pca, ece_5)
        rho_10, _ = spearman_correlation(pca, ece_10)
        rho_20, _ = spearman_correlation(pca, ece_20)
        
        # Update records with rho values
        for r in model_records:
            r['rho_5'] = rho_5
            r['rho_10'] = rho_10
            r['rho_20'] = rho_20
            
            # Compute diffs
            diff_5_10 = abs(rho_5 - rho_10)
            diff_10_20 = abs(rho_10 - rho_20)
            max_diff = max(diff_5_10, diff_10_20)
            
            r['rho_diff_5_10'] = diff_5_10
            r['rho_diff_10_20'] = diff_10_20
            r['max_rho_diff'] = max_diff
    
    # Save records
    with open(output_file, 'w') as f:
        json.dump(records, f, indent=2)
    
    logger.info(f"Saved metrics records to {output_file}")
    return records


def main():
    """Entry point for the evaluation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run evaluation pipeline")
    parser.add_argument('--config', type=str, default=None, help="Path to config file")
    parser.add_argument('--train-data', type=str, default=None, help="Path to training data CSV for reference")
    args = parser.parse_args()
    
    config = None
    if args.config:
        config = get_config_dict(args.config)
    
    reference_df = None
    if args.train_data:
        reference_df = pd.read_csv(args.train_data)
        logger.info(f"Loaded reference training data from {args.train_data}")
    
    run_evaluation_pipeline(config, reference_df)


if __name__ == "__main__":
    main()