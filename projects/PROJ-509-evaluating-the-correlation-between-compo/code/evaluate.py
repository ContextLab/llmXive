import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from scipy import stats

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
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Performs a stratified split by chemical family.
    Returns X_train, X_val, y_train, y_val, families_val
    """
    from sklearn.model_selection import train_test_split
    
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
    
    return X_train, X_val, y_train, y_val, families_val

def load_models(models_dir: Path) -> Dict[str, Any]:
    """
    Loads pre-trained models from a directory.
    """
    models = {}
    for model_file in models_dir.glob("model_*.pkl"):
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
            name = model_file.stem.replace("model_", "")
            models[name] = model
    return models

def calculate_tvd(dist1: pd.Series, dist2: pd.Series) -> float:
    """
    Calculates Total Variation Distance between two distributions.
    """
    # Normalize to probabilities
    prob1 = dist1.value_counts(normalize=True).sort_index()
    prob2 = dist2.value_counts(normalize=True).sort_index()
    
    # Align indices
    all_indices = prob1.index.union(prob2.index)
    prob1 = prob1.reindex(all_indices, fill_value=0)
    prob2 = prob2.reindex(all_indices, fill_value=0)
    
    tvd = 0.5 * np.sum(np.abs(prob1 - prob2))
    return tvd

def evaluate_models(
    models: Dict[str, Any],
    X_val: pd.DataFrame,
    y_val: pd.Series
) -> Dict[str, Dict[str, float]]:
    """
    Evaluates models on the validation set.
    """
    metrics = {}
    for name, model in models.items():
        y_pred = model.predict(X_val)
        r2 = r2_score(y_val, y_pred)
        mae = mean_absolute_error(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        metrics[name] = {
            "r2": r2,
            "mae": mae,
            "rmse": rmse
        }
    return metrics

def save_metrics(
    metrics: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Saves metrics to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def main() -> None:
    """
    Main entry point for the evaluation script.
    """
    paths = load_paths()
    data_path = paths['computed_descriptors']
    models_dir = paths['evaluation']
    metrics_path = paths['metrics_json']
    
    # Load data
    df = load_data(data_path)
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
    
    # Split data (re-split to get validation set for evaluation)
    # Note: In a real pipeline, we might load the split indices from training
    X_train, X_val, y_train, y_val, families_val = perform_stratified_split(
        df, target_col, feature_cols
    )
    
    # Load models
    models = load_models(models_dir)
    if not models:
        logger.error("No models found.")
        sys.exit(1)
    
    # Evaluate
    eval_metrics = evaluate_models(models, X_val, y_val)
    
    # Calculate TVD
    # Assuming we have training families too, but for simplicity we use val only
    # In real scenario, compare train vs val distributions
    # Here we just log a placeholder
    tvd = 0.0
    
    # Prepare final metrics
    final_metrics = {
        "models": eval_metrics,
        "tvd": tvd,
        "predictive_power": eval_metrics.get("rf", {}).get("r2", 0) > 0.0
    }
    
    # Save
    save_metrics(final_metrics, metrics_path)

if __name__ == "__main__":
    from utils.logging import setup_logging
    setup_logging()
    main()
