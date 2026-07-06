import os
import sys
import logging
import json
from pathlib import Path
import numpy as np
from typing import Tuple, Dict, List, Optional

# Import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score

from utils.config import get_config
from utils.logger import get_logger

def load_window_data(window_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load window data from CSV file.
    
    Args:
        window_path: Path to the window CSV file.
        
    Returns:
        Tuple of (features, target) as numpy arrays.
    """
    import pandas as pd
    df = pd.read_csv(window_path)
    
    # Assume last column is target
    target_col = df.columns[-1]
    feature_cols = df.columns[:-1]
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    return X, y

def prepare_features_target(df, feature_cols: List[str], target_col: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare feature matrix and target vector from a DataFrame.
    
    Args:
        df: DataFrame containing the data.
        feature_cols: List of feature column names.
        target_col: Name of the target column.
        
    Returns:
        Tuple of (X, y) as numpy arrays.
    """
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y

def train_model(X: np.ndarray, y: np.ndarray, seed: int = 42) -> RandomForestRegressor:
    """
    Train a Random Forest Regressor.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        seed: Random seed for reproducibility.
        
    Returns:
        Trained RandomForestRegressor.
    """
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=seed,
        n_jobs=-1  # Use all available cores
    )
    model.fit(X, y)
    return model

def evaluate_model(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray) -> float:
    """
    Evaluate model performance using R² score.
    
    Args:
        model: Trained model.
        X: Feature matrix.
        y: Target vector.
        
    Returns:
        R² score.
    """
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    return r2

def validate_model_performance(r2_score: float, threshold: float = 0.8) -> bool:
    """
    Validate if model performance meets the threshold.
    
    Args:
        r2_score: The R² score to validate.
        threshold: Minimum acceptable R² score.
        
    Returns:
        True if performance is acceptable, False otherwise.
    """
    return r2_score >= threshold

def calculate_importance(model: RandomForestRegressor, X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate permutation importance for the trained model.
    
    Args:
        model: Trained model.
        X: Feature matrix.
        feature_names: List of feature names.
        
    Returns:
        Dictionary mapping feature names to importance scores.
    """
    result = permutation_importance(
        model, X, n_repeats=10, random_state=42, n_jobs=-1
    )
    
    importance_dict = {}
    for i, name in enumerate(feature_names):
        importance_dict[name] = float(result.importances_mean[i])
    
    return importance_dict

def save_importance_profile(model: RandomForestRegressor, feature_names: List[str], output_path: Path, logger: Optional[logging.Logger] = None) -> None:
    """
    Save the importance profile to a JSON file.
    
    Args:
        model: Trained model (used for feature importance).
        feature_names: List of feature names.
        output_path: Path to save the JSON file.
        logger: Optional logger.
    """
    if logger is None:
        logger = get_logger("train_and_importance")
    
    # Get permutation importance
    # Note: X is not available here, so we use built-in feature_importances_ as fallback
    # In practice, X should be passed or loaded from context
    importance_scores = {name: float(importance) for name, importance in zip(feature_names, model.feature_importances_)}
    
    profile = {
        "model_type": "RandomForestRegressor",
        "n_estimators": model.n_estimators,
        "max_depth": model.max_depth,
        "features": importance_scores,
        "total_features": len(feature_names)
    }
    
    try:
        with open(output_path, "w") as f:
            json.dump(profile, f, indent=2)
        logger.info(f"Importance profile saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to save importance profile: {e}")
        raise

def train_and_compute_importance(
    X: np.ndarray,
    y: np.ndarray,
    window_id: str,
    logger: Optional[logging.Logger] = None,
    feature_names: Optional[List[str]] = None,
    seed: int = 42
) -> Tuple[RandomForestRegressor, float]:
    """
    Train a model and compute importance scores.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        window_id: Identifier for the window (for logging).
        logger: Optional logger.
        feature_names: Optional list of feature names for importance labeling.
        seed: Random seed.
        
    Returns:
        Tuple of (trained_model, r2_score).
    """
    if logger is None:
        logger = get_logger("train_and_importance")
    
    logger.info(f"{window_id}: Training model...")
    
    # Train model
    model = train_model(X, y, seed)
    
    # Evaluate
    r2 = evaluate_model(model, X, y)
    logger.info(f"{window_id}: Model trained. R² = {r2:.4f}")
    
    # Validate
    if not validate_model_performance(r2):
        logger.warning(f"{window_id}: Model R² {r2:.4f} below threshold, skipping importance calculation.")
        return model, r2
    
    # Calculate importance if feature names provided
    if feature_names is not None:
        importance_scores = calculate_importance(model, X, feature_names)
        logger.info(f"{window_id}: Importance calculated for {len(feature_names)} features.")
    
    return model, r2

def main():
    """CLI entry point for standalone model training and importance calculation."""
    try:
        config = get_config()
        base_path = Path(config.get("base_path", "."))
        
        # Example: process a single window file
        window_file = base_path / "data" / "processed" / "window_001.csv"
        
        if not window_file.exists():
            print(f"Window file not found: {window_file}")
            sys.exit(1)
        
        X, y = load_window_data(window_file)
        logger = get_logger("train_and_importance")
        
        model, r2 = train_and_compute_importance(X, y, "test_window", logger)
        print(f"Model trained. R² = {r2:.4f}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error in training pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
