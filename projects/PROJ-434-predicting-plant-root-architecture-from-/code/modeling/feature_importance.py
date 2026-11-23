"""
Feature Importance Extraction Module for Root Architecture Prediction.

This module handles the extraction of feature importance scores from trained
Random Forest models and saves them to CSV format.
"""

import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.exceptions import DataQualityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_trained_models(models_dir: Path) -> Tuple[Any, Any]:
    """
    Load the trained Model A (Soil-Only) and Model B (Soil+Species) from pickle files.

    Args:
        models_dir: Path to the directory containing trained model pickles.

    Returns:
        Tuple of (model_a, model_b)

    Raises:
        DataQualityError: If model files are not found or cannot be loaded.
    """
    model_a_path = models_dir / "model_a_rf.pkl"
    model_b_path = models_dir / "model_b_rf.pkl"

    if not model_a_path.exists():
        raise DataQualityError(f"Model A pickle not found at {model_a_path}")
    if not model_b_path.exists():
        raise DataQualityError(f"Model B pickle not found at {model_b_path}")

    try:
        with open(model_a_path, 'rb') as f:
            model_a = pickle.load(f)
        with open(model_b_path, 'rb') as f:
            model_b = pickle.load(f)
        logger.info(f"Successfully loaded models from {models_dir}")
        return model_a, model_b
    except Exception as e:
        raise DataQualityError(f"Failed to load models: {e}")


def extract_feature_importance(model: Any, feature_names: List[str]) -> List[Dict[str, Any]]:
    """
    Extract feature importance scores from a trained Random Forest model.

    Args:
        model: Trained Random Forest model object.
        feature_names: List of feature names corresponding to the model's feature order.

    Returns:
        List of dictionaries with 'feature_name' and 'importance_score'.
    """
    if not hasattr(model, 'feature_importances_'):
        raise DataQualityError("Model does not have feature_importances_ attribute")

    importances = model.feature_importances_
    if len(importances) != len(feature_names):
        raise DataQualityError(
            f"Mismatch: {len(importances)} importances vs {len(feature_names)} features"
        )

    return [
        {"feature_name": name, "importance_score": float(score)}
        for name, score in zip(feature_names, importances)
    ]


def save_feature_importance_csv(
    importance_data: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save feature importance scores to a CSV file.

    Args:
        importance_data: List of dictionaries with feature names and scores.
        output_path: Path to the output CSV file.
    """
    df = pd.DataFrame(importance_data)
    
    # Ensure columns are in the correct order
    df = df[['feature_name', 'importance_score']]
    
    # Sort by importance score descending
    df = df.sort_values(by='importance_score', ascending=False)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved feature importance to {output_path}")


def plot_feature_importance(
    importance_data: List[Dict[str, Any]],
    output_path: Path,
    title: str = "Feature Importance"
) -> None:
    """
    Generate a bar chart of feature importance scores.

    Args:
        importance_data: List of dictionaries with feature names and scores.
        output_path: Path to save the plot image.
        title: Title for the plot.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        raise DataQualityError("matplotlib is required for plotting. Install it via requirements.txt.")

    df = pd.DataFrame(importance_data)
    df = df.sort_values(by='importance_score', ascending=True)

    plt.figure(figsize=(10, 6))
    plt.barh(df['feature_name'], df['importance_score'], color='steelblue')
    plt.xlabel('Importance Score')
    plt.title(title)
    plt.gca().invert_yaxis()  # Highest importance at top
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved feature importance plot to {output_path}")


def main() -> int:
    """
    Main entry point for generating feature importance artifacts.

    This function:
    1. Loads trained models from artifacts/
    2. Extracts feature importance for Model A (Soil-Only)
    3. Saves the results to artifacts/feature_importance.csv
    4. Generates a visualization at figures/feature_importance.png

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Define paths
        base_dir = Path(__file__).parent.parent.parent
        artifacts_dir = base_dir / "artifacts"
        figures_dir = base_dir / "figures"
        
        models_dir = artifacts_dir
        csv_output = artifacts_dir / "feature_importance.csv"
        plot_output = figures_dir / "feature_importance.png"

        # Load models
        logger.info("Loading trained models...")
        model_a, model_b = load_trained_models(models_dir)

        # Define feature names for Model A (Soil-Only)
        # Predictors: N, P, K, pH
        feature_names_a = ['N', 'P', 'K', 'pH']

        # Extract importance for Model A
        logger.info("Extracting feature importance for Model A (Soil-Only)...")
        importance_data = extract_feature_importance(model_a, feature_names_a)

        # Save to CSV
        logger.info(f"Saving feature importance to {csv_output}...")
        save_feature_importance_csv(importance_data, csv_output)

        # Generate plot
        logger.info(f"Generating feature importance plot at {plot_output}...")
        plot_feature_importance(importance_data, plot_output, title="Model A: Soil-Only Feature Importance")

        logger.info("Task T025a completed successfully.")
        return 0

    except DataQualityError as e:
        logger.error(f"Data quality error: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())