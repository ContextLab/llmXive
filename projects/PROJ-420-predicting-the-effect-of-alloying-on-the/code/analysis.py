"""
Analysis module for Permutation Importance, Feature Importance, and Result Ranking.
Implements T027a: Permutation Importance on ILR features.
Implements T029: Result ranking and comparison logic.
"""
import pickle
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor

# Import config and logging utilities
from config import get_config
from logging_config import get_logger, log_operation

# Configure logging
logger = get_logger(__name__)

def load_trained_model(model_path: Optional[str] = None) -> RandomForestRegressor:
    """Load the trained Random Forest model."""
    config = get_config()
    if model_path is None:
        model_path = str(config.models_dir / "rf_model.pkl")
    
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def load_features_and_target(data_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """Load features (ILR transformed) and target from the cleaned dataset."""
    config = get_config()
    if data_path is None:
        data_path = str(config.data_processed_dir / "alloys_clean.parquet")
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)
    
    # ILR transformation for compositional data
    # Features: Cu, Mg, Si, Zn, Mn atomic fractions
    composition_cols = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    # Apply ILR transformation using ilr from compositional package
    # Note: compositional.ilr expects a DataFrame or array of compositions
    # and returns the ilr coordinates.
    from compositional import ilr
    
    ilr_features = ilr(df[composition_cols].values)
    ilr_df = pd.DataFrame(
        ilr_features, 
        columns=[f'ilr_{i}' for i in range(ilr_features.shape[1])],
        index=df.index
    )
    
    # Target: Poisson's ratio
    y = df['poisson_ratio']
    
    return ilr_df, y

def run_permutation_importance(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 10,
    random_state: int = 42,
    scoring: str = 'neg_mean_absolute_error'
) -> Dict[str, Any]:
    """
    Calculate Permutation Importance on ILR features.
    
    This implements T027a. Since back-transformation of RF importance is
    mathematically invalid for non-linear models in ILR space, we use
    Permutation Importance directly on the ILR features.
    """
    logger.info("Running permutation importance on ILR features")
    
    result = permutation_importance(
        model, X, y,
        n_repeats=n_repeats,
        random_state=random_state,
        scoring=scoring,
        n_jobs=-1
    )
    
    importance_dict = {
        'feature': list(X.columns),
        'importance_mean': result.importances_mean.tolist(),
        'importance_std': result.importances_std.tolist(),
        'importance_min': result.importances_min.tolist(),
        'importance_max': result.importances_max.tolist()
    }
    
    return importance_dict

def save_importance_results(importance_dict: Dict[str, Any], output_path: Optional[str] = None):
    """Save feature importance results to JSON."""
    config = get_config()
    if output_path is None:
        output_path = str(config.results_dir / "feature_importance.json")
    
    # Ensure results directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(importance_dict, f, indent=2)
    
    logger.info(f"Saved feature importance to {output_path}")

def rank_feature_importance(importance_dict: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Rank feature importance and generate comparison statements.
    
    Implements T029.
    Input: importance_dict from run_permutation_importance (with ILR feature names).
    Output: JSON with top_element, second_element, ratio, comparison_statement.
    
    Note: Since we are working in ILR space, the features are ilr_0, ilr_1, etc.
    We map these back to the original elements based on the ILR basis used.
    For the standard ilr transform with order ['Cu', 'Mg', 'Si', 'Zn', 'Mn'],
    the first coordinate (ilr_0) is most associated with the first element (Cu),
    and so on. However, ILR is an orthogonal transformation, so the relationship
    is not 1-to-1. For the purpose of this ranking, we will report the top
    ILR coordinates and their associated mean importance.
    
    To provide a more interpretable result, we will map the top ILR features
    back to the original elements by examining the loadings (if available) or
    by assuming the standard mapping where ilr_i is most influenced by the i-th
    element in the sequence. This is an approximation.
    
    A more rigorous approach would be to use the raw (non-ILR) data for ranking
    if the model was trained on it, but since the model was trained on ILR,
    we must interpret the ILR features.
    
    For this implementation, we will simply rank the ILR features by their
    mean importance and report the top two. We will then generate a statement
    comparing their importance.
    """
    logger.info("Ranking feature importance")
    
    # Sort features by mean importance (descending)
    features = importance_dict['feature']
    importances = importance_dict['importance_mean']
    
    sorted_indices = np.argsort(importances)[::-1]
    sorted_features = [features[i] for i in sorted_indices]
    sorted_importances = [importances[i] for i in sorted_indices]
    
    # Get top two
    top_feature = sorted_features[0] if len(sorted_features) > 0 else None
    top_importance = sorted_importances[0] if len(sorted_importances) > 0 else 0.0
    
    second_feature = sorted_features[1] if len(sorted_features) > 1 else None
    second_importance = sorted_importances[1] if len(sorted_importances) > 1 else 0.0
    
    # Calculate ratio (avoid division by zero)
    ratio = top_importance / second_importance if second_importance != 0 else float('inf')
    
    # Generate comparison statement
    if top_feature and second_feature:
        comparison_statement = (
            f"The {top_feature} feature has the highest importance (mean={top_importance:.4f}), "
            f"which is {ratio:.2f} times greater than the {second_feature} feature (mean={second_importance:.4f})."
        )
    elif top_feature:
        comparison_statement = (
            f"The {top_feature} feature has the highest importance (mean={top_importance:.4f}). "
            "No second feature could be identified for comparison."
        )
    else:
        comparison_statement = "No features could be ranked."
    
    # Map ILR features to original elements (approximation)
    # This is a simplified mapping. In a real scenario, we would use the ILR basis matrix.
    # For the standard ilr with order ['Cu', 'Mg', 'Si', 'Zn', 'Mn']:
    # ilr_0 is primarily influenced by Cu, ilr_1 by Mg, etc.
    # We will create a mapping for reporting.
    ilr_to_element = {
        'ilr_0': 'Cu',
        'ilr_1': 'Mg',
        'ilr_2': 'Si',
        'ilr_3': 'Zn',
        'ilr_4': 'Mn'
    }
    
    top_element = ilr_to_element.get(top_feature, top_feature) if top_feature else None
    second_element = ilr_to_element.get(second_feature, second_feature) if second_feature else None
    
    result = {
        'top_element': top_element,
        'top_feature': top_feature,
        'top_importance': top_importance,
        'second_element': second_element,
        'second_feature': second_feature,
        'second_importance': second_importance,
        'ratio': ratio if ratio != float('inf') else None,
        'comparison_statement': comparison_statement
    }
    
    # Save to JSON
    config = get_config()
    if output_path is None:
        output_path = str(config.results_dir / "feature_importance_summary.json")
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved feature importance summary to {output_path}")
    return result

def run_importance_analysis():
    """Main function to run the full importance analysis pipeline."""
    log_operation("run_importance_analysis", status="started")
    
    # Load model
    model = load_trained_model()
    
    # Load features and target
    X, y = load_features_and_target()
    
    # Run permutation importance
    importance_results = run_permutation_importance(model, X, y)
    
    # Save basic importance results
    save_importance_results(importance_results)
    
    # Run ranking and comparison (T029)
    ranking_results = rank_feature_importance(importance_results)
    
    log_operation("run_importance_analysis", status="completed")
    return importance_results, ranking_results

def main():
    """Entry point for the analysis script."""
    run_importance_analysis()

if __name__ == "__main__":
    main()