import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score

from config import load_paths
from utils.logging import get_logger
from evaluate import perform_stratified_split

logger = get_logger(__name__)

def load_data(data_path: Path) -> pd.DataFrame:
    """Load processed dataset.
    
    Args:
        data_path: Path to CSV file.
        
    Returns:
        Loaded DataFrame.
    """
    return pd.read_csv(data_path)

def load_models(model_path: Path) -> Dict[str, Any]:
    """Load existing models if any.
    
    Args:
        model_path: Path to model directory.
        
    Returns:
        Dictionary of models.
    """
    return {}

def train_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_estimators_rf: int = 200,
    max_depth: int = 20,
    random_state: int = 42
) -> Tuple[Any, Any]:
    """Train Random Forest and Gradient Boosting models.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        n_estimators_rf: Number of trees for RF.
        max_depth: Max depth for RF.
        random_state: Random seed.
        
    Returns:
        Tuple of (rf_model, gb_model).
    """
    rf = RandomForestRegressor(
        n_estimators=n_estimators_rf,
        max_depth=max_depth,
        random_state=random_state
    )
    rf.fit(X_train, y_train)
    
    gb = GradientBoostingRegressor(
        n_estimators=100,
        random_state=random_state
    )
    gb.fit(X_train, y_train)
    
    return rf, gb

def save_artifacts(
    rf_model: Any,
    gb_model: Any,
    output_path: Path
) -> None:
    """Save trained models to disk.
    
    Args:
        rf_model: Random Forest model.
        gb_model: Gradient Boosting model.
        output_path: Output directory.
    """
    import pickle
    
    rf_path = output_path / "model_rf.pkl"
    gb_path = output_path / "model_gb.pkl"
    
    with open(rf_path, "wb") as f:
        pickle.dump(rf_model, f)
    with open(gb_path, "wb") as f:
        pickle.dump(gb_model, f)
    
    logger.info(f"Models saved to {output_path}")

def main() -> None:
    """Main entry point for training."""
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
    
    # Train models
    logger.info("Training Random Forest")
    logger.info("Training Gradient Boosting")
    rf_model, gb_model = train_models(X_train, y_train)
    
    # Save artifacts
    output_path = paths["data_evaluation"]
    output_path.mkdir(parents=True, exist_ok=True)
    save_artifacts(rf_model, gb_model, output_path)
    
    # Cross-validation scores
    cv_scores = cross_val_score(rf_model, X_train, y_train, cv=5, scoring="r2")
    cv_results = {
        "mean_r2": float(cv_scores.mean()),
        "std_r2": float(cv_scores.std())
    }
    cv_path = output_path / "cv_scores.json"
    with open(cv_path, "w") as f:
        json.dump(cv_results, f, indent=2)
    
    logger.info(f"Training complete. CV R2: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

if __name__ == "__main__":
    main()
