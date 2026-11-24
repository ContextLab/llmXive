import os
import json
import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

from sklearn.linear_model import LinearRegression

from config import (
    get_processed_data_dir,
    get_results_dir,
    ensure_directories,
    get_logger,
)

logger = get_logger(__name__)

def main():
    """
    Entry point for the baseline (Linear Regression) training step.
    Loads the processed train CSV, trains a LinearRegression model on the
    first target column, and saves the model artifact to
    <project>/results/model/baseline_model.joblib.
    """
    logger.info("Starting baseline training step...")
    processed_dir = Path(get_processed_data_dir())
    train_path = processed_dir / "train.csv"
    test_path = processed_dir / "test.csv"

    if not train_path.exists() or not test_path.exists():
        logger.error("Processed train or test CSV not found.")
        raise FileNotFoundError("Processed data files missing.")

    train_df = pd.read_csv(train_path)

    # Determine target columns (use the first available)
    target_cols = [c for c in ["yield_strength", "ductility"] if c in train_df.columns]
    if not target_cols:
        raise ValueError("No target columns found in training data.")
    target = target_cols[0]

    feature_cols = [c for c in train_df.columns if c not in target_cols]

    X_train = train_df[feature_cols].values
    y_train = train_df[target].values

    # Train Linear Regression baseline
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Save model
    model_dir = Path(get_results_dir()) / "model"
    ensure_directories([model_dir])
    model_path = model_dir / "baseline_model.joblib"
    joblib.dump(model, model_path)
    logger.info(f"Baseline model saved to {model_path}")

if __name__ == "__main__":
    main()
