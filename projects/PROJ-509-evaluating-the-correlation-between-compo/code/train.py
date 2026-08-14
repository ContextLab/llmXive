import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import pickle

from config import load_paths
from utils.chemical_families import assign_chemical_family
from utils.io import load_dataframe_safely

logger = logging.getLogger(__name__)


def load_data(input_path: Path) -> pd.DataFrame:
    """Load the processed dataset."""
    return pd.read_csv(input_path)


def perform_stratified_split(
    df: pd.DataFrame,
    target_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Perform stratified split by chemical family."""
    df = df.copy()
    df["chem_family"] = df["dominant_element"].apply(assign_chemical_family)

    X = df.drop(columns=[target_col, "chem_family", "dominant_element"])
    y = df[target_col]
    family = df["chem_family"]

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, stratify=family, random_state=random_state
    )

    return X_train, X_val, y_train, y_val


def load_models(
    rf_path: Path, gb_path: Path
) -> Tuple[RandomForestRegressor, GradientBoostingRegressor]:
    """Load trained models from disk."""
    with open(rf_path, "rb") as f:
        rf = pickle.load(f)
    with open(gb_path, "rb") as f:
        gb = pickle.load(f)
    return rf, gb


def train_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Tuple[RandomForestRegressor, GradientBoostingRegressor]:
    """Train Random Forest and Gradient Boosting models."""
    rf = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42)
    gb = GradientBoostingRegressor(n_estimators=100, random_state=42)

    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)

    return rf, gb


def save_artifacts(
    rf: RandomForestRegressor,
    gb: GradientBoostingRegressor,
    metrics: Dict[str, Any],
    output_dir: Path,
) -> None:
    """Save model artifacts and metrics."""
    rf_path = output_dir / "model_rf.pkl"
    gb_path = output_dir / "model_gb.pkl"
    metrics_path = output_dir / "model_metrics.json"

    with open(rf_path, "wb") as f:
        pickle.dump(rf, f)
    with open(gb_path, "wb") as f:
        pickle.dump(gb, f)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Saved models and metrics to {output_dir}")


def main() -> None:
    """Main entry point for training."""
    logging.basicConfig(level=logging.INFO)
    paths = load_paths()

    # Load data
    input_path = paths["data_processed"] / "computed_descriptors.csv"
    df = load_data(input_path)

    # Split
    X_train, X_val, y_train, y_val = perform_stratified_split(
        df, target_col="formation_energy_per_atom"
    )

    # Train
    rf, gb = train_models(X_train, y_train)

    # Evaluate (simplified for training script)
    from sklearn.metrics import r2_score

    train_r2_rf = r2_score(y_train, rf.predict(X_train))
    val_r2_rf = r2_score(y_val, rf.predict(X_val))

    metrics = {
        "train_r2_rf": train_r2_rf,
        "val_r2_rf": val_r2_rf,
    }

    # Save
    save_artifacts(rf, gb, metrics, paths["data_evaluation"])
    logger.info("Training complete")


if __name__ == "__main__":
    main()
