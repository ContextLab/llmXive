"""
SHAP Interpretation Module for Creep Resistance Models.

This module loads the trained Thermodynamic Gradient Boosting Regressor,
computes SHAP values using TreeExplainer, generates summary plots,
and extracts feature importance rankings with direction of influence.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import shap
import matplotlib
# Use non-interactive backend for CI/Headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.utils.logger import get_logger
from src.utils.validators import validate_schema

# Configure logging
logger = get_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = DATA_DIR / "outputs"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure output directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# File paths
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "alloy_dataset_clean.csv"
TRAINED_MODEL_PATH = MODELS_DIR / "thermodynamic_gbr.pkl"
SHAP_PLOT_PATH = OUTPUTS_DIR / "shap_summary_plot.png"
SHAP_RESULTS_PATH = OUTPUTS_DIR / "shap_feature_importance.json"

def load_data_and_model() -> Tuple[pd.DataFrame, object, List[str]]:
    """
    Loads the processed dataset and the trained Thermodynamic GBR model.

    Returns:
        Tuple containing:
        - X: Feature DataFrame
        - model: Trained sklearn GradientBoostingRegressor
        - feature_names: List of feature column names
    """
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed data not found at {PROCESSED_DATA_PATH}. "
            "Please run the data pipeline (T019) first."
        )

    if not TRAINED_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found at {TRAINED_MODEL_PATH}. "
            "Please run the training script (T025) first."
        )

    logger.info(f"Loading data from {PROCESSED_DATA_PATH}")
    df = pd.read_csv(PROCESSED_DATA_PATH)

    # Define feature columns based on T018/T023 logic
    # Composition features (atomic fractions) + Thermodynamic descriptors
    # We assume the columns are named consistently with the pipeline
    composition_cols = [c for c in df.columns if c.startswith("atomic_frac_")]
    thermo_cols = ["mixing_enthalpy", "radius_mismatch"]
    feature_cols = composition_cols + thermo_cols

    # Sort to ensure consistent ordering
    feature_cols = sorted(composition_cols) + sorted(thermo_cols)

    X = df[feature_cols].copy()

    logger.info(f"Loading model from {TRAINED_MODEL_PATH}")
    import joblib
    model = joblib.load(TRAINED_MODEL_PATH)

    logger.info(f"Data shape: {X.shape}, Features: {feature_cols}")
    return X, model, feature_cols

def compute_shap_values(X: pd.DataFrame, model: object) -> shap.Explanation:
    """
    Computes SHAP values using TreeExplainer.

    Args:
        X: Feature DataFrame
        model: Trained sklearn model

    Returns:
        shap.Explanation object
    """
    logger.info("Initializing TreeExplainer...")
    explainer = shap.TreeExplainer(model)

    logger.info("Computing SHAP values...")
    # Calculate SHAP values for the entire dataset
    shap_values = explainer.shap_values(X)

    return shap_values

def generate_shap_plot(shap_values: shap.Explanation, X: pd.DataFrame, output_path: Path):
    """
    Generates and saves the SHAP summary plot.

    Args:
        shap_values: SHAP explanation object
        X: Feature DataFrame (for feature names)
        output_path: Path to save the plot
    """
    logger.info(f"Generating SHAP summary plot: {output_path}")

    # Create the plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, plot_type="dot", show=False, max_display=15)

    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"SHAP plot saved to {output_path}")

def extract_feature_importance(shap_values: shap.Explanation, X: pd.DataFrame) -> List[Dict]:
    """
    Extracts feature importance rankings and direction of influence.

    Args:
        shap_values: SHAP explanation object
        X: Feature DataFrame

    Returns:
        List of dictionaries containing feature info
    """
    # Calculate mean absolute SHAP values for global importance
    mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
    feature_names = X.columns.tolist()

    # Create a list of importance data
    importance_data = []
    for i, name in enumerate(feature_names):
        mean_val = float(mean_abs_shap[i])
        # Determine direction: correlation between feature and SHAP value
        # Positive correlation -> positive influence (higher feature -> higher target)
        # Negative correlation -> negative influence
        corr = np.corrcoef(X[name].values, shap_values.values[:, i])[0, 1]
        direction = "positive" if corr > 0 else "negative"

        importance_data.append({
            "feature": name,
            "mean_abs_shap": mean_val,
            "correlation": float(corr),
            "direction": direction
        })

    # Sort by mean absolute SHAP value descending
    importance_data.sort(key=lambda x: x["mean_abs_shap"], reverse=True)

    return importance_data

def save_results(importance_data: List[Dict], output_path: Path):
    """
    Saves the feature importance results to a JSON file.

    Args:
        importance_data: List of importance dictionaries
        output_path: Path to save the JSON file
    """
    logger.info(f"Saving feature importance results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(importance_data, f, indent=2)
    logger.info("Results saved successfully.")

def main():
    """
    Main entry point for the interpretation pipeline.
    """
    logger.info("Starting SHAP Interpretation Pipeline (T027)")

    try:
        # 1. Load Data and Model
        X, model, feature_names = load_data_and_model()

        # 2. Compute SHAP Values
        shap_values = compute_shap_values(X, model)

        # 3. Generate Plot
        generate_shap_plot(shap_values, X, SHAP_PLOT_PATH)

        # 4. Extract and Save Importance
        importance_data = extract_feature_importance(shap_values, X)
        save_results(importance_data, SHAP_RESULTS_PATH)

        # 5. Log Top 5 Features
        logger.info("Top 5 Features by Importance:")
        for i, item in enumerate(importance_data[:5], 1):
            logger.info(f"  {i}. {item['feature']}: {item['mean_abs_shap']:.4f} ({item['direction']})")

        logger.info("T027 Execution Completed Successfully.")

    except Exception as e:
        logger.error(f"T027 Execution Failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
