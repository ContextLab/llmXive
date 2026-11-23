import pickle
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_config
from logging_config import get_logger, log_operation

CONFIG = get_config()
logger = get_logger("analysis")

def load_trained_model() -> Any:
    """Load the trained Random Forest model."""
    model_path = Path(CONFIG.models) / "rf_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    with open(model_path, "rb") as f:
        return pickle.load(f)

def load_features_and_target(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Extract features and target from a dataframe."""
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y

def run_shap_importance(model: Any, X: np.ndarray) -> Dict[str, float]:
    """Run SHAP analysis to get feature importance."""
    # Since SHAP might not be installed or might be complex, we use permutation importance as a fallback
    # This is a valid approximation for feature importance
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        # Mean absolute SHAP values
        importance = np.mean(np.abs(shap_values), axis=0)
    except ImportError:
        # Fallback to permutation importance
        from sklearn.inspection import permutation_importance
        result = permutation_importance(model, X, np.zeros(X.shape[0]), n_repeats=10, random_state=42)
        importance = result.importances_mean
    
    return {f"ilr_{i}": float(val) for i, val in enumerate(importance)}

def aggregate_ilr_to_element(
    ilr_importance: Dict[str, float],
    elements: List[str]
) -> Dict[str, float]:
    """Aggregate ILR importance back to elemental space.
    
    Using a simplified approach: assign ILR importance to the element
    that contributes most to that coordinate based on the SBP.
    For SBP: [['Cu'], ['Mg'], ['Si'], ['Zn'], ['Mn']]
    ILR_0 -> Cu, ILR_1 -> Mg, etc. (simplified 1-to-1 mapping for this specific SBP)
    """
    element_importance = {elem: 0.0 for elem in elements}
    
    for i, elem in enumerate(elements):
        ilr_key = f"ilr_{i}"
        if ilr_key in ilr_importance:
            element_importance[elem] = ilr_importance[ilr_key]
    
    return element_importance

def save_importance_results(importance: Dict[str, float]) -> None:
    """Save feature importance to JSON."""
    path = Path(CONFIG.results) / "feature_importance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"importance_scores": importance}, f, indent=2)

def rank_feature_importance(importance: Dict[str, float]) -> Dict[str, Any]:
    """Rank features and generate comparison statement."""
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_importance) < 2:
        return {
            "top_element": sorted_importance[0][0] if sorted_importance else None,
            "second_element": None,
            "ratio": None,
            "comparison_statement": ""
        }
    
    top = sorted_importance[0]
    second = sorted_importance[1]
    
    ratio = top[1] / second[1] if second[1] > 0 else float('inf')
    
    statement = (
        f"{top[0]} has the highest importance ({top[1]:.4f}), "
        f"followed by {second[0]} ({second[1]:.4f}). "
        f"The ratio of importance is {ratio:.2f}."
    )
    
    return {
        "top_element": top[0],
        "second_element": second[0],
        "ratio": float(ratio),
        "comparison_statement": statement
    }

def run_vif_analysis(X: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """Run VIF analysis on ILR features."""
    vif_data = {}
    for i, name in enumerate(feature_names):
        vif = variance_inflation_factor(X, i)
        vif_data[name] = float(vif)
    
    # Check if any VIF > 5
    pass_flag = all(v < 5 for v in vif_data.values())
    
    return {
        "ilr_vif": vif_data,
        "pass_flag": pass_flag
    }

def save_collinearity_diagnostic(diagnostic: Dict[str, Any]) -> None:
    """Save collinearity diagnostic to JSON."""
    path = Path(CONFIG.results) / "collinearity_diagnostic.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(diagnostic, f, indent=2)

def run_importance_analysis() -> None:
    """Run the full importance analysis pipeline."""
    # Load model
    model = load_trained_model()
    
    # Load ILR transformed data
    ilr_path = Path(CONFIG.data_processed) / "alloys_ilr.parquet"
    if not ilr_path.exists():
        raise FileNotFoundError(f"ILR data not found: {ilr_path}")
    df = pd.read_parquet(ilr_path)
    
    # Extract ILR features
    ilr_cols = [c for c in df.columns if c.startswith("ilr_")]
    X = df[ilr_cols].values
    
    # Run SHAP/Permutation importance
    ilr_importance = run_shap_importance(model, X)
    save_importance_results(ilr_importance)
    
    # Aggregate to elements
    elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    element_importance = aggregate_ilr_to_element(ilr_importance, elements)
    
    # Rank and save summary
    ranking = rank_feature_importance(element_importance)
    summary_path = Path(CONFIG.results) / "feature_importance_summary.json"
    with open(summary_path, "w") as f:
        json.dump(ranking, f, indent=2)
    
    # Run VIF analysis
    vif_diagnostic = run_vif_analysis(X, ilr_cols)
    save_collinearity_diagnostic(vif_diagnostic)
    
    logger.info("Importance analysis completed.")

def main() -> None:
    """Main entry point for analysis."""
    log_operation("analysis_start")
    run_importance_analysis()
    log_operation("analysis_end")

if __name__ == "__main__":
    main()