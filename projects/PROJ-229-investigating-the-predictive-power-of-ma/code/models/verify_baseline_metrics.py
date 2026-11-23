"""
verify_baseline_metrics.py

This script loads the baseline models trained by
`train_random_forest.py` and `train_gradient_boosting.py`,
evaluates them on a held‑out test split of the raw materials data,
and writes a JSON verification report to
`data/results/baseline_verification.json`.

The script is deliberately lightweight – it does not re‑train any model,
it only performs inference and records the R² scores for reproducibility
checks.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

import joblib
import numpy as np
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

# Project utilities
from config import get_random_seed
from evaluate import load_raw_materials_data

# Configure a module‑level logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_model(model_path: Path):
    """Load a scikit‑learn model persisted with ``joblib.dump``."""
    if not model_path.is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    logger.info("Loading model from %s", model_path)
    return joblib.load(model_path)


def _prepare_data(test_size: float = 0.2):
    """
    Load the raw materials dataset and split it into train / test sets.

    The raw loader returns a ``pandas.DataFrame`` with the target column
    named ``target`` (the column name is defined by the earlier target‑
    consistency step). All other columns are treated as features.
    """
    df = load_raw_materials_data()
    if "target" not in df.columns:
        raise KeyError(
            "Target column 'target' not found in the raw materials dataframe."
        )
    X = df.drop(columns=["target"]).values
    y = df["target"].values
    # Use the project‑wide random seed for reproducibility
    seed = get_random_seed()
    logger.info("Splitting data (test_size=%.2f, random_state=%s)", test_size, seed)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed
    )
    # The training split is not needed for verification, but we keep the
    # variable names for clarity.
    return X_test, y_test


def _evaluate_model(model, X_test: np.ndarray, y_test: np.ndarray) -> float:
    """Return the R² score of ``model`` on the provided test data."""
    predictions = model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    logger.info("Model %s R²: %.4f", type(model).__name__, r2)
    return r2


def main():
    """
    Entry point for the verification script.

    It performs the following steps:

    1. Load the test split of the raw dataset.
    2. Load the two baseline models (RF and GB).
    3. Compute R² for each model on the test data.
    4. Write a JSON file with the results and a timestamp.
    """
    logger.info("Starting baseline verification...")

    # ------------------------------------------------------------------
    # 1. Prepare test data
    # ------------------------------------------------------------------
    X_test, y_test = _prepare_data()

    # ------------------------------------------------------------------
    # 2. Load models
    # ------------------------------------------------------------------
    rf_model_path = Path("data/models/rf_model.pkl")
    gb_model_path = Path("data/models/gb_model.pkl")

    rf_model = _load_model(rf_model_path)
    gb_model = _load_model(gb_model_path)

    # ------------------------------------------------------------------
    # 3. Evaluate
    # ------------------------------------------------------------------
    rf_r2 = _evaluate_model(rf_model, X_test, y_test)
    gb_r2 = _evaluate_model(gb_model, X_test, y_test)

    # ------------------------------------------------------------------
    # 4. Write verification report
    # ------------------------------------------------------------------
    results = {
        "random_forest_r2": rf_r2,
        "gradient_boosting_r2": gb_r2,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    output_path = Path("data/results/baseline_verification.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info("Baseline verification written to %s", output_path)

# ----------------------------------------------------------------------
# When executed as a script
# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
