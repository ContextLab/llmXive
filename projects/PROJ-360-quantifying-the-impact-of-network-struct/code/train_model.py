"""
Train a Linear Regression Model on Filtered Features.

Reads filtered features from data/processed/filtered_features.csv,
trains a model, and saves it to models/thermal_predictor.pkl.
"""
import os
import sys
import logging
import pickle
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error

# Add project root to path
project_root = Path(__file__).parent.parent
sys_path = str(project_root)
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from config import Config, initialize_environment

def setup_model_logger():
    logger = logging.getLogger("train_model")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def load_filtered_features(path: str, logger: logging.Logger) -> pd.DataFrame:
    """Load filtered features CSV."""
    logger.info(f"Loading filtered features from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Filtered features file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    
    # Verify required columns
    required_cols = ['unit_cell_volume', 'total_atom_count', 'mean_atomic_mass']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        raise ValueError(f"Missing required columns: {missing}")
    
    return df

def train_linear_model(df: pd.DataFrame, target_col: str = 'thermal_conductivity_scalar', logger: logging.Logger = None) -> LinearRegression:
    """Train a linear regression model."""
    if logger is None:
        logger = logging.getLogger("train_model")
    
    # Drop rows with NaN in target or features
    clean_df = df.dropna(subset=[target_col] + [c for c in df.columns if c != 'material_id'])
    
    if len(clean_df) < 2:
        logger.error("Not enough data to train model.")
        raise ValueError("Not enough data to train model.")
    
    # Features: all numeric columns except material_id and target
    feature_cols = [c for c in clean_df.columns if c not in ['material_id', target_col] and clean_df[c].dtype in ['float64', 'int64']]
    
    if not feature_cols:
        logger.error("No feature columns found.")
        raise ValueError("No feature columns found.")
    
    X = clean_df[feature_cols]
    y = clean_df[target_col]
    
    logger.info(f"Training with features: {feature_cols}")
    logger.info(f"Target: {target_col}")
    logger.info(f"Training samples: {len(X)}")
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Evaluate on training set (simple check)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    rmse = mean_squared_error(y, y_pred, squared=False)
    
    logger.info(f"Training R2: {r2:.4f}, RMSE: {rmse:.4f}")
    
    return model

def save_model(model: LinearRegression, path: str, logger: logging.Logger):
    """Save model to pickle."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Saved model to {path}")

def main():
    logger = setup_model_logger()
    initialize_environment()
    
    input_path = os.environ.get("FILTERED_FEATURES_INPUT", str(project_root / "data" / "processed" / "filtered_features.csv"))
    output_path = os.environ.get("MODEL_OUTPUT", str(project_root / "models" / "thermal_predictor.pkl"))

    try:
        df = load_filtered_features(input_path, logger)
        model = train_linear_model(df, logger=logger)
        save_model(model, output_path, logger)
        logger.info("Model training completed.")
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()