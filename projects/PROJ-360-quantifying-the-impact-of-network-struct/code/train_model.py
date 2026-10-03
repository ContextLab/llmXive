"""
T022: Train a linear regression model using filtered features.

Reads filtered features from data/processed/filtered_features.csv,
trains a Linear Regression model, and saves it to models/thermal_predictor.pkl.

Dependencies: T020b (filtered_features.csv must exist).
"""
import os
import sys
import logging
import pickle
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config, initialize_environment
from utils import pin_seed

def setup_model_logger():
    """Configure logging for the model training script."""
    logger = logging.getLogger("model_trainer")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_filtered_features(csv_path):
    """
    Load the filtered features CSV.
    
    Expected columns (based on T020b):
    - Feature columns (VIF filtered network metrics + physical descriptors)
    - Target column: 'thermal_conductivity_scalar'
    
    Returns:
        X (pd.DataFrame): Feature matrix
        y (pd.Series): Target vector
    """
    logger = logging.getLogger("model_trainer")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Filtered features file not found at {csv_path}. "
            "Ensure T020b (filter_features) has been run successfully."
        )
    
    df = pd.read_csv(csv_path)
    
    # Identify target column
    if 'thermal_conductivity_scalar' not in df.columns:
        raise ValueError(
            f"Target column 'thermal_conductivity_scalar' not found in {csv_path}. "
            f"Available columns: {list(df.columns)}"
        )
    
    # Separate features and target
    # We assume all columns except the target are features
    target_col = 'thermal_conductivity_scalar'
    feature_cols = [col for col in df.columns if col != target_col]
    
    if not feature_cols:
        raise ValueError(
            f"No feature columns found in {csv_path} excluding target."
        )
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]
    
    # Drop rows where target is NaN as well
    valid_mask = y.notna()
    X = X[valid_mask]
    y = y[valid_mask]
    
    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features.")
    
    if len(X) < 2:
        raise ValueError(
            f"Insufficient data for training. Found {len(X)} valid samples. "
            "Need at least 2."
        )
    
    return X, y

def train_linear_model(X, y, seed=42):
    """
    Train a Linear Regression model.
    
    Args:
        X (pd.DataFrame): Feature matrix
        y (pd.Series): Target vector
        seed (int): Random seed for reproducibility
        
    Returns:
        model (LinearRegression): Trained model
    """
    logger = logging.getLogger("model_trainer")
    pin_seed(seed)
    
    logger.info("Initializing Linear Regression model...")
    model = LinearRegression()
    
    logger.info("Fitting model...")
    model.fit(X, y)
    
    # Calculate training metrics for logging
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    
    logger.info(f"Training complete. R²: {r2:.4f}, RMSE: {rmse:.4f}")
    
    return model

def save_model(model, output_path):
    """
    Save the trained model to a pickle file.
    
    Args:
        model: Trained sklearn model
        output_path (str): Path to save the pickle file
    """
    logger = logging.getLogger("model_trainer")
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Model saved to {output_path}")

def main():
    """Main entry point for T022."""
    logger = setup_model_logger()
    
    # Initialize config to ensure environment is ready
    initialize_environment()
    
    # Paths
    features_path = "data/processed/filtered_features.csv"
    model_path = "models/thermal_predictor.pkl"
    
    logger.info(f"Starting T022: Train Linear Regression Model")
    logger.info(f"Input: {features_path}")
    logger.info(f"Output: {model_path}")
    
    try:
        # Load data
        X, y = load_filtered_features(features_path)
        
        # Train model
        model = train_linear_model(X, y)
        
        # Save model
        save_model(model, model_path)
        
        logger.info("T022 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
