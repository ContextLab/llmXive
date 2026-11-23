"""
Task T033: Model Validation - Generate Residual Plot
Generates a residual plot (predicted vs. actual thermal conductivity) to inspect
heteroscedasticity or bias. Saves the plot to results/model_residuals.png.
"""
import os
import sys
import pickle
import logging
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
from pathlib import Path

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config, initialize_environment
from utils import setup_logging

def setup_logger(name: str) -> logging.Logger:
    """Setup a dedicated logger for this module."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_model(model_path: str, logger: logging.Logger) -> object:
    """Load the trained linear regression model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. "
                                "Ensure T022 (train_model.py) has been run successfully.")
    logger.info(f"Loading model from {model_path}...")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info("Model loaded successfully.")
    return model

def load_data(features_path: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Load the filtered features dataset used for training.
    Expects 'filtered_features.csv' which contains features and the target column.
    """
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found at {features_path}. "
                                "Ensure T020b/T020c (filter_features) has been run.")
    logger.info(f"Loading features from {features_path}...")
    df = pd.read_csv(features_path)
    
    # Verify required columns exist
    required_cols = ['thermal_conductivity_scalar']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {features_path}: {missing}")
    
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def generate_residuals(model, df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Generate predictions and calculate residuals.
    Returns a DataFrame with 'actual', 'predicted', and 'residual' columns.
    """
    # Identify feature columns (exclude the target)
    feature_cols = [col for col in df.columns if col != 'thermal_conductivity_scalar']
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset to make predictions.")
    
    logger.info(f"Using {len(feature_cols)} features for prediction: {feature_cols}")
    
    X = df[feature_cols]
    y_actual = df['thermal_conductivity_scalar']
    
    # Handle potential NaNs in features if any (though filtered_features should be clean)
    if X.isnull().any().any():
        logger.warning("NaN values detected in feature matrix. Dropping rows with NaNs.")
        mask = ~X.isnull().any(axis=1)
        X = X[mask]
        y_actual = y_actual[mask]
    
    y_pred = model.predict(X)
    
    residuals = y_actual - y_pred
    
    result_df = pd.DataFrame({
        'actual': y_actual.values,
        'predicted': y_pred,
        'residual': residuals
    })
    
    logger.info(f"Generated {len(result_df)} residual records.")
    return result_df

def plot_residuals(residuals_df: pd.DataFrame, output_path: str, logger: logging.Logger) -> None:
    """
    Create a residual plot: Predicted vs Actual (with identity line) 
    and Residuals vs Predicted (with zero line).
    Saves to output_path.
    """
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    
    fig, axs = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Predicted vs Actual
    ax1 = axs[0]
    actual = residuals_df['actual']
    predicted = residuals_df['predicted']
    
    ax1.scatter(predicted, actual, alpha=0.6, edgecolors='k', s=50)
    ax1.plot([predicted.min(), predicted.max()], 
             [predicted.min(), predicted.max()], 
             'r--', lw=2, label='Ideal (y=x)')
    ax1.set_xlabel('Predicted Thermal Conductivity')
    ax1.set_ylabel('Actual Thermal Conductivity')
    ax1.set_title('Predicted vs Actual')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Residuals vs Predicted
    ax2 = axs[1]
    residuals = residuals_df['residual']
    
    ax2.scatter(predicted, residuals, alpha=0.6, edgecolors='k', s=50, c='darkblue')
    ax2.axhline(0, color='red', linestyle='--', lw=2, label='Zero Residual')
    ax2.set_xlabel('Predicted Thermal Conductivity')
    ax2.set_ylabel('Residuals (Actual - Predicted)')
    ax2.set_title('Residuals vs Predicted')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Check for patterns (heteroscedasticity)
    if len(residuals) > 0:
        std_dev = np.std(residuals)
        ax2.set_title(f'Residuals vs Predicted (Std Dev: {std_dev:.4f})')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Residual plot saved to {output_path}")

def main():
    """Main entry point for T033."""
    # Initialize environment and config
    initialize_environment()
    config = Config()
    
    # Setup logging
    logger = setup_logger("generate_residuals")
    setup_logging(level=logging.INFO)
    
    logger.info("Starting Task T033: Model Validation - Residual Plot Generation")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    model_path = project_root / "models" / "thermal_predictor.pkl"
    features_path = project_root / "data" / "processed" / "filtered_features.csv"
    output_path = project_root / "results" / "model_residuals.png"
    
    try:
        # 1. Load Model
        model = load_model(str(model_path), logger)
        
        # 2. Load Data
        df = load_data(str(features_path), logger)
        
        # 3. Generate Residuals
        residuals_df = generate_residuals(model, df, logger)
        
        # 4. Plot and Save
        plot_residuals(residuals_df, str(output_path), logger)
        
        logger.info("Task T033 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Prerequisites (T022, T020b) may not have completed or artifacts are missing.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during residual generation: {e}")
        raise

if __name__ == "__main__":
    main()
