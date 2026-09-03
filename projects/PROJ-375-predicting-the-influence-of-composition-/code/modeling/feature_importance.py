"""
Feature Importance Extraction for Metallic Glass Thermal Expansion Prediction.

This module implements Task T037: Extract feature importance from the trained
Random Forest model and save the results to results/feature_importance.csv.

The script loads the latest serialized Random Forest model from code/models/,
extracts the feature importances, sorts them by importance score in descending
order, and writes them to a CSV file in the results directory.
"""

import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
import joblib

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.io import setup_logging
from utils.config import get_env_var

# Constants
RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = PROJECT_ROOT / "code" / "models"
OUTPUT_FILE = RESULTS_DIR / "feature_importance.csv"

# Feature list matching the training pipeline (T025)
FEATURE_NAMES = [
    "mean_atomic_radius",
    "electronegativity_var",
    "vec",
    "size_mismatch"
]

logger = logging.getLogger(__name__)


def load_latest_rf_model() -> tuple:
    """
    Load the latest Random Forest model from the models directory.

    Returns:
        tuple: (model, metadata_dict)

    Raises:
        FileNotFoundError: If no Random Forest model is found.
        ValueError: If the model is not a Random Forest instance.
    """
    if not MODELS_DIR.exists():
        raise FileNotFoundError(f"Models directory not found: {MODELS_DIR}")

    # Find the latest RF model file
    rf_files = list(MODELS_DIR.glob("random_forest_v*.pkl"))
    if not rf_files:
        raise FileNotFoundError(f"No Random Forest model found in {MODELS_DIR}")

    # Sort by modification time to get the latest
    latest_rf_file = max(rf_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Loading Random Forest model from: {latest_rf_file}")

    try:
        model = joblib.load(latest_rf_file)
    except Exception as e:
        raise RuntimeError(f"Failed to load model from {latest_rf_file}: {e}")

    # Verify it's a Random Forest
    model_type = type(model).__name__
    if "RandomForest" not in model_type:
        raise ValueError(f"Expected RandomForest model, got {model_type}")

    # Load corresponding metadata
    meta_file = latest_rf_file.with_suffix(".json").name.replace(".pkl", "_meta.json")
    meta_path = MODELS_DIR / meta_file
    
    metadata = {}
    if meta_path.exists():
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            logger.info(f"Loaded metadata from {meta_path}")
        except Exception as e:
            logger.warning(f"Could not load metadata from {meta_path}: {e}")
    else:
        logger.warning(f"Metadata file not found: {meta_path}")

    return model, metadata


def extract_feature_importance(model) -> pd.DataFrame:
    """
    Extract feature importance scores from the trained Random Forest model.

    Args:
        model: The trained Random Forest model.

    Returns:
        pd.DataFrame: DataFrame with columns 'feature' and 'importance_score',
                     sorted by importance_score in descending order.
    """
    if not hasattr(model, 'feature_importances_'):
        raise AttributeError("Model does not have feature_importances_ attribute")

    importances = model.feature_importances_

    if len(importances) != len(FEATURE_NAMES):
        raise ValueError(
            f"Feature count mismatch: model has {len(importances)} features, "
            f"but expected {len(FEATURE_NAMES)} ({FEATURE_NAMES})"
        )

    df = pd.DataFrame({
        "feature": FEATURE_NAMES,
        "importance_score": importances
    })

    # Sort by importance_score descending
    df = df.sort_values(by="importance_score", ascending=False).reset_index(drop=True)

    # Round importance scores to 6 decimal places for readability
    df["importance_score"] = df["importance_score"].round(6)

    return df


def save_feature_importance(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the feature importance DataFrame to a CSV file.

    Args:
        df: DataFrame with feature importance data.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to: {output_path}")


def main():
    """Main entry point for feature importance extraction."""
    setup_logging()
    logger.info("Starting feature importance extraction (Task T037)")

    try:
        # Load the latest Random Forest model
        model, metadata = load_latest_rf_model()

        # Extract feature importance
        logger.info("Extracting feature importance scores...")
        importance_df = extract_feature_importance(model)

        # Display results
        logger.info("Feature Importance Results:")
        for _, row in importance_df.iterrows():
            logger.info(f"  {row['feature']}: {row['importance_score']:.6f}")

        # Save to CSV
        save_feature_importance(importance_df, OUTPUT_FILE)

        # Log success
        logger.info("Feature importance extraction completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during feature importance extraction: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())