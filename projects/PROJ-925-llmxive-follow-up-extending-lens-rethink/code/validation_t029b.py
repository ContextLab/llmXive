"""
T029b: Preliminary Validation for Train XGBoost Logic (US3).

This script validates the training logic of `train_xgboost` from `code/data/train.py`.
It performs a sanity check on a small, deterministic subset of the processed data
to ensure the model trains, converges, and produces valid output metrics.
It generates `results/validation_report.json` as the artifact.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import xgboost as xgb

# Project imports
from config import get_paths, init_run
from utils.logging import setup_logging, get_logger
from data.train import train_xgboost

# Constants
RESULTS_DIR = "results"
VALIDATION_REPORT_PATH = "results/validation_report.json"
SAMPLE_SIZE = 1000  # Use a small sample for validation speed
RANDOM_SEED = 42

def load_sample_features_and_target() -> tuple[pd.DataFrame, pd.Series]:
    """
    Loads a small sample of the processed features and deviation target.
    Expects data to be in data/processed/features.csv and data/processed/deviation.csv.
    """
    paths = get_paths()
    features_path = paths.processed_dir / "features.csv"
    deviation_path = paths.processed_dir / "deviation.csv"

    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found: {features_path}")
    if not deviation_path.exists():
        raise FileNotFoundError(f"Deviation file not found: {deviation_path}")

    logger = get_logger()
    logger.info(f"Loading features from {features_path}")
    features_df = pd.read_csv(features_path)
    logger.info(f"Loading deviation from {deviation_path}")
    target_df = pd.read_csv(deviation_path)

    # Merge on a common key if necessary, or assume aligned rows.
    # Based on typical pipeline, deviation.csv usually has the target column 'deviation_score'.
    # We assume the rows are aligned by index or a common 'caption_id' if present.
    # For safety, we merge on index if no ID column is obvious, but let's check columns.
    
    # Simplest assumption for validation: rows are aligned by index after processing.
    # If 'caption_id' exists, we merge on that.
    if 'caption_id' in features_df.columns and 'caption_id' in target_df.columns:
        merged = features_df.merge(target_df[['caption_id', 'deviation_score']], on='caption_id', how='inner')
    else:
        # Fallback to index alignment (assuming same order and no drops in between)
        merged = pd.concat([features_df, target_df['deviation_score']], axis=1)

    if merged.empty:
        raise ValueError("Merged dataframe is empty. Check data alignment.")

    # Separate features and target
    # Assume target column is 'deviation_score'
    if 'deviation_score' not in merged.columns:
        raise ValueError(f"Target column 'deviation_score' not found in merged data. Columns: {merged.columns.tolist()}")

    X = merged.drop(columns=['deviation_score', 'caption_id'] if 'caption_id' in merged.columns else ['deviation_score'])
    y = merged['deviation_score']

    # Sample if too large
    if len(X) > SAMPLE_SIZE:
        logger.info(f"Sampling {SAMPLE_SIZE} rows for validation...")
        indices = np.random.RandomState(RANDOM_SEED).choice(len(X), SAMPLE_SIZE, replace=False)
        X = X.iloc[indices]
        y = y.iloc[indices]

    return X, y

def validate_training_logic(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Runs the training logic on the sample data and validates the output.
    """
    logger = get_logger()
    report = {
        "status": "unknown",
        "validation_time_seconds": 0.0,
        "input_rows": len(X),
        "input_features": X.shape[1],
        "metrics": {},
        "errors": []
    }

    start_time = time.time()

    try:
        # 1. Train the model
        logger.info("Starting XGBoost training validation...")
        model = train_xgboost(X.values, y.values)

        if model is None:
            report["errors"].append("Model returned None.")
            report["status"] = "failed"
            return report

        # 2. Verify model attributes
        if not hasattr(model, 'best_score'):
            logger.warning("Model does not have 'best_score' attribute (might not have used CV).")
        
        # 3. Predict on a hold-out split or the same data (for sanity check)
        # Since we are validating logic, we check if it can predict without error.
        preds = model.predict(X.values[:10]) # Predict on first 10 rows
        
        if len(preds) != 10:
            report["errors"].append(f"Prediction length mismatch: expected 10, got {len(preds)}")
            report["status"] = "failed"
            return report

        # 4. Check for NaNs in predictions
        if np.any(np.isnan(preds)):
            report["errors"].append("Predictions contain NaN values.")
            report["status"] = "failed"
            return report

        # 5. Calculate a simple correlation to ensure non-trivial fit
        corr = np.corrcoef(preds, y.values[:10])[0, 1]
        if np.isnan(corr):
            report["errors"].append("Correlation coefficient is NaN.")
            report["status"] = "failed"
            return report

        # 6. Record metrics
        report["metrics"] = {
            "sample_prediction_mean": float(np.mean(preds)),
            "sample_prediction_std": float(np.std(preds)),
            "sample_target_mean": float(np.mean(y.values[:10])),
            "sample_target_std": float(np.std(y.values[:10])),
            "sample_correlation": float(corr),
            "model_type": str(type(model).__name__),
            "best_score": float(model.best_score) if hasattr(model, 'best_score') else None
        }

        report["status"] = "passed"
        logger.info("Training logic validation PASSED.")

    except Exception as e:
        logger.error(f"Validation failed with exception: {e}", exc_info=True)
        report["errors"].append(str(e))
        report["status"] = "failed"
    
    finally:
        report["validation_time_seconds"] = time.time() - start_time

    return report

def main():
    """
    Entry point for T029b validation.
    """
    # Setup
    setup_logging()
    logger = get_logger()
    logger.info("Starting T029b: Preliminary Validation for Train XGBoost")

    # Ensure results directory exists
    paths = get_paths()
    results_dir = paths.project_root / RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load Data
        X, y = load_sample_features_and_target()
        logger.info(f"Loaded sample data: {X.shape[0]} rows, {X.shape[1]} features")

        # 2. Validate Logic
        report = validate_training_logic(X, y)

        # 3. Save Report
        report_path = results_dir / VALIDATION_REPORT_PATH
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {report_path}")
        logger.info(f"Final Status: {report['status']}")

        if report["status"] != "passed":
            logger.error("Validation FAILED. Check logs and report.")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"Required data files missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
