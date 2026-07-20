"""Inter-family generalization test.

Measures MAPE on unseen families and verifies that the test set contains
entirely excluded families.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

# Import from existing API surface
from utils.logger import get_logger

logger = get_logger("generalization_test")


def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict[str, Any], path: Path) -> None:
    """Save a dictionary to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def verify_family_disjoint(
    train_families: Set[str], test_families: Set[str]
) -> None:
    """Assert that training and test families are disjoint.

    Raises SystemExit(1) if any family appears in both sets.
    """
    intersection = train_families.intersection(test_families)
    if intersection:
        error_msg = (
            f"SC-002 Violation: Training and test families overlap. "
            f"Common families: {intersection}"
        )
        logger.error(error_msg)
        raise SystemExit(1)


def load_graphs_from_parquet(path: Path) -> pd.DataFrame:
    """Load graphs from a Parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    return pd.read_parquet(path)


def build_family_mapping(
    df: pd.DataFrame,
    index_column: str = "material_id",
    family_column: str = "family_id",
) -> Dict[str, str]:
    """Build a mapping from material_id to family_id."""
    return dict(zip(df[index_column], df[family_column]))


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Percentage Error.

    Handles zero values in y_true by skipping them.
    """
    mask = y_true != 0
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def run_generalization_test(
    predictions_path: Path,
    split_path: Path,
    graphs_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    """Run the inter-family generalization test.

    Args:
        predictions_path: Path to predictions.json from training.
        split_path: Path to split_indices.json.
        graphs_path: Path to graphs_v1.parquet.
        output_path: Path to write generalization_metrics.json.

    Returns:
        Dictionary containing generalization metrics.
    """
    # Load predictions
    logger.info(f"Loading predictions from {predictions_path}")
    predictions = load_json(predictions_path)
    test_indices = predictions.get("test_indices", [])
    test_predictions = predictions.get("test_predictions", {})

    # Load split indices to get family IDs
    logger.info(f"Loading split indices from {split_path}")
    split_data = load_json(split_path)
    train_indices = split_data.get("train_indices", [])
    test_indices_from_split = split_data.get("test_indices", [])

    # Load graphs to get family IDs
    logger.info(f"Loading graphs from {graphs_path}")
    df = load_graphs_from_parquet(graphs_path)
    family_mapping = build_family_mapping(df)

    # Get unique families for train and test
    train_families = set(
        family_mapping.get(str(mid), "unknown") for mid in train_indices
    )
    test_families = set(
        family_mapping.get(str(mid), "unknown") for mid in test_indices_from_split
    )

    # Verify disjoint families
    logger.info(
        f"Verifying family disjointness: {len(train_families)} train families, "
        f"{len(test_families)} test families"
    )
    verify_family_disjoint(train_families, test_families)

    # Calculate metrics on test set
    y_true_list = []
    y_pred_list = []

    for material_id in test_indices_from_split:
        if str(material_id) in test_predictions:
            pred = test_predictions[str(material_id)]
            # Assuming predictions structure: {"youngs": ..., "shear": ..., "poisson": ...}
            if isinstance(pred, dict):
                # For Young's modulus
                true_val = df.loc[df["material_id"] == material_id, "target_youngs"].values
                if len(true_val) > 0:
                    y_true_list.append(true_val[0])
                    y_pred_list.append(pred.get("youngs", 0.0))
            else:
                # If prediction is a single value (e.g., Young's only)
                true_val = df.loc[df["material_id"] == material_id, "target_youngs"].values
                if len(true_val) > 0:
                    y_true_list.append(true_val[0])
                    y_pred_list.append(float(pred))

    if not y_true_list:
        logger.warning("No valid predictions found for test set.")
        mape_youngs = float("nan")
        mape_shear = float("nan")
        mape_poisson = float("nan")
        rmse_youngs = float("nan")
        rmse_shear = float("nan")
        rmse_poisson = float("nan")
    else:
        y_true = np.array(y_true_list)
        y_pred = np.array(y_pred_list)

        mape_youngs = calculate_mape(y_true, y_pred)
        rmse_youngs = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

        # Placeholder for Shear and Poisson if not in predictions
        mape_shear = float("nan")
        mape_poisson = float("nan")
        rmse_shear = float("nan")
        rmse_poisson = float("nan")

    result = {
        "test_families": sorted(list(test_families)),
        "train_families": sorted(list(train_families)),
        "family_disjoint": True,
        "metrics": {
            "youngs_mape": mape_youngs,
            "youngs_rmse": rmse_youngs,
            "shear_mape": mape_shear,
            "shear_rmse": rmse_shear,
            "poisson_mape": mape_poisson,
            "poisson_rmse": rmse_poisson,
        },
        "num_test_materials": len(test_indices_from_split),
        "num_train_materials": len(train_indices),
        "disclaimer": (
            "These results are derived from a machine learning surrogate model "
            "interpolating pre-computed DFT data. They do not represent first-principles "
            "calculations or solutions to the Schrödinger equation."
        ),
    }

    # Save result
    save_json(result, output_path)
    logger.info(f"Generalization metrics saved to {output_path}")

    return result


def main() -> None:
    """Main entry point for the generalization test."""
    parser = argparse.ArgumentParser(
        description="Measure MAPE on unseen families (inter-family generalization test)."
    )
    parser.add_argument(
        "--predictions-path",
        type=Path,
        default=Path("data/results/predictions.json"),
        help="Path to predictions.json from training.",
    )
    parser.add_argument(
        "--split-path",
        type=Path,
        default=Path("data/processed/split_indices.json"),
        help="Path to split_indices.json.",
    )
    parser.add_argument(
        "--graphs-path",
        type=Path,
        default=Path("data/processed/graphs_v1.parquet"),
        help="Path to graphs_v1.parquet.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/results/generalization_metrics.json"),
        help="Path to write generalization_metrics.json.",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting inter-family generalization test...")

    try:
        run_generalization_test(
            predictions_path=args.predictions_path,
            split_path=args.split_path,
            graphs_path=args.graphs_path,
            output_path=args.output_path,
        )
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Generalization test failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()