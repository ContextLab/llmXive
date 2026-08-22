"""
Feature Importance Analysis Module

This module handles the extraction, saving, and visualization of feature importance
scores from trained Random Forest models.
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path for imports if running as script
if 'code' not in sys.path[0]:
    code_root = Path(__file__).resolve().parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

from utils.exceptions import DataQualityError
from utils.logging_utils import get_logger

# Configure logging
logger = get_logger(__name__)

def load_trained_models(model_dir: Path) -> Tuple[Any, Any]:
    """
    Load the trained Model A (Soil-Only) and Model B (Soil+Species) from disk.

    Args:
        model_dir: Path to the directory containing trained model pickles.

    Returns:
        Tuple of (model_a, model_b)

    Raises:
        DataQualityError: If model files are missing or corrupted.
    """
    model_a_path = model_dir / "model_a_soil_only.pkl"
    model_b_path = model_dir / "model_b_soil_species.pkl"

    if not model_a_path.exists():
        raise DataQualityError(f"Model A file not found: {model_a_path}")
    if not model_b_path.exists():
        raise DataQualityError(f"Model B file not found: {model_b_path}")

    try:
        with open(model_a_path, 'rb') as f:
            model_a = pickle.load(f)
        with open(model_b_path, 'rb') as f:
            model_b = pickle.load(f)
        logger.info(f"Successfully loaded models from {model_dir}")
        return model_a, model_b
    except Exception as e:
        raise DataQualityError(f"Failed to load model files: {e}")

def extract_feature_importance(
    model: Any,
    feature_names: List[str],
    target: str = "root_depth"
) -> pd.DataFrame:
    """
    Extract feature importance scores from a trained Random Forest model.

    Args:
        model: Trained sklearn RandomForestRegressor.
        feature_names: List of feature names corresponding to the model's feature_importances_.
        target: Target variable name for labeling (default: root_depth).

    Returns:
        DataFrame with columns: 'feature_name', 'importance_score'.
    """
    if not hasattr(model, 'feature_importances_'):
        raise DataQualityError("Model does not have feature_importances_ attribute.")

    importances = model.feature_importances_
    if len(importances) != len(feature_names):
        raise DataQualityError(
            f"Mismatch in feature counts: model has {len(importances)}, "
            f"but {len(feature_names)} names provided."
        )

    df = pd.DataFrame({
        'feature_name': feature_names,
        'importance_score': importances
    })

    # Sort by importance descending
    df = df.sort_values(by='importance_score', ascending=False).reset_index(drop=True)
    return df

def save_feature_importance_csv(
    df_importance: pd.DataFrame,
    output_path: Path
) -> None:
    """
    Save feature importance scores to a CSV file.

    Args:
        df_importance: DataFrame with 'feature_name' and 'importance_score'.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_importance.to_csv(output_path, index=False)
    logger.info(f"Saved feature importance to {output_path}")

def plot_feature_importance(
    df_importance: pd.DataFrame,
    output_path: Path,
    title: str = "Feature Importance (Model B: Soil + Species)",
    top_n: Optional[int] = None,
    color: str = "#2c7bb6"
) -> None:
    """
    Generate a horizontal bar chart of feature importance scores.

    Args:
        df_importance: DataFrame with 'feature_name' and 'importance_score'.
        output_path: Path to save the PNG figure.
        title: Plot title.
        top_n: If provided, only plot the top N features.
        color: Bar color.
    """
    if df_importance.empty:
        raise DataQualityError("Cannot plot: Feature importance DataFrame is empty.")

    # Select top N if requested
    plot_df = df_importance
    if top_n is not None:
        if top_n < len(plot_df):
            plot_df = plot_df.head(top_n)

    # Setup plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 8))

    # Create horizontal bar chart
    y_pos = np.arange(len(plot_df))
    bars = ax.barh(y_pos, plot_df['importance_score'], color=color, edgecolor='black', alpha=0.8)

    # Labels and Title
    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_df['feature_name'], fontsize=11)
    ax.set_xlabel('Importance Score', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.invert_yaxis()  # Highest importance at top

    # Add value labels on bars
    for i, v in enumerate(plot_df['importance_score']):
        ax.text(v + 0.001, i, f"{v:.4f}", va='center', fontsize=10)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Saved feature importance plot to {output_path}")

def main():
    """
    Main entry point for generating feature importance artifacts.
    1. Loads trained models from code/modeling/models/ (or configured path).
    2. Extracts importance for Model B (primary).
    3. Saves CSV to artifacts/feature_importance.csv.
    4. Generates PNG plot to figures/feature_importance.png.
    """
    # Configuration
    project_root = Path(__file__).resolve().parent.parent.parent
    models_dir = project_root / "code" / "modeling" / "models"
    artifacts_dir = project_root / "artifacts"
    figures_dir = project_root / "figures"

    csv_output = artifacts_dir / "feature_importance.csv"
    png_output = figures_dir / "feature_importance.png"

    # Setup logging
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "feature_importance.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger.info("Starting Feature Importance Generation (T025b)")

    try:
        # 1. Load Models
        # Note: We assume Model B is the primary model for this visualization.
        # We need to know the feature names used for Model B.
        # These are typically: ['N', 'P', 'K', 'pH', 'Species_<one-hot-encoded>']
        # Since we don't have the exact list here, we load the model and get feature_names_
        # if available (e.g., if wrapped in a Pipeline with OneHotEncoder).
        # If not, we rely on a known config or the model's internal state.
        
        # Attempt to load models
        model_a, model_b = load_trained_models(models_dir)

        # Determine feature names
        # Strategy: Try to get from model attributes (common in Pipelines)
        # If not available, we might need a hardcoded list or a metadata file.
        # For robustness, we check if the model has feature_names_ (from sklearn 1.0+ or custom wrapper)
        
        feature_names = None
        
        # Check for common attributes
        if hasattr(model_b, 'feature_names_in_'):
            feature_names = list(model_b.feature_names_in_)
            logger.info(f"Retrieved feature names from model: {len(feature_names)} features.")
        elif hasattr(model_b, 'feature_importances_'):
            # Fallback: If we have a metadata file or known structure
            # In a real pipeline, this would be saved alongside the model.
            # For this implementation, we assume a standard set if not found.
            # However, to be strict, we should fail if we don't know the names.
            logger.warning("Model does not expose feature_names_in_. Attempting to load from metadata.")
            
            metadata_path = models_dir / "model_b_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    meta = json.load(f)
                    feature_names = meta.get('feature_names')
                    logger.info(f"Loaded feature names from metadata: {len(feature_names)} features.")
            else:
                raise DataQualityError(
                    "Model B loaded but feature names are not available via attributes or metadata. "
                    "Cannot generate importance plot without feature names."
                )
        else:
            raise DataQualityError("Model B does not have feature_importances_ or feature names.")

        # 2. Extract Importance
        df_importance = extract_feature_importance(model_b, feature_names)
        logger.info(f"Extracted importance for {len(df_importance)} features.")

        # 3. Save CSV (T025a dependency - ensure this exists)
        save_feature_importance_csv(df_importance, csv_output)

        # 4. Generate Plot (T025b)
        plot_feature_importance(df_importance, png_output, title="Feature Importance (Model B: Soil + Species)")

        logger.info("Task T025b completed successfully.")

    except DataQualityError as e:
        logger.error(f"Data Quality Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()