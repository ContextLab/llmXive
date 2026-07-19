"""
SHAP (SHapley Additive exPlanations) utilities for model interpretability.
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
    Check if the SHAP library is available.
    
    Returns:
        True if available, False otherwise.
    """
    try:
        import shap
        return True
    except ImportError:
        logger.warning("SHAP library is not installed. Install with: pip install shap")
        return False

def compute_global_shap_values(model, X: Union[pd.DataFrame, np.ndarray], 
                               feature_names: Optional[List[str]] = None, 
                               background_data: Optional[Union[pd.DataFrame, np.ndarray]] = None,
                               nsamples: int = 100) -> Dict[str, Any]:
    """
    Compute global SHAP values for a model.
    
    Args:
        model: The trained model (e.g., RandomForestRegressor).
        X: The feature matrix to explain.
        feature_names: Optional list of feature names.
        background_data: Optional background data for KernelExplainer. If None, uses X.
        nsamples: Number of background samples for KernelExplainer.
        
    Returns:
        Dictionary containing SHAP values and summary statistics.
    """
    if not ensure_shap_available():
        raise ImportError("SHAP library is required for this function.")
    
    import shap

    # Handle feature names
    if isinstance(X, pd.DataFrame):
        if feature_names is None:
            feature_names = list(X.columns)
        X = X.values
    elif feature_names is None:
        feature_names = [f"Feature_{i}" for i in range(X.shape[1])]

    # Handle background data
    if background_data is None:
        background_data = X[:nsamples] if len(X) > nsamples else X
    
    if isinstance(background_data, pd.DataFrame):
        background_data = background_data.values

    # Create explainer
    # Try TreeExplainer for tree-based models, fall back to KernelExplainer
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
    except (ValueError, TypeError):
        logger.info("TreeExplainer failed, trying KernelExplainer...")
        explainer = shap.KernelExplainer(model.predict, background_data)
        shap_values = explainer.shap_values(X, nsamples=nsamples)

    # Handle multi-output SHAP (regression usually returns 1D or list of 1D)
    if isinstance(shap_values, list):
        shap_values = shap_values[0] if len(shap_values) > 0 else np.zeros_like(X)
    
    shap_values = np.array(shap_values)
    
    # Calculate mean absolute SHAP values for global importance
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    # Sort by importance
    importance_indices = np.argsort(mean_abs_shap)[::-1]
    sorted_features = [feature_names[i] for i in importance_indices]
    sorted_importance = mean_abs_shap[importance_indices]

    return {
        "shap_values": shap_values.tolist(),
        "feature_names": feature_names,
        "mean_abs_shap": mean_abs_shap.tolist(),
        "sorted_features": sorted_features,
        "sorted_importance": sorted_importance.tolist()
    }

def get_feature_importance_from_shap(shap_results: Dict[str, Any], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Extract top N feature importances from SHAP results.
    
    Args:
        shap_results: Output from compute_global_shap_values.
        top_n: Number of top features to return.
        
    Returns:
        List of dictionaries with feature name and importance score.
    """
    features = shap_results["sorted_features"][:top_n]
    importance = shap_results["sorted_importance"][:top_n]
    
    return [
        {"feature": f, "importance": float(i)} 
        for f, i in zip(features, importance)
    ]

def save_shap_results(shap_results: Dict[str, Any], output_path: Path) -> None:
    """
    Save SHAP results to a JSON file.
    
    Args:
        shap_results: Output from compute_global_shap_values.
        output_path: Path to save the JSON file.
    """
    # Create a copy to avoid modifying original
    results_to_save = {
        k: v for k, v in shap_results.items() 
        if k not in ["shap_values"] # Exclude large array for summary file if needed
    }
    
    # Save full results (including values)
    with open(output_path, 'w') as f:
        json.dump(shap_results, f, indent=2)
    
    logger.info(f"SHAP results saved to {output_path}")

def generate_shap_summary_plot(shap_values: np.ndarray, feature_names: List[str], 
                               output_path: Optional[Path] = None) -> None:
    """
    Generate a SHAP summary plot (beeswarm).
    
    Args:
        shap_values: SHAP values array.
        feature_names: List of feature names.
        output_path: Optional path to save the plot.
    """
    if not ensure_shap_available():
        raise ImportError("SHAP library is required for this function.")
    
    import shap
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, features=None, feature_names=feature_names, show=False)
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"SHAP summary plot saved to {output_path}")
    
    plt.close()

def main():
    """
    Main entry point for testing SHAP utilities.
    """
    logger.info("SHAP Utils module loaded successfully.")
    print("SHAP utilities available. Use compute_global_shap_values to analyze models.")

if __name__ == "__main__":
    main()
