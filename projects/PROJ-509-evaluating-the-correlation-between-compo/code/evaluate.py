import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import cross_val_score
from scipy import stats

from config import load_paths
from utils.logging import get_logger
from utils.chemical_families import assign_chemical_family

logger = get_logger(__name__)

def load_data(path: Path) -> pd.DataFrame:
    """Load processed dataset.
    
    Args:
        path: Path to CSV file.
        
    Returns:
        Loaded DataFrame.
    """
    return pd.read_csv(path)

def perform_stratified_split(
    df: pd.DataFrame,
    target_col: str = "chemical_family",
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Perform stratified split by chemical family.
    
    Args:
        df: Input DataFrame.
        target_col: Column to stratify by.
        test_size: Fraction for test set.
        random_state: Random seed.
        
    Returns:
        Tuple of (train_df, test_df).
    """
    df = df.copy()
    if target_col not in df.columns:
        df[target_col] = df["composition"].apply(
            lambda x: assign_chemical_family(x.split()[0] if " " in x else x)
        )
    
    train_idx, test_idx = [], []
    for family, group in df.groupby(target_col):
        n_test = int(len(group) * test_size)
        indices = group.index.tolist()
        np.random.seed(random_state)
        np.random.shuffle(indices)
        test_idx.extend(indices[:n_test])
        train_idx.extend(indices[n_test:])
    
    return df.loc[train_idx], df.loc[test_idx]

def load_models(model_path: Path) -> Dict[str, Any]:
    """Load trained models from pickle files.
    
    Args:
        model_path: Directory containing model files.
        
    Returns:
        Dictionary of loaded models.
    """
    models = {}
    rf_path = model_path / "model_rf.pkl"
    gb_path = model_path / "model_gb.pkl"
    
    if rf_path.exists():
        with open(rf_path, "rb") as f:
            models["rf"] = pickle.load(f)
    if gb_path.exists():
        with open(gb_path, "rb") as f:
            models["gb"] = pickle.load(f)
    
    return models

def calculate_tvd(dist1: pd.Series, dist2: pd.Series) -> float:
    """Calculate Total Variation Distance between two distributions.
    
    Args:
        dist1: First distribution.
        dist2: Second distribution.
        
    Returns:
        TVD value.
    """
    total = 0
    all_vals = set(dist1.unique()).union(dist2.unique())
    for val in all_vals:
        p1 = (dist1 == val).sum() / len(dist1)
        p2 = (dist2 == val).sum() / len(dist2)
        total += abs(p1 - p2)
    return total / 2

def evaluate_models(
    models: Dict[str, Any],
    X_test: pd.DataFrame,
    y_test: pd.Series,
    X_train: Optional[pd.DataFrame] = None,
    y_train: Optional[pd.Series] = None
) -> Dict[str, Dict[str, float]]:
    """Evaluate models on test set.
    
    Args:
        models: Dictionary of models.
        X_test: Test features.
        y_test: Test targets.
        X_train: Training features (optional).
        y_train: Training targets (optional).
        
    Returns:
        Dictionary of metrics per model.
    """
    metrics = {}
    for name, model in models.items():
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        metrics[name] = {
            "r2": r2,
            "mae": mae,
            "rmse": rmse
        }
        
        if X_train is not None and y_train is not None:
            y_train_pred = model.predict(X_train)
            train_r2 = r2_score(y_train, y_train_pred)
            metrics[name]["train_r2"] = train_r2
            metrics[name]["overfitting_ratio"] = train_r2 - r2
    
    return metrics

def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """Save metrics to JSON file.
    
    Args:
        metrics: Metrics dictionary.
        output_path: Output file path.
    """
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

def main() -> None:
    """Main entry point for evaluation."""
    paths = load_paths()
    
    # Load data
    data_path = paths["data_processed"] / "computed_descriptors.csv"
    df = load_data(data_path)
    
    # Prepare features and target
    feature_cols = [c for c in df.columns if c not in ["composition", "formation_energy"]]
    X = df[feature_cols]
    y = df["formation_energy"]
    
    # Stratified split
    train_df, test_df = perform_stratified_split(df)
    X_train, y_train = train_df[feature_cols], train_df["formation_energy"]
    X_test, y_test = test_df[feature_cols], test_df["formation_energy"]
    
    # Load models
    model_path = paths["data_evaluation"]
    models = load_models(model_path)
    
    if not models:
        raise RuntimeError("No models found for evaluation")
    
    # Evaluate
    metrics = evaluate_models(models, X_test, y_test, X_train, y_train)
    
    # Calculate TVD
    tvd = calculate_tvd(train_df["chemical_family"], test_df["chemical_family"])
    metrics["tvd"] = tvd
    
    # Add metadata
    metrics["final_r2_source"] = "holdout"
    
    # Save
    output_path = paths["data_evaluation"] / "model_metrics.json"
    save_metrics(metrics, output_path)
    
    logger.info(f"Metrics saved to {output_path}")

if __name__ == "__main__":
    main()
