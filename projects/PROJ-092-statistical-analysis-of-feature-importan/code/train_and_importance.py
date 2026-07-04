"""
Model Training and Importance Calculation Module.

Handles training Random Forest models, evaluating performance,
and calculating permutation importance.
"""
import os
import sys
import logging
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logger import setup_logger, get_logger

logger = setup_logger("train_and_importance")

def load_window_data(filepath: Path) -> pd.DataFrame:
    """Load a specific window CSV file."""
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return None
    return pd.read_csv(filepath)

def prepare_features_target(df: pd.DataFrame) -> tuple:
    """
    Prepare features (X) and target (y) from DataFrame.
    Assumes the last column is the target variable.
    
    Returns:
        tuple: (X, y, feature_names)
    """
    if df.empty:
        return None, None, []
    
    # Assume last column is target
    feature_cols = df.columns[:-1]
    target_col = df.columns[-1]
    
    X = df[feature_cols].values
    y = df[target_col].values
    feature_names = list(feature_cols)
    
    return X, y, feature_names

def train_model(X: np.ndarray, y: np.ndarray, n_estimators: int = 100, max_depth: int = 10, random_state: int = 42):
    """Train a Random Forest Regressor."""
    logger.info(f"Training RandomForest (n={n_estimators}, d={max_depth})...")
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X, y)
    return model

def evaluate_model(model, X: np.ndarray, y: np.ndarray) -> float:
    """Calculate R² score on the training data (or provided test data)."""
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    return r2

def validate_model_performance(r2_score: float, threshold: float = 0.8) -> tuple:
    """
    Validate if the model performance meets the threshold.
    
    Args:
        r2_score: The calculated R² score
        threshold: Minimum acceptable R² (default 0.8)
    
    Returns:
        tuple: (is_valid: bool, reason: str)
    """
    if r2_score >= threshold:
        return True, "Valid"
    else:
        return False, f"R² ({r2_score:.4f}) < {threshold}"

def calculate_importance(model, X: np.ndarray, y: np.ndarray, feature_names: list, n_repeats: int = 10, random_state: int = 42) -> dict:
    """
    Calculate permutation importance.
    
    Returns:
        dict: {feature_name: importance_score}
    """
    logger.info("Calculating permutation importance...")
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        n_jobs=-1
    )
    
    importance_dict = {}
    for i, name in enumerate(feature_names):
        importance_dict[name] = result.importances_mean[i]
    
    return importance_dict

def save_importance_profile(importance_dict: dict, feature_names: list, output_path: Path):
    """Save the importance profile to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = []
    for feat in feature_names:
        score = importance_dict.get(feat, 0.0)
        data.append({"feature": feat, "importance": score})
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved importance profile to {output_path}")

def train_and_compute_importance(window_path: Path) -> dict:
    """
    End-to-end training and importance calculation for a single window.
    Returns a dict with results or None if validation fails.
    """
    df = load_window_data(window_path)
    if df is None or df.empty:
        return None
    
    X, y, feature_names = prepare_features_target(df)
    if X is None:
        return None
    
    model = train_model(X, y)
    r2 = evaluate_model(model, X, y)
    
    is_valid, reason = validate_model_performance(r2)
    if not is_valid:
        logger.warning(f"Model validation failed: {reason}")
        return None
    
    importance = calculate_importance(model, X, y, feature_names)
    
    return {
        "r2_score": r2,
        "importance_scores": importance,
        "model": model
    }

def main():
    """Main entry point for testing a single window."""
    logger.info("Running train_and_importance module test...")
    # This is usually called by main.py
    # Example:
    # window_path = Path("data/processed/window_001.csv")
    # result = train_and_compute_importance(window_path)
    # if result:
    #     print(f"R2: {result['r2_score']}, Importance: {result['importance_scores']}")

if __name__ == "__main__":
    main()
