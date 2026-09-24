"""
Sensitivity Analysis Module (T029)

Implements feature importance extraction from the trained Semi-Empirical Random Forest model.
Outputs: reports/sensitivity.csv with rank, descriptor, importance, cumulative_importance.
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import joblib

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths
MODEL_PATH = PROJECT_ROOT / "models" / "rf_semi.pkl"
EVALUATION_METRICS_PATH = PROJECT_ROOT / "reports" / "evaluation.json"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "sensitivity.csv"
LOG_PATH = PROJECT_ROOT / "logs" / "sensitivity_analysis.log"

# Ensure logs directory exists
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str, log_file: Path) -> logging.Logger:
    """Set up a logger that writes to both file and console."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def load_model(model_path: Path, logger: Optional[logging.Logger] = None) -> Any:
    """Load the trained Random Forest model from disk."""
    if not model_path.exists():
        msg = f"Model file not found: {model_path}. Ensure T021 has completed successfully."
        if logger:
            logger.error(msg)
        raise FileNotFoundError(msg)

    if logger:
        logger.info(f"Loading model from {model_path}")

    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        msg = f"Failed to load model from {model_path}: {e}"
        if logger:
            logger.error(msg)
        raise RuntimeError(msg)


def load_data(data_path: Path, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """Load the descriptor dataset used for training."""
    if not data_path.exists():
        msg = f"Data file not found: {data_path}. Ensure descriptor generation has completed."
        if logger:
            logger.error(msg)
        raise FileNotFoundError(msg)

    if logger:
        logger.info(f"Loading data from {data_path}")

    try:
        df = pd.read_csv(data_path)
        return df
    except Exception as e:
        msg = f"Failed to load data from {data_path}: {e}"
        if logger:
            logger.error(msg)
        raise RuntimeError(msg)


def prepare_features_target(df: pd.DataFrame, target_col: str = "experimental_barrier", logger: Optional[logging.Logger] = None) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Separate features and target from the DataFrame.
    Returns X (features), y (target), and feature_names list.
    """
    if target_col not in df.columns:
        msg = f"Target column '{target_col}' not found in data. Available columns: {list(df.columns)}"
        if logger:
            logger.error(msg)
        raise KeyError(msg)

    feature_cols = [col for col in df.columns if col != target_col]
    if not feature_cols:
        msg = "No feature columns found in the dataset."
        if logger:
            logger.error(msg)
        raise ValueError(msg)

    X = df[feature_cols].values
    y = df[target_col].values

    if logger:
        logger.info(f"Prepared {X.shape[0]} samples with {X.shape[1]} features.")

    return X, y, feature_cols


def extract_feature_importance(model: Any, feature_names: List[str], logger: Optional[logging.Logger] = None) -> List[Dict[str, Any]]:
    """
    Extract feature importances from the model and sort by descending importance.
    Returns a list of dicts: [{'descriptor': str, 'importance': float}, ...]
    """
    if not hasattr(model, 'feature_importances_'):
        msg = "Model does not have 'feature_importances_' attribute. Is it a tree-based model?"
        if logger:
            logger.error(msg)
        raise AttributeError(msg)

    importances = model.feature_importances_

    if len(importances) != len(feature_names):
        msg = f"Feature importance count ({len(importances)}) does not match feature names count ({len(feature_names)})."
        if logger:
            logger.error(msg)
        raise ValueError(msg)

    # Pair and sort
    paired = list(zip(feature_names, importances))
    sorted_pairs = sorted(paired, key=lambda x: x[1], reverse=True)

    result = []
    cumulative = 0.0
    for rank, (desc, imp) in enumerate(sorted_pairs, start=1):
        cumulative += imp
        result.append({
            'rank': rank,
            'descriptor': desc,
            'importance': float(imp),
            'cumulative_importance': float(cumulative)
        })

    if logger:
        logger.info(f"Extracted importance for {len(result)} features.")
        logger.info(f"Top 3 descriptors: {[r['descriptor'] for r in result[:3]]}")

    return result


def write_sensitivity_csv(results: List[Dict[str, Any]], output_path: Path, logger: Optional[logging.Logger] = None) -> None:
    """Write the sensitivity analysis results to a CSV file."""
    if not results:
        msg = "No results to write."
        if logger:
            logger.error(msg)
        raise ValueError(msg)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['rank', 'descriptor', 'importance', 'cumulative_importance']

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    if logger:
        logger.info(f"Wrote sensitivity results to {output_path}")


def main() -> None:
    """Main entry point for T029."""
    parser = argparse.ArgumentParser(description="T029: Extract feature importance from Semi-Empirical RF model.")
    parser.add_argument('--model-path', type=str, default=str(MODEL_PATH), help="Path to the trained model (rf_semi.pkl)")
    parser.add_argument('--data-path', type=str, default=str(PROJECT_ROOT / "data" / "descriptors_semi.csv"), help="Path to the descriptor data CSV")
    parser.add_argument('--output-path', type=str, default=str(OUTPUT_PATH), help="Path to output sensitivity CSV")
    parser.add_argument('--log-path', type=str, default=str(LOG_PATH), help="Path to log file")
    args = parser.parse_args()

    # Setup logging
    logger = setup_logger("sensitivity_analysis", Path(args.log_path))
    logger.info("Starting T029: Sensitivity Analysis")

    try:
        # 1. Load Model (T021 artifact)
        model = load_model(Path(args.model_path), logger)

        # 2. Load Data (T013c artifact)
        df = load_data(Path(args.data_path), logger)

        # 3. Prepare Features
        X, y, feature_names = prepare_features_target(df, logger=logger)

        # 4. Extract Importance
        results = extract_feature_importance(model, feature_names, logger)

        # 5. Write Output
        write_sensitivity_csv(results, Path(args.output_path), logger)

        logger.info("T029 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Missing required artifact: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
