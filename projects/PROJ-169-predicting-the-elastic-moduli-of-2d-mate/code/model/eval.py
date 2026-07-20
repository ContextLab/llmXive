"""Evaluation and metrics calculation for the elastic moduli surrogate model.

Computes MAPE, RMSE, and R² for Young's Modulus, Shear Modulus, and Poisson's Ratio
using real predictions and ground-truth values from the test set.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.config import set_global_config, enforce_reproducibility

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def calculate_metrics(
    y_true: np.ndarray, y_pred: np.ndarray
) -> Dict[str, float]:
    """Calculate evaluation metrics: MAPE, RMSE, R².

    Args:
        y_true: Ground truth values (N,).
        y_pred: Predicted values (N,).

    Returns:
        Dictionary with 'mape', 'rmse', 'r2'.
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        logger.warning("Empty arrays provided for metric calculation.")
        return {"mape": float("nan"), "rmse": float("nan"), "r2": float("nan")}

    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()

    if y_true.shape != y_pred.shape:
        raise ValueError(
            f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}"
        )

    # RMSE
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    # R²
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        r2 = 0.0 if ss_res == 0 else float("nan")
    else:
        r2 = 1.0 - (ss_res / ss_tot)

    # MAPE (handle zero true values to avoid division by zero)
    mask = y_true != 0
    if np.sum(mask) == 0:
        mape = float("nan")
    else:
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    return {"mape": float(mape), "rmse": float(rmse), "r2": float(r2)}


def evaluate_model(
    predictions_path: Path, test_indices_path: Path, graphs_path: Path
) -> Dict[str, Any]:
    """Evaluate model predictions against ground truth.

    Args:
        predictions_path: Path to predictions.json (output of train.py).
        test_indices_path: Path to split_indices.json.
        graphs_path: Path to graphs_v1.parquet.

    Returns:
        Dictionary containing metrics for Young's, Shear, and Poisson.
    """
    # Load predictions
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")

    with open(predictions_path, "r") as f:
        predictions_data = json.load(f)

    # Load split indices to identify test set
    if not test_indices_path.exists():
        raise FileNotFoundError(f"Split indices file not found: {test_indices_path}")

    with open(test_indices_path, "r") as f:
        split_data = json.load(f)

    test_indices = split_data.get("test_indices", [])
    if not test_indices:
        raise ValueError("No test indices found in split file.")

    # Load graphs to extract ground truth
    # Note: We use pandas to read parquet as it's the standard for this project
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is required to read parquet files. Install it via pip.")
        raise

    df = pd.read_parquet(graphs_path)

    # Filter for test set
    if not all(isinstance(i, int) for i in test_indices):
        # Handle case where indices might be strings or mixed
        test_indices = [int(i) for i in test_indices if str(i).isdigit()]

    test_df = df.iloc[test_indices]

    if len(test_df) == 0:
        raise ValueError("No test samples found in the dataset after filtering.")

    # Extract ground truth
    # Assuming target_moduli is stored as a dict or list in the parquet
    # Structure: {'youngs': val, 'shear': val, 'poissons': val}
    y_true_youngs = []
    y_true_shear = []
    y_true_poissons = []
    y_pred_youngs = []
    y_pred_shear = []
    y_pred_poissons = []

    # Map predictions to test indices
    # predictions_data should be a list of dicts: [{'youngs': p, 'shear': p, 'poissons': p}, ...]
    # corresponding to the full dataset or just the test set?
    # Based on T018b, predictions.json contains predictions for the test set.
    # We assume the order in predictions.json matches the order of test_indices in split.

    if len(predictions_data) != len(test_indices):
        logger.warning(
            f"Prediction count ({len(predictions_data)}) does not match test indices count ({len(test_indices)}). "
            "Attempting to align by index if predictions contain indices."
        )
        # If predictions are keyed by index, we need to sort them
        if isinstance(predictions_data, list) and len(predictions_data) > 0 and isinstance(predictions_data[0], dict):
            # Check if 'index' key exists
            if 'index' in predictions_data[0]:
                pred_map = {p['index']: p for p in predictions_data}
                for idx in test_indices:
                    if idx in pred_map:
                        p = pred_map[idx]
                        y_pred_youngs.append(p.get('youngs', 0.0))
                        y_pred_shear.append(p.get('shear', 0.0))
                        y_pred_poissons.append(p.get('poissons', 0.0))
                    else:
                        # Fallback if index missing
                        y_pred_youngs.append(0.0)
                        y_pred_shear.append(0.0)
                        y_pred_poissons.append(0.0)
            else:
                # Assume order matches
                for i, row in test_df.iterrows():
                    if i < len(predictions_data):
                        p = predictions_data[i]
                        y_pred_youngs.append(p.get('youngs', 0.0))
                        y_pred_shear.append(p.get('shear', 0.0))
                        y_pred_poissons.append(p.get('poissons', 0.0))
                    else:
                        y_pred_youngs.append(0.0)
                        y_pred_shear.append(0.0)
                        y_pred_poissons.append(0.0)
        else:
            # Fallback: assume order matches
            for i, row in test_df.iterrows():
                if i < len(predictions_data):
                    p = predictions_data[i]
                    y_pred_youngs.append(p.get('youngs', 0.0))
                    y_pred_shear.append(p.get('shear', 0.0))
                    y_pred_poissons.append(p.get('poissons', 0.0))
                else:
                    y_pred_youngs.append(0.0)
                    y_pred_shear.append(0.0)
                    y_pred_poissons.append(0.0)
    else:
        # Direct mapping
        for i, row in test_df.iterrows():
            if i < len(predictions_data):
                p = predictions_data[i]
                y_pred_youngs.append(p.get('youngs', 0.0))
                y_pred_shear.append(p.get('shear', 0.0))
                y_pred_poissons.append(p.get('poissons', 0.0))
            else:
                y_pred_youngs.append(0.0)
                y_pred_shear.append(0.0)
                y_pred_poissons.append(0.0)

    # Extract ground truth from dataframe
    # Assuming 'target_moduli' column contains dict {'youngs': ..., 'shear': ..., 'poissons': ...}
    for _, row in test_df.iterrows():
        target = row.get('target_moduli')
        if isinstance(target, dict):
            y_true_youngs.append(target.get('youngs', 0.0))
            y_true_shear.append(target.get('shear', 0.0))
            y_true_poissons.append(target.get('poissons', 0.0))
        elif isinstance(target, (list, tuple)) and len(target) >= 3:
            # Fallback for list format
            y_true_youngs.append(target[0])
            y_true_shear.append(target[1])
            y_true_poissons.append(target[2])
        else:
            y_true_youngs.append(0.0)
            y_true_shear.append(0.0)
            y_true_poissons.append(0.0)

    y_true_youngs = np.array(y_true_youngs)
    y_true_shear = np.array(y_true_shear)
    y_true_poissons = np.array(y_true_poissons)
    y_pred_youngs = np.array(y_pred_youngs)
    y_pred_shear = np.array(y_pred_shear)
    y_pred_poissons = np.array(y_pred_poissons)

    # Calculate metrics for each property
    metrics_youngs = calculate_metrics(y_true_youngs, y_pred_youngs)
    metrics_shear = calculate_metrics(y_true_shear, y_pred_shear)
    metrics_poissons = calculate_metrics(y_true_poissons, y_pred_poissons)

    return {
        "youngs_modulus": metrics_youngs,
        "shear_modulus": metrics_shear,
        "poissons_ratio": metrics_poissons,
        "sample_size": len(test_indices),
    }


def main():
    """Main entry point for evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate model predictions and calculate metrics."
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path("data/results/predictions.json"),
        help="Path to predictions.json file.",
    )
    parser.add_argument(
        "--splits",
        type=Path,
        default=Path("data/processed/split_indices.json"),
        help="Path to split_indices.json file.",
    )
    parser.add_argument(
        "--graphs",
        type=Path,
        default=Path("data/processed/graphs_v1.parquet"),
        help="Path to graphs_v1.parquet file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results/evaluation_metrics.json"),
        help="Path to output metrics JSON file.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (optional, for reproducibility).",
    )

    args = parser.parse_args()

    # Set global config if provided
    if args.config:
        set_global_config(args.config)
        enforce_reproducibility()

    logger.info(f"Loading predictions from {args.predictions}")
    logger.info(f"Loading split indices from {args.splits}")
    logger.info(f"Loading graphs from {args.graphs}")
    logger.info(f"Output will be written to {args.output}")

    try:
        metrics = evaluate_model(args.predictions, args.splits, args.graphs)

        # Ensure output directory exists
        args.output.parent.mkdir(parents=True, exist_ok=True)

        # Write results
        with open(args.output, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Evaluation complete. Metrics written to {args.output}")
        logger.info(f"Young's Modulus MAPE: {metrics['youngs_modulus']['mape']:.2f}%")
        logger.info(f"Shear Modulus MAPE: {metrics['shear_modulus']['mape']:.2f}%")
        logger.info(f"Poisson's Ratio MAPE: {metrics['poissons_ratio']['mape']:.2f}%")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {e}")
        raise


if __name__ == "__main__":
    main()