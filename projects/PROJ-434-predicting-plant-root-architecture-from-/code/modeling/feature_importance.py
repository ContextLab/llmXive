"""
Feature Importance Analysis Module for Predicting Plant Root Architecture.

This module handles loading trained models, extracting feature importance scores,
saving them to CSV, and generating visualization plots.
"""

import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

# Import from sibling modules based on API surface
from utils.exceptions import DataQualityError
from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_trained_models(models_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load the trained Model A (Soil-Only) and Model B (Soil+Species) from disk.

    Args:
        models_dir: Path to the directory containing model pickles.

    Returns:
        Tuple of (model_a, model_b) dictionaries containing the trained estimators.
    """
    model_a_path = models_dir / "model_a_soil_only.pkl"
    model_b_path = models_dir / "model_b_soil_species.pkl"

    if not model_a_path.exists():
        raise FileNotFoundError(f"Model A not found at {model_a_path}")
    if not model_b_path.exists():
        raise FileNotFoundError(f"Model B not found at {model_b_path}")

    logger.info(f"Loading Model A from {model_a_path}")
    with open(model_a_path, 'rb') as f:
        model_a = pickle.load(f)

    logger.info(f"Loading Model B from {model_b_path}")
    with open(model_b_path, 'rb') as f:
        model_b = pickle.load(f)

    return model_a, model_b


def extract_feature_importance(model: Any, model_name: str) -> pd.DataFrame:
    """
    Extract feature importance scores from a trained Random Forest model.

    Args:
        model: The trained Random Forest estimator.
        model_name: Name of the model for logging purposes.

    Returns:
        DataFrame with columns: 'feature_name', 'importance_score'.
    """
    if not hasattr(model, 'feature_importances_'):
        raise ValueError(f"Model {model_name} does not have feature_importances_ attribute.")

    # Determine feature names based on model type
    # This assumes the model was trained with a specific feature order known at training time.
    # For robustness, we might need to store feature names in the model metadata.
    # Based on the pipeline description:
    # Model A (Soil-Only): ['N', 'P', 'K', 'pH']
    # Model B (Soil+Species): ['N', 'P', 'K', 'pH', 'Species_encoded'] (or similar)

    # Since we are extracting from the trained object, we need to know the feature names.
    # The training script should have saved the feature names.
    # Let's assume a standard mapping or read from a metadata file if available.
    # For now, we will infer or use a standard set if Model A.
    # If Model B, we need the species encoding info.

    # A robust approach: The training script saves feature_names in the pickle or a sidecar.
    # Let's assume the model object has a 'feature_names_' attribute or we load it from metadata.
    # If not present, we raise an error or use defaults for Model A.

    feature_names = getattr(model, 'feature_names_', None)

    if feature_names is None:
        if model_name == "Model A":
            feature_names = ['N', 'P', 'K', 'pH']
        elif model_name == "Model B":
            # Placeholder for Model B features. In a real scenario, this must be retrieved.
            # Assuming one-hot encoded species or target encoding.
            # Let's try to load from a sidecar if it exists, otherwise default to generic names.
            # For this implementation, we will assume the training script saved the feature names
            # in a 'feature_importance_data.json' or similar, or we rely on the model's metadata.
            # To be safe, we'll assume the training script stored the feature names in the model's __dict__
            # or a specific attribute.
            # If not, we raise an error.
            raise DataQualityError(
                f"Feature names not found for {model_name}. Ensure training script saves feature names.",
                match_proportion=0.0
            )

    importances = model.feature_importances_

    if len(importances) != len(feature_names):
        raise ValueError(
            f"Feature count mismatch: {len(importances)} importances vs {len(feature_names)} names."
        )

    df = pd.DataFrame({
        'feature_name': feature_names,
        'importance_score': importances
    })

    # Sort by importance descending
    df = df.sort_values(by='importance_score', ascending=False).reset_index(drop=True)

    return df


def save_feature_importance_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save feature importance scores to a CSV file.

    Args:
        df: DataFrame with 'feature_name' and 'importance_score'.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved feature importance to {output_path}")


def plot_feature_importance(df: pd.DataFrame, output_path: Path, title: str = "Feature Importance") -> None:
    """
    Generate a bar chart of feature importance scores.

    Args:
        df: DataFrame with 'feature_name' and 'importance_score'.
        output_path: Path to save the plot image.
        title: Title for the plot.
    """
    plt.figure(figsize=(10, 6))

    # Sort by importance for the plot (already sorted in df, but ensure)
    df_sorted = df.sort_values(by='importance_score', ascending=True)

    plt.barh(df_sorted['feature_name'], df_sorted['importance_score'], color='skyblue', edgecolor='black')
    plt.xlabel('Importance Score')
    plt.ylabel('Feature')
    plt.title(title)
    plt.gca().invert_yaxis()  # Highest importance at the top
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved feature importance plot to {output_path}")


def main():
    """
    Main execution function for T025.
    Loads trained models, extracts feature importance, saves CSV, and generates plot.
    """
    config = get_config()
    project_root = Path(config.get('project_root', '.'))

    models_dir = project_root / "artifacts"
    output_csv = project_root / "artifacts" / "feature_importance.csv"
    output_plot = project_root / "figures" / "feature_importance.png"

    logger.info(f"Starting Feature Importance Generation for {models_dir}")

    try:
        # Load models
        model_a, model_b = load_trained_models(models_dir)

        # Extract importance for Model B (Soil+Species) as it's the primary model
        # The task description implies generating importance for the main predictive model.
        # Model B is the primary implementation of FR-003.
        df_model_b = extract_feature_importance(model_b, "Model B")

        # Also extract for Model A for comparison if needed, but T025 focuses on the main output.
        # We will save Model B's importance as the primary artifact.
        save_feature_importance_csv(df_model_b, output_csv)

        # Generate plot
        plot_feature_importance(df_model_b, output_plot, title="Feature Importance (Model B: Soil + Species)")

        logger.info("T025 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Required model files not found: {e}")
        sys.exit(1)
    except DataQualityError as e:
        logger.error(f"Data quality error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during feature importance generation: {e}")
        raise


if __name__ == "__main__":
    main()