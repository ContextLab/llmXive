"""
Evaluation Pipeline for Calibration Drift Analysis.

This module loads fixed models and iterates through yearly test splits to compute
calibration and covariate shift metrics. It implements graceful handling of missing
years as per Edge Cases (T025).
"""
import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import numpy as np

# Local imports matching API surface
from utils.config import get_path, ensure_directories
from utils.metrics import (
    expected_calibration_error,
    brier_score,
    pca_shift,
    key_feature_shift,
    spearman_correlation
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_models(model_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load trained models from the data/models directory.

    Args:
        model_dir: Optional path to models directory. Defaults to config.

    Returns:
        Dictionary mapping model names to loaded model objects.
    """
    if model_dir is None:
        model_dir = get_path("models")
    
    if not model_dir.exists():
        raise FileNotFoundError(f"Model directory not found: {model_dir}")

    models = {}
    for model_file in model_dir.glob("*.pkl"):
        model_name = model_file.stem
        with open(model_file, 'rb') as f:
            models[model_name] = pickle.load(f)
        logger.info(f"Loaded model: {model_name}")
    
    return models


def load_yearly_test_splits(data_dir: Optional[Path] = None) -> Dict[int, pd.DataFrame]:
    """
    Load yearly test splits from data/processed.

    Args:
        data_dir: Optional path to processed data directory.

    Returns:
        Dictionary mapping year to DataFrame.
    """
    if data_dir is None:
        data_dir = get_path("processed")
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {data_dir}")

    yearly_splits = {}
    
    # Look for files matching pattern: test_split_YEAR.csv
    for file_path in data_dir.glob("test_split_*.csv"):
        try:
            # Extract year from filename
            year_str = file_path.stem.replace("test_split_", "")
            year = int(year_str)
            
            df = pd.read_csv(file_path)
            yearly_splits[year] = df
            logger.info(f"Loaded test split for year: {year}")
        except ValueError as e:
            logger.warning(f"Skipping file {file_path.name} due to invalid year format: {e}")
        except Exception as e:
            logger.warning(f"Error loading {file_path.name}: {e}")

    return yearly_splits


def compute_metrics_for_year(
    year: int,
    model: Any,
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    bins_list: List[int] = [5, 10, 20]
) -> Dict[str, Any]:
    """
    Compute all calibration and shift metrics for a single year.

    Args:
        year: The year being evaluated.
        model: The trained model to evaluate.
        df: The DataFrame containing test data for the year.
        feature_cols: List of feature column names.
        target_col: Name of the target column.
        bins_list: List of bin counts for ECE calculation.

    Returns:
        Dictionary containing all computed metrics.
    """
    X = df[feature_cols].values
    y_true = df[target_col].values

    # Get predictions (probabilities for positive class)
    try:
        y_prob = model.predict_proba(X)[:, 1]
    except AttributeError:
        # Fallback for models that only have predict
        y_prob = model.predict(X)
        # If predictions are already probabilities (0/1), convert to prob-like
        if set(np.unique(y_prob)) == {0, 1}:
            y_prob = y_prob.astype(float)

    # Compute calibration metrics
    ece_results = {}
    for n_bins in bins_list:
        ece = expected_calibration_error(y_true, y_prob, n_bins)
        ece_results[f'ece_{n_bins}'] = ece

    # Compute Brier score
    brier = brier_score(y_true, y_prob)

    # Compute covariate shift metrics
    # We need training data for shift calculation, but this function is called per year
    # The shift metrics are computed against the original training set
    # This will be handled in the pipeline function by passing train data

    metrics = {
        'year': year,
        'model_type': model.__class__.__name__,
        **ece_results,
        'brier': brier
    }

    return metrics


def compute_shift_metrics(
    year: int,
    model_name: str,
    train_features: np.ndarray,
    test_features: np.ndarray,
    feature_names: List[str],
    ece_5: float,
    ece_10: float,
    ece_20: float,
    y_true: np.ndarray,
    y_prob: np.ndarray
) -> Dict[str, Any]:
    """
    Compute covariate shift metrics and correlation with calibration error.

    Args:
        year: The year being evaluated.
        model_name: Name of the model.
        train_features: Training feature matrix.
        test_features: Test feature matrix for the year.
        feature_names: List of feature names.
        ece_5, ece_10, ece_20: ECE values for different bin counts.
        y_true: True labels.
        y_prob: Predicted probabilities.

    Returns:
        Dictionary containing shift metrics and correlations.
    """
    # Compute PCA Shift
    pca_shift_val = pca_shift(train_features, test_features, n_components=0.95)

    # Compute Key Feature Shift
    key_shift_val = key_feature_shift(train_features, test_features, feature_names)

    # Compute Spearman correlation between shift and calibration error
    # We correlate the shift metric with the ECE for this year
    # Since we have only one point per year, we compute correlation across years
    # This will be aggregated later. For now, we store individual values.
    
    # Compute rho for each binning strategy (correlation of shift vs ECE across years)
    # Since we can't compute correlation on a single point, we return the raw values
    # The correlation will be computed in the statistical analysis phase
    
    rho_5 = np.nan  # Placeholder, will be computed across years
    rho_10 = np.nan
    rho_20 = np.nan

    metrics = {
        'year': year,
        'model_type': model_name,
        'pca_shift': pca_shift_val,
        'key_feature_shift': key_shift_val,
        'rho_5': rho_5,
        'rho_10': rho_10,
        'rho_20': rho_20
    }

    return metrics


def run_evaluation_pipeline(
    models: Optional[Dict[str, Any]] = None,
    train_data: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Run the full evaluation pipeline.

    Loads models, iterates through yearly test splits, computes metrics,
    and handles missing years gracefully.

    Args:
        models: Pre-loaded models. If None, loads from default path.
        train_data: Training data for shift calculation. If None, loads from default.
        output_path: Path to save metrics records.

    Returns:
        List of metric records.
    """
    if models is None:
        models = load_models()
    
    if not models:
        raise ValueError("No models found to evaluate.")

    yearly_splits = load_yearly_test_splits()
    
    if not yearly_splits:
        raise ValueError("No yearly test splits found.")

    # Load training data for shift calculation
    if train_data is None:
        train_path = get_path("processed", "train_split_1994.csv")
        if not train_path.exists():
            # Try to find any train split
            train_dir = get_path("processed")
            train_files = list(train_dir.glob("train_split_*.csv"))
            if train_files:
                train_path = train_files[0]
            else:
                raise FileNotFoundError("Training data not found for shift calculation.")
        train_data = pd.read_csv(train_path)
        logger.info(f"Loaded training data from: {train_path}")

    # Determine feature columns (common subset)
    # Assume target column is 'income' or similar
    target_col = 'income' if 'income' in train_data.columns else train_data.columns[-1]
    feature_cols = [col for col in train_data.columns if col != target_col]
    
    train_features = train_data[feature_cols].values
    train_feature_names = feature_cols

    # Sort years to handle gaps
    sorted_years = sorted(yearly_splits.keys())
    all_metrics = []

    # Track years for correlation calculation
    all_eces = {5: [], 10: [], 20: []}
    all_shifts = []
    all_years_for_corr = []

    for year in sorted_years:
        df = yearly_splits[year]
        
        # Check for missing columns (graceful handling)
        missing_cols = set(feature_cols) - set(df.columns)
        if missing_cols:
            logger.warning(f"Year {year}: Missing features {missing_cols}. Skipping year.")
            continue

        # Check for missing target column
        if target_col not in df.columns:
            logger.warning(f"Year {year}: Target column '{target_col}' not found. Skipping year.")
            continue

        # Filter to common features
        X_test = df[feature_cols].values
        y_true = df[target_col].values

        # Process each model
        for model_name, model in models.items():
            try:
                # Compute calibration metrics
                year_metrics = compute_metrics_for_year(
                    year=year,
                    model=model,
                    df=df,
                    feature_cols=feature_cols,
                    target_col=target_col
                )

                # Compute shift metrics
                shift_metrics = compute_shift_metrics(
                    year=year,
                    model_name=model_name,
                    train_features=train_features,
                    test_features=X_test,
                    feature_names=train_feature_names,
                    ece_5=year_metrics['ece_5'],
                    ece_10=year_metrics['ece_10'],
                    ece_20=year_metrics['ece_20'],
                    y_true=y_true,
                    y_prob=model.predict_proba(X_test)[:, 1]
                )

                # Merge metrics
                record = {**year_metrics, **shift_metrics}
                all_metrics.append(record)

                # Collect for correlation calculation
                all_eces[5].append(year_metrics['ece_5'])
                all_eces[10].append(year_metrics['ece_10'])
                all_eces[20].append(year_metrics['ece_20'])
                all_shifts.append(shift_metrics['pca_shift'])
                all_years_for_corr.append(year)

                logger.info(f"Computed metrics for {model_name} in year {year}")

            except Exception as e:
                logger.warning(f"Error processing {model_name} for year {year}: {e}")
                continue

    # Compute correlations across years
    if len(all_years_for_corr) > 1:
        # Correlation between PCA shift and ECE
        rho_5, _ = spearman_correlation(all_shifts, all_eces[5])
        rho_10, _ = spearman_correlation(all_shifts, all_eces[10])
        rho_20, _ = spearman_correlation(all_shifts, all_eces[20])

        # Update records with correlation values
        for record in all_metrics:
            if record['year'] in all_years_for_corr:
                idx = all_years_for_corr.index(record['year'])
                record['rho_5'] = rho_5
                record['rho_10'] = rho_10
                record['rho_20'] = rho_20

        # Compute rho_diff fields
        for record in all_metrics:
            record['rho_diff_5_10'] = abs(record['rho_5'] - record['rho_10'])
            record['rho_diff_10_20'] = abs(record['rho_10'] - record['rho_20'])
            record['max_rho_diff'] = max(record['rho_diff_5_10'], record['rho_diff_10_20'])

    # Save results
    if output_path is None:
        output_path = get_path("processed", "metrics_records.json")
    
    ensure_directories(output_path)
    
    with open(output_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"Saved {len(all_metrics)} metric records to {output_path}")

    return all_metrics


def main():
    """Main entry point for the evaluation pipeline."""
    logger.info("Starting evaluation pipeline...")
    
    try:
        metrics = run_evaluation_pipeline()
        logger.info(f"Evaluation complete. Processed {len(metrics)} records.")
    except Exception as e:
        logger.error(f"Evaluation pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()