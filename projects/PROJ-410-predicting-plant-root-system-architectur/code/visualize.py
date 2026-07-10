"""
Visualization module for root architecture prediction results.
Handles SHAP values, Lasso coefficients, and plotting.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.linear_model import Lasso

# Import config for paths and hyperparameters
from config import HYPERPARAMETERS, DATA_PROCESSED_DIR, DATA_FIGURES_DIR, RANDOM_SEED

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_model(model_path: str):
    """Load a trained model from disk."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    logger.info(f"Loading model from {model_path}")
    return joblib.load(model_path)

def load_split_data(data_path: str):
    """Load processed data splits."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    logger.info(f"Loading data from {data_path}")
    return pd.read_parquet(data_path)

def calculate_shap_values(model, X: pd.DataFrame, model_type: str = 'tree') -> np.ndarray:
    """
    Calculate SHAP values for a model.
    Note: This function assumes a tree-based model or a compatible explainer.
    """
    try:
        import shap
        logger.info("Calculating SHAP values...")
        if model_type == 'tree':
            explainer = shap.TreeExplainer(model)
        else:
            # Fallback for linear models if needed, though T044 focuses on coefficients
            explainer = shap.LinearExplainer(model, X)
        
        shap_values = explainer.shap_values(X)
        return shap_values
    except ImportError:
        logger.warning("SHAP library not installed. Skipping SHAP calculation.")
        return None

def extract_lasso_coefficients(model: Lasso, feature_names: List[str]) -> pd.DataFrame:
    """
    Extract Lasso coefficients and return as a DataFrame.
    
    Args:
        model: Trained Lasso model.
        feature_names: List of feature names corresponding to coefficients.
        
    Returns:
        DataFrame with 'feature', 'coefficient', and 'abs_coefficient' columns.
        Sorted by absolute coefficient magnitude.
    """
    if not isinstance(model, Lasso):
        raise TypeError("Expected a Lasso model instance.")
    
    coeffs = model.coef_
    intercept = model.intercept_
    
    df = pd.DataFrame({
        'feature': feature_names,
        'coefficient': coeffs,
        'abs_coefficient': np.abs(coeffs)
    })
    
    # Sort by absolute magnitude descending
    df = df.sort_values(by='abs_coefficient', ascending=False)
    
    logger.info(f"Extracted {len(df)} coefficients. Non-zero features: {(df['coefficient'] != 0).sum()}")
    return df

def plot_shap_summary(shap_values, feature_names: List[str], save_path: str):
    """Generate and save a SHAP summary plot."""
    if shap_values is None:
        logger.warning("SHAP values are None. Skipping SHAP summary plot.")
        return

    plt.figure(figsize=(10, 8))
    # Using a simplified bar plot if the full SHAP plot is too complex or requires specific input
    # For this implementation, we'll create a summary importance plot based on mean absolute SHAP
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    
    # Ensure shape matches feature names
    if len(mean_abs_shap) != len(feature_names):
        logger.error(f"Shape mismatch: SHAP values {len(mean_abs_shap)} vs features {len(feature_names)}")
        return

    # Sort features
    indices = np.argsort(mean_abs_shap)[::-1]
    top_n = min(20, len(indices))
    
    plt.barh(range(top_n), mean_abs_shap[indices][:top_n])
    plt.yticks(range(top_n), [feature_names[i] for i in indices[:top_n]])
    plt.xlabel('Mean |SHAP Value|')
    plt.title('Top 20 Feature Importance (SHAP)')
    plt.gca().invert_yaxis()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"SHAP summary plot saved to {save_path}")

def plot_feature_importance_from_shap(shap_values, feature_names: List[str], save_path: str):
    """Alias for summary plot or specific feature importance view."""
    plot_shap_summary(shap_values, feature_names, save_path)

def plot_lasso_coefficients(coefficient_df: pd.DataFrame, save_path: str, top_n: int = 20):
    """
    Plot the top N Lasso coefficients by absolute magnitude.
    
    Args:
        coefficient_df: DataFrame from extract_lasso_coefficients.
        save_path: Path to save the figure.
        top_n: Number of top features to display.
    """
    plt.figure(figsize=(12, 8))
    
    # Select top N
    top_df = coefficient_df.head(top_n)
    
    # Sort by coefficient value for the plot (not absolute)
    top_df = top_df.sort_values(by='coefficient')
    
    plt.barh(top_df['feature'], top_df['coefficient'], color='skyblue')
    plt.xlabel('Coefficient Value')
    plt.title(f'Top {top_n} Lasso Coefficients')
    plt.axvline(0, color='black', linewidth=1)
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Lasso coefficient plot saved to {save_path}")

def main():
    """
    Main entry point for visualization tasks.
    Specifically handles Lasso coefficient extraction and plotting as per T044.
    """
    parser = argparse.ArgumentParser(description="Visualize model results")
    parser.add_argument('--model_path', type=str, required=True, help="Path to the trained Lasso model (.pkl)")
    parser.add_argument('--data_path', type=str, required=True, help="Path to the processed data parquet file")
    parser.add_argument('--output_dir', type=str, default=str(DATA_FIGURES_DIR), help="Output directory for figures")
    parser.add_argument('--model_type', type=str, default='lasso', help="Type of model (lasso, tree)")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Load model
        model = load_model(args.model_path)
        
        # Load data to get feature names
        # We only need the header to get feature names, not the full data if large
        # But for safety with parquet, we load a small sample or just the columns
        df = load_split_data(args.data_path)
        
        # Assume the last column is the target, or we need to know the target name.
        # For Lasso coefficients, we need the feature columns used for training.
        # We'll assume the data file has 'target' column and all others are features.
        feature_cols = [c for c in df.columns if c != 'target']
        
        if args.model_type == 'lasso':
            logger.info("Processing Lasso coefficients...")
            coeffs = extract_lasso_coefficients(model, feature_cols)
            
            # Save coefficients to CSV
            csv_path = os.path.join(args.output_dir, "lasso_coefficients.csv")
            coeffs.to_csv(csv_path, index=False)
            logger.info(f"Lasso coefficients saved to {csv_path}")
            
            # Plot coefficients
            plot_path = os.path.join(args.output_dir, "lasso_coefficients_plot.png")
            plot_lasso_coefficients(coeffs, plot_path, top_n=20)
            
        elif args.model_type == 'tree':
            logger.info("Processing Tree model SHAP values...")
            # We need X for SHAP
            X = df[feature_cols]
            shap_vals = calculate_shap_values(model, X, model_type='tree')
            
            if shap_vals is not None:
                shap_plot_path = os.path.join(args.output_dir, "shap_summary.png")
                plot_shap_summary(shap_vals, feature_cols, shap_plot_path)
        else:
            logger.warning(f"Unknown model type: {args.model_type}")
            
    except Exception as e:
        logger.error(f"Visualization failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()