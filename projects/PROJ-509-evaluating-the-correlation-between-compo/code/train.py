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

from config import load_paths
from utils.logging import get_logger

def load_data() -> pd.DataFrame:
    """Load the processed dataset with computed descriptors."""
    paths = load_paths()
    data_path = paths['data_processed'] / 'computed_descriptors.csv'
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")
    return pd.read_csv(data_path)

def perform_stratified_split(df: pd.DataFrame, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform an 80/20 stratified split by Crystal System.

    Args:
        df: DataFrame containing the dataset
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (train_df, val_df)
    """
    if 'crystal_system' not in df.columns:
        raise ValueError("Column 'crystal_system' not found in dataset")

    train_df, val_df = train_test_split(
        df,
        test_size=0.2,
        stratify=df['crystal_system'],
        random_state=random_state
    )
    return train_df, val_df

def train_models(train_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Train Random Forest and Gradient Boosting models.

    Args:
        train_df: Training DataFrame

    Returns:
        Dictionary of trained models
    """
    target = 'formation_energy_per_atom'
    features = [col for col in train_df.columns if col not in ['formation_energy_per_atom', 'crystal_system']]

    # Train Random Forest
    rf_model = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42)
    rf_model.fit(train_df[features], train_df[target])

    # Train Gradient Boosting
    gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    gb_model.fit(train_df[features], train_df[target])

    return {
        'rf': rf_model,
        'gb': gb_model
    }

def save_artifacts(models: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Save trained models to a temporary location for evaluation.

    Args:
        models: Dictionary of trained models
        logger: Logger instance
    """
    paths = load_paths()
    models_path = paths['data_evaluation'] / 'temp_models.pkl'

    # Ensure directory exists
    models_path.parent.mkdir(parents=True, exist_ok=True)

    # Save models as pickle
    import pickle
    with open(models_path, 'wb') as f:
        pickle.dump(models, f)

    logger.info(f"Successfully saved model artifacts to {models_path}")

def main() -> None:
    """Main entry point for model training."""
    logger = get_logger(__name__)

    # Load data
    df = load_data()
    logger.info(f"Loaded dataset with {len(df)} rows")

    # Perform stratified split
    train_df, val_df = perform_stratified_split(df)
    logger.info(f"Train size: {len(train_df)}, Val size: {len(val_df)}")

    # Train models
    models = train_models(train_df)
    logger.info(f"Trained models: {list(models.keys())}")

    # Save artifacts
    save_artifacts(models, logger)

    logger.info("Training completed successfully")

if __name__ == "__main__":
    main()
