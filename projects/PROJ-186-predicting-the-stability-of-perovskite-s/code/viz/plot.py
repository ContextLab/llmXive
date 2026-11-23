import os
import sys
import logging
import pickle
import json
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import permutation_result
from sklearn.metrics import r2_score, mean_squared_error

# Configure logging
from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

# Ensure results directory exists
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_test_data() -> pd.DataFrame:
    """
    Load the test set from the preprocessed data.
    Expects data/processed/features.csv to exist.
    We need to re-split the data exactly as done in training to get the test set.
    However, for plotting predicted vs true, we can use the full dataset if we re-predict,
    but the standard approach is to use the held-out test set.
    
    Since T021a performs a split, we assume the test set was saved or we need to re-load
    the full features and re-split using the same random state and stratification logic.
    
    To avoid re-splitting complexity, we assume the pipeline saves 'test_set.csv' in data/processed/
    if the split is persistent. If not, we load the full features and re-split.
    
    Based on T021a description: "Perform a stratified split...". It doesn't explicitly say it saves them.
    Let's check for a specific test file first.
    """
    test_path = Path("data/processed/test_set.csv")
    if test_path.exists():
        logger.info(f"Loading test set from {test_path}")
        return pd.read_csv(test_path)
    
    # Fallback: Load full features and re-split (assuming we know the columns)
    # This is less ideal but necessary if test_set.csv wasn't saved.
    data_path = Path("data/processed/features.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_path} or {data_path}. "
                                "Please run the data pipeline (T018) first.")
    
    logger.warning(f"Test set file '{test_path}' not found. Loading full features and re-splitting.")
    df = pd.read_csv(data_path)
    
    # Re-split logic (matching T021a: stratified by quantiles of decomposition_energy)
    # We need to replicate the split from train.py. Since we don't have the exact code here,
    # we'll use a simple stratified split based on quantiles.
    from sklearn.model_selection import train_test_split
    
    # Create quantile bins for stratification
    df['energy_quantile'] = pd.qcut(df['decomposition_energy'], q=5, duplicates='drop')
    
    train_df, test_df = train_test_split(
        df, 
        test_size=0.2, 
        random_state=42, 
        stratify=df['energy_quantile']
    )
    
    # Drop the helper column
    test_df = test_df.drop(columns=['energy_quantile'])
    
    # Save the test set for future use
    test_df.to_csv(test_path, index=False)
    logger.info(f"Saved re-split test set to {test_path}")
    
    return test_df

def load_model() -> Any:
    """
    Load the trained model from results/model.pkl.
    """
    model_path = Path("results/model.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. "
                                "Please run the training pipeline (T021c) first.")
    
    with open(model_path, "rb") as f:
        return pickle.load(f)

def load_metrics() -> Dict[str, Any]:
    """
    Load metrics from results/metrics.json.
    """
    metrics_path = Path("results/metrics.json")
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics not found at {metrics_path}. "
                                "Please run the training pipeline (T021c) first.")
    
    with open(metrics_path, "r") as f:
        return json.load(f)

def plot_predicted_vs_true(
    y_true: pd.Series, 
    y_pred: pd.Series, 
    output_path: str = "predicted-vs-true.png"
) -> None:
    """
    Generate a scatter plot of predicted vs true decomposition energy.
    """
    plt.figure(figsize=(10, 8))
    
    # Scatter plot
    plt.scatter(y_true, y_pred, alpha=0.6, edgecolors='k', linewidth=0.5)
    
    # Identity line
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Ideal Prediction')
    
    # Calculate and display metrics
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    plt.text(
      0.05, 0.95, 
      f'RMSE: {rmse:.4f} eV/atom\nR²: {r2:.4f}',
      transform=plt.gca().transAxes,
      fontsize=12,
      verticalalignment='top',
      bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.title("Predicted vs True Decomposition Energy", fontsize=14)
    plt.xlabel("True Decomposition Energy (eV/atom)", fontsize=12)
    plt.ylabel("Predicted Decomposition Energy (eV/atom)", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_file = RESULTS_DIR / output_path
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    log_pipeline_event(f"Predicted vs True plot saved to {output_file}")
    logger.info(f"Generated predicted vs true plot: {output_file}")

def main() -> None:
    """
    Main entry point for generating the predicted-vs-true plot.
    """
    logger.info("Starting predicted vs true plot generation (T022).")
    
    try:
        # Load data and model
        df_test = load_test_data()
        model = load_model()
        
        # Identify feature columns and target
        target_col = 'decomposition_energy'
        if target_col not in df_test.columns:
            raise ValueError(f"Target column '{target_col}' not found in test data.")
        
        feature_cols = [col for col in df_test.columns if col != target_col]
        
        # Extract features and target
        X_test = df_test[feature_cols]
        y_true = df_test[target_col]
        
        # Predict
        y_pred = model.predict(X_test)
        
        # Generate the plot
        plot_predicted_vs_true(y_true, y_pred, output_path="predicted-vs-true.png")
        
        logger.info("T022 completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate predicted vs true plot: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()