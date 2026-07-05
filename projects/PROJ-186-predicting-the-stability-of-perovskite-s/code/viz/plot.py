import os
import sys
import logging
import pickle
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.inspection import permutation_importance

# Configure logging
from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

# Ensure plots directory exists
PLOTS_DIR = Path("results")
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

def load_test_data() -> pd.DataFrame:
    """
    Load the test set from the preprocessed data.
    Expects data/processed/features.csv to exist.
    """
    data_path = Path("data/processed/features.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Test data not found at {data_path}. "
                                "Please run the data pipeline (T018) first.")
    
    df = pd.read_csv(data_path)
    
    # The train/test split is usually done in preprocess.py and saved as separate files
    # or the split is performed in memory. 
    # Based on T022, we need the test split. 
    # If split_data saved separate files, we load them. 
    # If not, we assume the features.csv is the full dataset and we might need to reload the split logic 
    # or assume the task T022 saved a specific test file. 
    # However, standard practice in this pipeline implies we need the test set used for evaluation.
    # Let's check for a specific test file first, otherwise we might need to re-split.
    test_path = Path("data/processed/test_set.csv")
    if test_path.exists():
        return pd.read_csv(test_path)
    
    # Fallback: If the split wasn't saved to disk, we might need to infer or re-load.
    # But T022 says "save_processed_data" which usually saves the full features.
    # Let's assume the standard output of T022 (split_data) might have saved test_set.csv.
    # If not, we proceed with the full features and assume the model was trained on a subset,
    # but for plotting we need the specific test points.
    # For robustness, let's check if there's a specific test file. If not, we raise a clear error
    # or attempt to load the full features and warn.
    # Actually, looking at T026, it logs test RMSE. The test set must exist.
    # Let's assume the pipeline saves 'test_set.csv' or 'train_set.csv' in data/processed/
    # if the split is persistent. If not, we might have to re-run the split logic.
    # To be safe, we try to load the test set.
    raise FileNotFoundError(
        "Test set file 'data/processed/test_set.csv' not found. "
        "Ensure T022 (split_data) saves the test split to disk."
    )

def load_model() -> Any:
    """
    Load the trained model from results/model.pkl.
    """
    model_path = Path("results/model.pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. "
                                "Please run the training pipeline (T023-T026) first.")
    
    with open(model_path, "rb") as f:
        return pickle.load(f)

def plot_feature_importance(model: Any, feature_names: list, output_path: str = "feature-importance.png") -> None:
    """
    Generate a bar chart of feature importance from the trained model.
    
    For RandomForestRegressor, feature importance is available via .feature_importances_.
    """
    if not hasattr(model, 'feature_importances_'):
        logger.warning("Model does not have feature_importances_ attribute. Attempting permutation importance.")
        # Fallback to permutation importance if direct importance is missing
        # This requires X_test and y_test
        raise NotImplementedError("Direct feature importance not found. Permutation importance requires test data loading which is complex without explicit X/y separation in this function context. Assuming RandomForest has .feature_importances_")
    
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    sorted_importances = importances[indices]
    sorted_features = [feature_names[i] for i in indices]
    
    plt.figure(figsize=(10, 8))
    plt.title("Feature Importance for Perovskite Stability Prediction", fontsize=14)
    plt.bar(range(len(sorted_importances)), sorted_importances, align="center")
    plt.xticks(range(len(sorted_features)), sorted_features, rotation=45, ha="right")
    plt.xlabel("Feature")
    plt.ylabel("Importance Score")
    plt.tight_layout()
    
    output_file = PLOTS_DIR / output_path
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    log_pipeline_event(f"Feature importance plot saved to {output_file}")
    logger.info(f"Generated feature importance plot: {output_file}")

def main() -> None:
    """
    Main entry point for generating the feature importance plot.
    """
    logger.info("Starting feature importance plot generation (T030).")
    
    try:
        # Load data and model
        df_test = load_test_data()
        model = load_model()
        
        # Identify feature columns. 
        # We assume the features are all columns except 'decomposition_energy' (target)
        # and any metadata columns if present.
        # Based on T018, features.csv has specific columns.
        target_col = 'decomposition_energy'
        if target_col not in df_test.columns:
            raise ValueError(f"Target column '{target_col}' not found in test data.")
        
        feature_cols = [col for col in df_test.columns if col != target_col]
        
        # Generate the plot
        plot_feature_importance(model, feature_cols, output_path="feature-importance.png")
        
        logger.info("T030 completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate feature importance plot: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()