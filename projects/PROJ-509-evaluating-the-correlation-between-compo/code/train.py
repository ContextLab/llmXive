import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import pickle

from config import load_paths
from utils.logging import get_logger
from utils.chemical_families import assign_chemical_family
from utils.io import load_dataframe_safely

logger = get_logger(__name__)

def load_data(input_path: Path) -> pd.DataFrame:
    """Loads the dataset from a CSV file."""
    return load_dataframe_safely(input_path)

def perform_stratified_split(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Performs a stratified split by chemical family.
    """
    # Assign chemical family to each row
    df = df.copy()
    df['chemical_family'] = df['dominant_element'].apply(assign_chemical_family)
    
    X = df[feature_cols]
    y = df[target_col]
    families = df['chemical_family']
    
    X_train, X_val, y_train, y_val, families_train, families_val = train_test_split(
        X, y, families,
        test_size=test_size,
        random_state=random_state,
        stratify=families
    )
    
    return X_train, X_val, y_train, y_val

def load_models(models_dir: Path) -> Dict[str, Any]:
    """
    Loads pre-trained models from a directory.
    """
    models = {}
    for model_file in models_dir.glob("*.pkl"):
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
            models[model_file.stem] = model
    return models

def train_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series
) -> Dict[str, Any]:
    """
    Trains Random Forest and Gradient Boosting models.
    """
    models = {}
    
    # Random Forest
    logger.info("Training Random Forest...")
    rf = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42)
    rf.fit(X_train, y_train)
    models['rf'] = rf
    
    # Gradient Boosting
    logger.info("Training Gradient Boosting...")
    gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
    gb.fit(X_train, y_train)
    models['gb'] = gb
    
    return models

def save_artifacts(
    models: Dict[str, Any],
    metrics: Dict[str, Any],
    output_dir: Path
) -> None:
    """
    Saves models and metrics to the output directory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for name, model in models.items():
        model_path = output_dir / f"model_{name}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Saved model {name} to {model_path}")
    
    metrics_path = output_dir / "model_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")

def main() -> None:
    """
    Main entry point for the training script.
    """
    paths = load_paths()
    input_path = paths['computed_descriptors']
    output_dir = paths['evaluation']
    
    # Load data
    df = load_data(input_path)
    if df is None:
        logger.error("Failed to load data.")
        sys.exit(1)
    
    # Define features and target
    feature_cols = [
        "mean_electronegativity", "variance_electronegativity",
        "mean_radius", "variance_radius",
        "mean_valence", "variance_valence",
        "mean_melting_point", "variance_melting_point",
        "mean_ionization_energy", "variance_ionization_energy"
    ]
    target_col = "formation_energy"
    
    # Split data
    X_train, X_val, y_train, y_val = perform_stratified_split(
        df, target_col, feature_cols
    )
    
    # Train models
    models = train_models(X_train, y_train, X_val, y_val)
    
    # Dummy metrics for now (real metrics computed in evaluate.py)
    metrics = {
        "rf_train_r2": 0.0,
        "rf_val_r2": 0.0,
        "gb_train_r2": 0.0,
        "gb_val_r2": 0.0
    }
    
    # Save artifacts
    save_artifacts(models, metrics, output_dir)

if __name__ == "__main__":
    from utils.logging import setup_logging
    setup_logging()
    main()
