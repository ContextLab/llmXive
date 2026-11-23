"""
SHAP Visualization and Feature Importance Module.

This module handles the generation of SHAP summary plots, waterfall plots,
and feature importance tables for the oxidation resistance prediction models.
"""

import os
import sys
import argparse
import json
import logging
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap

from config import get_config_from_args
from utils.logger import get_logger

# Ensure matplotlib uses a non-interactive backend for server environments
plt.switch_backend('Agg')

logger = get_logger(__name__)

# Constants
MODEL_PATH = "data/processed/best_model.pkl"
PROCESSED_DATA_PATH = "data/processed/processed_data.csv"
FEATURE_IMPORTANCE_OUTPUT = "data/processed/feature_importance_table.json"
SHAP_SUMMARY_PLOT_PATH = "data/processed/shap_summary_plot.png"


def load_trained_model(model_path: str) -> Any:
    """
    Load the best trained model from disk.

    Args:
        model_path: Path to the pickled model file.

    Returns:
        The loaded model object.

    Raises:
        FileNotFoundError: If the model file does not exist.
        ImportError: If sklearn is not installed.
    """
    try:
        import joblib
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        
        logger.info(f"Loading model from {model_path}")
        model = joblib.load(model_path)
        logger.info("Model loaded successfully")
        return model
    except ImportError:
        logger.error("joblib not found. Please install scikit-learn.")
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def load_processed_data(data_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load processed data and separate features from target.

    Args:
        data_path: Path to the processed CSV file.

    Returns:
        Tuple of (feature_matrix, target_series).
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data file not found at: {data_path}")
    
    logger.info(f"Loading processed data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Assume the last column is the target 'observed_weight_gain'
    # This aligns with the data model in T004
    feature_cols = [col for col in df.columns if col != 'observed_weight_gain']
    
    if 'observed_weight_gain' not in df.columns:
        raise ValueError("Target column 'observed_weight_gain' not found in data.")
    
    X = df[feature_cols]
    y = df['observed_weight_gain']
    
    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features")
    return X, y


def generate_shap_summary_plot(model: Any, X: pd.DataFrame, output_path: str) -> None:
    """
    Generate and save a SHAP summary plot.

    Args:
        model: The trained model.
        X: Feature matrix.
        output_path: Path to save the plot.
    """
    logger.info("Generating SHAP summary plot...")
    
    # Create SHAP explainer
    # Use TreeExplainer for tree-based models (RF, GB) as it's faster and exact
    # Use KernelExplainer as fallback for other models (slower)
    try:
        if hasattr(model, 'feature_importances_'):
            explainer = shap.TreeExplainer(model)
            logger.info("Using TreeExplainer")
        else:
            # Fallback for Gaussian Process or others
            logger.warning("Model does not have feature_importances_. Using KernelExplainer (may be slow).")
            explainer = shap.KernelExplainer(model.predict, X)
    except Exception as e:
        logger.error(f"Failed to create explainer: {e}")
        raise

    # Calculate SHAP values
    # For large datasets, we sample to avoid memory issues during explain
    sample_size = min(500, len(X))
    X_sample = X.sample(n=sample_size, random_state=42)
    logger.info(f"Calculating SHAP values on {sample_size} samples")
    
    shap_values = explainer.shap_values(X_sample)
    
    # Handle multi-output SHAP values if necessary (regression usually single)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    
    # Generate plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_sample, show=False, plot_type="dot")
    plt.title("SHAP Summary Plot: Feature Impact on Oxidation Weight Gain")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"SHAP summary plot saved to {output_path}")


def generate_shap_waterfall_plot(model: Any, X: pd.DataFrame, sample_idx: int, output_path: str) -> None:
    """
    Generate a SHAP waterfall plot for a specific sample.

    Args:
        model: The trained model.
        X: Feature matrix.
        sample_idx: Index of the sample to explain.
        output_path: Path to save the plot.
    """
    logger.info(f"Generating SHAP waterfall plot for sample index {sample_idx}...")
    
    try:
        if hasattr(model, 'feature_importances_'):
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.KernelExplainer(model.predict, X)
    except Exception as e:
        logger.error(f"Failed to create explainer: {e}")
        raise

    # Select single sample
    sample = X.iloc[[sample_idx]]
    
    # Calculate SHAP values for this sample
    shap_values = explainer.shap_values(sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    
    # Create waterfall plot
    plt.figure(figsize=(10, 6))
    shap.waterfall_plot(shap.Explanation(values=shap_values, base_values=explainer.expected_value, data=sample.iloc[0].values, feature_names=X.columns))
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"SHAP waterfall plot saved to {output_path}")


def generate_feature_importance_table(model: Any, X: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Generate a feature importance table based on mean absolute SHAP values.

    This function calculates the mean absolute SHAP value for each feature
    across the dataset, providing a robust measure of feature importance
    that accounts for both positive and negative contributions.

    Args:
        model: The trained model.
        X: Feature matrix.
        output_path: Path to save the JSON report.

    Returns:
        Dictionary containing the feature importance table.
    """
    logger.info("Generating feature importance table via SHAP...")
    
    # Create explainer
    try:
        if hasattr(model, 'feature_importances_'):
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.KernelExplainer(model.predict, X)
    except Exception as e:
        logger.error(f"Failed to create explainer: {e}")
        raise

    # Sample for efficiency if dataset is large
    sample_size = min(1000, len(X))
    X_sample = X.sample(n=sample_size, random_state=42)
    
    # Calculate SHAP values
    shap_values = explainer.shap_values(X_sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    
    # Calculate mean absolute SHAP values
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    # Create DataFrame for sorting
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'mean_abs_shap_value': mean_abs_shap
    })
    
    # Sort by importance (descending)
    importance_df = importance_df.sort_values(by='mean_abs_shap_value', ascending=False)
    
    # Convert to list of dicts for JSON serialization
    feature_importance_list = importance_df.to_dict(orient='records')
    
    # Prepare the report
    report = {
        "description": "Feature importance ranked by mean absolute SHAP values",
        "method": "SHAP (TreeExplainer/KernelExplainer)",
        "sample_size": sample_size,
        "total_features": len(X.columns),
        "top_features": feature_importance_list
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to JSON
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Feature importance table saved to {output_path}")
    
    # Log top 5 features for quick verification
    top_5 = importance_df.head(5)
    logger.info("Top 5 Features:")
    for _, row in top_5.iterrows():
        logger.info(f"  {row['feature']}: {row['mean_abs_shap_value']:.4f}")
    
    return report


def main():
    """
    Main entry point for the SHAP visualization module.
    
    This script loads the trained model and processed data, then generates:
    1. SHAP Summary Plot
    2. Feature Importance Table (JSON)
    3. (Optional) SHAP Waterfall Plot for a specific sample
    """
    config = get_config_from_args()
    
    # Paths
    model_path = os.path.join(config.project_root, MODEL_PATH)
    data_path = os.path.join(config.project_root, PROCESSED_DATA_PATH)
    summary_plot_path = os.path.join(config.project_root, SHAP_SUMMARY_PLOT_PATH)
    importance_table_path = os.path.join(config.project_root, FEATURE_IMPORTANCE_OUTPUT)
    
    # Load Data
    try:
        model = load_trained_model(model_path)
        X, y = load_processed_data(data_path)
    except Exception as e:
        logger.error(f"Failed to load data or model: {e}")
        sys.exit(1)
    
    # Generate Outputs
    try:
        # 1. Summary Plot
        generate_shap_summary_plot(model, X, summary_plot_path)
        
        # 2. Feature Importance Table
        generate_feature_importance_table(model, X, importance_table_path)
        
        # 3. Waterfall Plot (for the first sample)
        waterfall_path = os.path.join(config.project_root, "data/processed/shap_waterfall_sample_0.png")
        generate_shap_waterfall_plot(model, X, sample_idx=0, output_path=waterfall_path)
        
        logger.info("All SHAP visualizations generated successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate visualizations: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()