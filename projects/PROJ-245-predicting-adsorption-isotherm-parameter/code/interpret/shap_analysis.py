import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

import numpy as np
import pandas as pd
import shap
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConsensusValidationFailure(Exception):
    """Raised when SHAP consensus validation fails."""
    pass

def ensure_dirs():
    """Ensure output directories exist."""
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def get_best_model() -> Union[RandomForestRegressor, GradientBoostingRegressor]:
    """
    Load the best trained model from the trained_models directory.
    Expects the model to be saved as 'best_model.pkl' by T021.
    """
    model_path = Path("trained_models/best_model.pkl")
    if not model_path.exists():
        raise FileNotFoundError(
            f"Best model not found at {model_path}. "
            "Please ensure T021 (train_models) has run successfully."
        )
    logger.info(f"Loading best model from {model_path}")
    model = joblib.load(model_path)
    return model

def generate_shap_summary_plot(model, X_test: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate SHAP summary values and return them as a sorted list of dicts.
    
    Args:
        model: The trained sklearn model.
        X_test: The test feature dataframe.
        
    Returns:
        List of dicts: [{'name': str, 'mean_abs_shap_value': float}, ...]
        sorted by mean_abs_shap_value descending.
    """
    logger.info("Initializing SHAP Explainer...")
    # Use TreeExplainer for tree-based models, otherwise KernelExplainer
    try:
        explainer = shap.TreeExplainer(model)
    except Exception as e:
        logger.warning(f"TreeExplainer failed ({e}), falling back to KernelExplainer. This will be slow.")
        explainer = shap.KernelExplainer(model, X_test)
    
    logger.info("Computing SHAP values...")
    shap_values = explainer.shap_values(X_test)
    
    # Handle case where shap_values might be a list (for multi-output or specific models)
    if isinstance(shap_values, list):
        # For regression, usually just one array, but sometimes wrapped
        if len(shap_values) == 1:
            shap_values = shap_values[0]
        else:
            # Take the mean of absolute values across outputs if multi-output
            shap_values = np.mean([np.abs(sv) for sv in shap_values], axis=0)
    else:
        shap_values = np.abs(shap_values)
    
    # Calculate mean absolute SHAP value for each feature
    mean_abs_shap = np.mean(shap_values, axis=0)
    feature_names = X_test.columns.tolist()
    
    summary_list = []
    for name, value in zip(feature_names, mean_abs_shap):
        summary_list.append({
            "name": name,
            "mean_abs_shap_value": float(value)
        })
    
    # Sort descending by importance
    summary_list.sort(key=lambda x: x["mean_abs_shap_value"], reverse=True)
    
    logger.info(f"SHAP summary generated for {len(summary_list)} features.")
    return summary_list

def generate_partial_dependence_plots(model, X_test: pd.DataFrame, output_dir: Path):
    """
    Generate partial dependence plots for top features.
    (Stubs logic here, actual implementation depends on T031 requirements)
    """
    # Placeholder for T031 implementation details if needed here
    pass

def validate_consensus(shap_summary: List[Dict[str, Any]], consensus_list: List[str]) -> bool:
    """
    Validate that top 3 SHAP features overlap with consensus list.
    """
    top_3_names = [item["name"] for item in shap_summary[:3]]
    overlap = set(top_3_names).intersection(set(consensus_list))
    if len(overlap) < 2:
        logger.warning(f"Consensus validation failed. Only {len(overlap)} overlap in top 3.")
        return False
    return True

def run_shap_analysis_pipeline():
    """
    Main pipeline for T030:
    1. Load best model.
    2. Load test data (features).
    3. Compute SHAP values.
    4. Generate summary list.
    5. Write to data/results/shap_summary.json.
    """
    output_dir = ensure_dirs()
    output_file = output_dir / "shap_summary.json"
    
    # Load model
    model = get_best_model()
    
    # Load test data
    # We need the features used for training. T020/T021 should have saved split data.
    # Assuming standard location from T020 split logic:
    test_data_path = Path("data/processed/split_test_data.parquet")
    if not test_data_path.exists():
        # Fallback if T020 saved differently, check common patterns
        # If T020 saved train/test in a specific way, we need to load the test features.
        # For now, assume the pipeline saves split data.
        raise FileNotFoundError(
            f"Test data not found at {test_data_path}. "
            "Ensure T020 (split_data) has run and saved test features."
        )
    
    logger.info(f"Loading test data from {test_data_path}")
    df_test = pd.read_parquet(test_data_path)
    
    # Identify feature columns (exclude target and metadata)
    # Common targets: langmuir_capacity, henry_constant
    # Metadata: material_id, adsorbent_structure_id, descriptor_hash
    exclude_cols = {'langmuir_capacity', 'henry_constant', 'material_id', 
                    'adsorbent_structure_id', 'descriptor_hash'}
    feature_cols = [c for c in df_test.columns if c not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in test data.")
    
    X_test = df_test[feature_cols]
    
    logger.info(f"Running SHAP analysis on {X_test.shape[0]} samples with {len(feature_cols)} features.")
    
    summary_list = generate_shap_summary_plot(model, X_test)
    
    # Write output
    logger.info(f"Writing SHAP summary to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(summary_list, f, indent=2)
    
    logger.info("SHAP analysis pipeline completed successfully.")
    return summary_list

def main():
    """Entry point for script execution."""
    try:
        run_shap_analysis_pipeline()
        logger.info("Task T030 completed successfully.")
    except Exception as e:
        logger.error(f"Task T030 failed: {e}")
        raise

if __name__ == "__main__":
    main()
