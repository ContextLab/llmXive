"""
SHAP (SHapley Additive exPlanations) utilities for model interpretability.
Computes global feature importance and generates summary plots.
"""
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def ensure_shap_available() -> bool:
    """
    Checks if the 'shap' library is installed.
    
    Returns:
        True if available, False otherwise.
    """
    try:
        import shap
        return True
    except ImportError:
        logger.warning("SHAP library not found. Install with: pip install shap")
        return False

def compute_global_shap_values(model: Any, X: Union[pd.DataFrame, np.ndarray], 
                               feature_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Computes global SHAP values for a given model and dataset.
    
    Args:
        model: The trained scikit-learn compatible model.
        X: The feature matrix (dataframe or array).
        feature_names: Optional list of feature names. If None, derived from X or indices.
    
    Returns:
        Dictionary containing SHAP values and mean absolute SHAP values.
    """
    if not ensure_shap_available():
        raise ImportError("SHAP library is required for this function.")
    
    import shap

    # Determine feature names
    if feature_names is None:
        if isinstance(X, pd.DataFrame):
            feature_names = list(X.columns)
        else:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    
    # Create Explainer
    # Handle different model types (TreeExplainer for RF/GB is faster)
    try:
        explainer = shap.TreeExplainer(model)
    except Exception:
        explainer = shap.Explainer(model, X)
    
    # Compute SHAP values
    shap_values = explainer.shap_values(X)
    
    # Handle multi-output or specific return types from TreeExplainer
    if isinstance(shap_values, list):
        # For regression, usually returns a list of arrays if multi-output, 
        # or sometimes just one array wrapped. 
        # Assuming single target regression for this pipeline:
        if len(shap_values) == 1:
            shap_values = shap_values[0]
        else:
            # Take the first output if multi-output
            shap_values = shap_values[0]
    
    # Calculate mean absolute SHAP values for global importance
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    
    importance_dict = {
        "feature_names": feature_names,
        "mean_abs_shap": mean_abs_shap.tolist(),
        "shap_values": shap_values.tolist()
    }
    
    return importance_dict

def get_feature_importance_from_shap(shap_results: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Extracts the top-K most important features from SHAP results.
    
    Args:
        shap_results: Dictionary from compute_global_shap_values.
        top_k: Number of top features to return.
    
    Returns:
        List of dicts with 'feature', 'importance', and 'rank'.
    """
    names = shap_results["feature_names"]
    values = shap_results["mean_abs_shap"]
    
    # Sort indices by importance descending
    sorted_indices = np.argsort(values)[::-1]
    
    top_features = []
    for rank, idx in enumerate(sorted_indices[:top_k]):
        top_features.append({
            "feature": names[idx],
            "importance": float(values[idx]),
            "rank": rank + 1
        })
    
    return top_features

def save_shap_results(shap_results: Dict[str, Any], output_path: Path) -> None:
    """
    Saves SHAP results to a JSON file.
    
    Args:
        shap_results: Dictionary from compute_global_shap_values.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(shap_results, f, indent=2)
    logger.info(f"SHAP results saved to {output_path}")

def generate_shap_summary_plot(shap_values: np.ndarray, 
                               feature_names: List[str],
                               output_path: Optional[Path] = None) -> None:
    """
    Generates and saves a SHAP summary plot (beeswarm).
    
    Args:
        shap_values: 2D array of SHAP values.
        feature_names: List of feature names.
        output_path: Optional path to save the plot. If None, displays it.
    """
    if not ensure_shap_available():
        raise ImportError("SHAP library is required for this function.")
    
    import shap
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, features=None, feature_names=feature_names, plot_type="dot", show=False)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"SHAP summary plot saved to {output_path}")
    else:
        plt.show()
        plt.close()

def main():
    """
    Main entry point for testing the SHAP utilities.
    Note: This requires a trained model and data to run effectively.
    """
    logger.info("SHAP utilities module loaded successfully.")
    logger.info("Available functions: ensure_shap_available, compute_global_shap_values, get_feature_importance_from_shap, save_shap_results, generate_shap_summary_plot")
    
    if not ensure_shap_available():
        logger.warning("Cannot run full test without SHAP installed.")
        return

    # Placeholder for a real test if data were available
    logger.info("Ready to compute SHAP values when model and data are provided.")

if __name__ == "__main__":
    main()