import os
import sys
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import lightgbm as lgb
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_training_data(data_path: Path) -> tuple:
    """Load training data."""
    df = pd.read_parquet(data_path)
    feature_cols = [c for c in df.columns if c not in ['smiles', 'target']]
    X = df[feature_cols].values
    y = df['target'].values
    return X, y

def train_final_model(X: np.ndarray, y: np.ndarray, params: Dict[str, Any]) -> lgb.Booster:
    """Train final model."""
    train_data = lgb.Dataset(X, label=y)
    model = lgb.train(params, train_data)
    return model

def save_model(model: lgb.Booster, output_path: Path) -> None:
    """Save model."""
    with open(output_path, "wb") as f:
        pickle.dump(model, f)

def main() -> None:
    """Main entry point."""
    data_path = Path("data/processed/splits_train.parquet")
    model_path = Path("data/processed/model.pkl")
    params = {"num_leaves": 31, "learning_rate": 0.05, "n_estimators": 100}
    
    X, y = load_training_data(data_path)
    model = train_final_model(X, y, params)
    save_model(model, model_path)
    logger.info(f"Model saved to {model_path}")

if __name__ == "__main__":
    main()
