"""
Partial Dependence Plot (PDP) Generation for Solder Hardness Models.

This module generates Partial Dependence Plots for the top-ranked features
identified by SHAP analysis (from T030). It reads the trained models and
feature importance rankings to produce visualizations of the marginal effect
of features on the predicted hardness.

Dependencies:
    - code/evaluation/shap_analysis.py (for top-k feature list)
    - code/models/xgboost_trainer.py (for trained model artifacts)
    - data/processed/descriptors.csv (for feature data)
    - data/processed/solder_hardness_cleaned.csv (for raw composition context if needed)
"""

import os
import sys
import logging
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
from sklearn.inspection import partial_dependence
from sklearn.model_selection import train_test_split

# Project imports based on provided API surface
from config import (
    get_data_processed_dir,
    get_data_outputs_dir,
    get_models_dir,
    get_cv_folds
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants
PDP_OUTPUT_FILE = "data/outputs/pdp_top_features.png"
PDP_DETAILS_FILE = "data/outputs/pdp_details.yaml"
MAX_PDP_FEATURES = 5  # Limit number of plots to avoid clutter
PDP_GRID_ROWS = 2
PDP_GRID_COLS = 3


def load_shap_ranking() -> List[Dict[str, Any]]:
    """
    Load the SHAP ranking from the evaluation output.

    Returns:
        List of dictionaries containing feature_name, mean_abs_shap_value, rank.
    """
    shap_file = get_data_processed_dir() / "shap_ranking.yaml"
    if not shap_file.exists():
        raise FileNotFoundError(f"SHAP ranking file not found: {shap_file}")

    with open(shap_file, 'r') as f:
        data = yaml.safe_load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'ranking' in data:
        return data['ranking']
    else:
        raise ValueError(f"Unexpected format in {shap_file}")


def load_trained_models() -> Dict[str, Any]:
    """
    Load the trained XGBoost and Linear Regression models.

    Returns:
        Dictionary mapping model name to the trained estimator object.
    """
    models_dir = get_models_dir()
    xgb_path = models_dir / "xgboost_model.pkl"
    lr_path = models_dir / "linear_model.pkl"

    models = {}

    if xgb_path.exists():
        with open(xgb_path, 'rb') as f:
            models['xgboost'] = pickle.load(f)
        logger.info("Loaded XGBoost model.")
    else:
        logger.warning(f"XGBoost model not found at {xgb_path}. PDP for XGBoost will be skipped.")

    if lr_path.exists():
        with open(lr_path, 'rb') as f:
            models['linear'] = pickle.load(f)
        logger.info("Loaded Linear Regression model.")
    else:
        logger.warning(f"Linear Regression model not found at {lr_path}. PDP for Linear will be skipped.")

    if not models:
        raise RuntimeError("No trained models found to generate PDPs.")

    return models


def load_features_and_target() -> tuple:
    """
    Load the feature matrix (descriptors) and target (hardness).

    Returns:
        Tuple of (X: pd.DataFrame, y: pd.Series, feature_names: List[str])
    """
    desc_file = get_data_processed_dir() / "descriptors.csv"
    if not desc_file.exists():
        raise FileNotFoundError(f"Descriptors file not found: {desc_file}")

    df = pd.read_csv(desc_file)

    # Identify target column (usually 'hardness_hv')
    target_col = 'hardness_hv'
    if target_col not in df.columns:
        # Fallback: check for other common names or raise
        cols = [c for c in df.columns if 'hardness' in c.lower()]
        if cols:
            target_col = cols[0]
        else:
            raise ValueError(f"Target column '{target_col}' not found in {desc_file}. Columns: {df.columns.tolist()}")

    y = df[target_col]
    # Features are all columns except target
    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols]

    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features.")
    return X, y, feature_cols


def generate_partial_dependence_plots(
    models: Dict[str, Any],
    X: pd.DataFrame,
    y: pd.Series,
    top_features: List[str],
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate Partial Dependence Plots for the top features.

    Args:
        models: Dictionary of trained models.
        X: Feature matrix.
        y: Target vector.
        top_features: List of feature names to plot.
        output_path: Path to save the plot image.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine grid size
    n_features = min(len(top_features), MAX_PDP_FEATURES)
    rows = (n_features + PDP_GRID_COLS - 1) // PDP_GRID_COLS
    fig, axes = plt.subplots(rows, PDP_GRID_COLS, figsize=(15, 5 * rows))
    axes = axes.flatten()

    pdp_details = []

    for idx, feat_name in enumerate(top_features[:MAX_PDP_FEATURES]):
        if feat_name not in X.columns:
            logger.warning(f"Feature '{feat_name}' not in feature matrix. Skipping.")
            continue

        ax = axes[idx]

        # Generate PDP for each available model
        model_colors = {
            'xgboost': 'blue',
            'linear': 'red'
        }
        model_labels = {
            'xgboost': 'XGBoost',
            'linear': 'Linear Reg'
        }

        for model_name, model in models.items():
            # Calculate partial dependence
            # Using sklearn's partial_dependence which handles the grid generation
            try:
                # We need to pass the feature indices or names
                # partial_dependence returns a dictionary with 'values' and 'average'
                pdp_result = partial_dependence(
                    model, X, features=[feat_name], kind='average'
                )

                values = pdp_result['values'][0]
                predictions = pdp_result['average'][0]

                ax.plot(values, predictions, label=model_labels.get(model_name, model_name),
                        color=model_colors.get(model_name, 'black'), linewidth=2)

                # Store details for YAML output
                pdp_details.append({
                    'feature': feat_name,
                    'model': model_name,
                    'min_x': float(min(values)),
                    'max_x': float(max(values)),
                    'min_y': float(min(predictions)),
                    'max_y': float(max(predictions)),
                    'slope_direction': "positive" if predictions[-1] > predictions[0] else "negative"
                })

            except Exception as e:
                logger.error(f"Error generating PDP for {model_name} on {feat_name}: {e}")
                ax.text(0.5, 0.5, f"Error: {str(e)[:30]}", ha='center', va='center', transform=ax.transAxes)

        ax.set_title(f"Partial Dependence: {feat_name}")
        ax.set_xlabel("Feature Value")
        ax.set_ylabel("Partial Dependence (Hardness)")
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

    # Hide unused subplots
    for j in range(idx + 1, len(axes)):
        axes[j].axis('off')

    plt.suptitle("Partial Dependence Plots for Top SHAP Features", fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved PDP plot to {output_path}")
    return pdp_details


def save_pdp_details(details: List[Dict[str, Any]], output_path: Path):
    """
    Save the detailed PDP metrics to a YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(details, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Saved PDP details to {output_path}")


def main():
    """
    Main entry point for generating Partial Dependence Plots.
    """
    logger.info("Starting Partial Dependence Plot generation (T037)...")

    try:
        # 1. Load SHAP ranking to get top features
        shap_ranking = load_shap_ranking()
        top_features = [item['feature_name'] for item in shap_ranking]
        logger.info(f"Loaded top features: {top_features}")

        # 2. Load trained models
        models = load_trained_models()

        # 3. Load feature data
        X, y, feature_names = load_features_and_target()

        # 4. Generate plots
        output_img = get_data_outputs_dir() / PDP_OUTPUT_FILE
        details = generate_partial_dependence_plots(
            models=models,
            X=X,
            y=y,
            top_features=top_features,
            output_path=output_img
        )

        # 5. Save details
        output_yaml = get_data_outputs_dir() / PDP_DETAILS_FILE
        save_pdp_details(details, output_yaml)

        logger.info("T037 completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during PDP generation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
