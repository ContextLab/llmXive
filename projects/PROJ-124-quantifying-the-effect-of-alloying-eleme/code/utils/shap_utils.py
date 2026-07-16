"""
SHAP (SHapley Additive exPlanations) utility functions for model interpretability.

This module provides functions to compute and visualize SHAP values for
understanding feature importance in glass-forming ability predictions.
"""
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Try to import shap, but handle gracefully if not available
SHAP_AVAILABLE = False
try:
    import shap
    SHAP_AVAILABLE = True
    logger.info("SHAP library is available")
except ImportError:
    logger.warning("SHAP library not installed. Install with: pip install shap")

def ensure_shap_available() -> bool:
    """
    Ensure SHAP library is available.
    
    Returns:
        True if SHAP is available, False otherwise.
    """
    if not SHAP_AVAILABLE:
        logger.error("SHAP library is not available. Please install it.")
    return SHAP_AVAILABLE

def compute_global_shap_values(model: Any, 
                              X: Union[pd.DataFrame, np.ndarray],
                              feature_names: Optional[List[str]] = None,
                              nsamples: int = 100) -> Dict[str, Any]:
    """
    Compute global SHAP values for a model on a dataset.
    
    Args:
        model: Trained model with predict method
        X: Feature matrix (DataFrame or array)
        feature_names: Optional list of feature names
        nsamples: Number of samples for SHAP approximation
        
    Returns:
        Dictionary containing:
            - shap_values: Array of SHAP values
            - expected_value: Expected value of the model output
            - feature_importance: Mean absolute SHAP values per feature
    """
    if not ensure_shap_available():
        raise RuntimeError("SHAP library not available")
    
    # Convert to DataFrame if needed
    if not isinstance(X, pd.DataFrame):
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        X = pd.DataFrame(X, columns=feature_names)
    
    # Create SHAP explainer
    try:
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X)
    except Exception as e:
        logger.warning(f"Standard explainer failed: {e}. Trying KernelExplainer.")
        # Fallback to KernelExplainer for black-box models
        explainer = shap.KernelExplainer(model.predict, X[:nsamples])
        shap_values = explainer.shap_values(X[:nsamples])
    
    # Handle different output formats
    if isinstance(shap_values, list):
        # For multi-class or multi-output models
        shap_values = np.array(shap_values)
    
    # Compute feature importance (mean absolute SHAP values)
    if len(shap_values.shape) == 2:
        feature_importance = np.mean(np.abs(shap_values), axis=0)
    else:
        # Handle 3D case (samples, features, classes)
        feature_importance = np.mean(np.abs(shap_values), axis=(0, 1))
    
    expected_value = explainer.expected_value
    
    # If expected_value is an array, take the mean
    if isinstance(expected_value, (list, np.ndarray)):
        expected_value = np.mean(expected_value)
    
    return {
        "shap_values": shap_values,
        "expected_value": float(expected_value) if np.isscalar(expected_value) else expected_value.tolist(),
        "feature_importance": feature_importance.tolist() if isinstance(feature_importance, np.ndarray) else feature_importance,
        "feature_names": list(X.columns)
    }

def get_feature_importance_from_shap(shap_results: Dict[str, Any], 
                                   top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Extract ranked feature importance from SHAP results.
    
    Args:
        shap_results: Dictionary from compute_global_shap_values
        top_n: Number of top features to return
        
    Returns:
        List of dicts with feature name, importance, and rank
    """
    importance = shap_results.get("feature_importance", [])
    feature_names = shap_results.get("feature_names", [])
    
    if not importance or not feature_names:
        logger.warning("No SHAP results available")
        return []
    
    # Create list of (name, importance) tuples
    ranked = list(zip(feature_names, importance))
    ranked.sort(key=lambda x: x[1], reverse=True)
    
    # Return top N
    result = []
    for i, (name, imp) in enumerate(ranked[:top_n]):
        result.append({
            "rank": i + 1,
            "feature_name": name,
            "importance": float(imp)
        })
    
    return result

def save_shap_results(shap_results: Dict[str, Any], 
                    output_path: Union[str, Path]) -> None:
    """
    Save SHAP results to a JSON file.
    
    Args:
        shap_results: Dictionary from compute_global_shap_values
        output_path: Path to save the JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy arrays to lists for JSON serialization
    serializable = {}
    for key, value in shap_results.items():
        if isinstance(value, np.ndarray):
            serializable[key] = value.tolist()
        elif isinstance(value, (np.floating, np.integer)):
            serializable[key] = float(value)
        else:
            serializable[key] = value
    
    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2)
    
    logger.info(f"Saved SHAP results to {output_path}")

def generate_shap_summary_plot(shap_results: Dict[str, Any],
                             output_path: Optional[Union[str, Path]] = None) -> Optional[str]:
    """
    Generate a SHAP summary plot.
    
    Args:
        shap_results: Dictionary from compute_global_shap_values
        output_path: Optional path to save the plot
        
    Returns:
        Path to saved plot, or None if not saved
    """
    if not ensure_shap_available():
        logger.error("Cannot generate SHAP plot: library not available")
        return None
    
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("Matplotlib not available for plotting")
        return None
    
    shap_values = shap_results.get("shap_values")
    feature_names = shap_results.get("feature_names", [])
    
    if shap_values is None:
        logger.error("No SHAP values available for plotting")
        return None
    
    # Create figure
    plt.figure(figsize=(10, 8))
    
    # Create SHAP summary plot
    shap.summary_plot(shap_values, feature_names=feature_names, show=False)
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved SHAP summary plot to {output_path}")
        return str(output_path)
    else:
        plt.show()
        return None

def main():
    """Main function for testing SHAP utilities."""
    if not SHAP_AVAILABLE:
        logger.info("SHAP not available, skipping detailed tests")
        return
    
    logger.info("Testing SHAP utilities...")
    
    # Create dummy data for testing
    np.random.seed(42)
    X_dummy = pd.DataFrame(
        np.random.rand(100, 5),
        columns=["feature_1", "feature_2", "feature_3", "feature_4", "feature_5"]
    )
    
    # Create a simple model for testing
    from sklearn.ensemble import RandomForestRegressor
    y_dummy = np.random.rand(100)
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_dummy, y_dummy)
    
    # Test compute_global_shap_values
    try:
        shap_results = compute_global_shap_values(model, X_dummy, nsamples=20)
        logger.info(f"Computed SHAP values with {len(shap_results['feature_names'])} features")
        logger.info(f"Expected value: {shap_results['expected_value']}")
        logger.info(f"Feature importance shape: {len(shap_results['feature_importance'])}")
    except Exception as e:
        logger.error(f"SHAP computation failed: {e}")
    
    # Test get_feature_importance_from_shap
    try:
        importance = get_feature_importance_from_shap(shap_results, top_n=3)
        logger.info("Top 3 features:")
        for feat in importance:
            logger.info(f"  {feat['rank']}. {feat['feature_name']}: {feat['importance']:.4f}")
    except Exception as e:
        logger.error(f"Feature importance extraction failed: {e}")
    
    # Test save_shap_results
    try:
        test_path = Path("output/test_shap_results.json")
        save_shap_results(shap_results, test_path)
        logger.info("SHAP results saved successfully")
    except Exception as e:
        logger.error(f"Failed to save SHAP results: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()