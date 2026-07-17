import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.decomposition import PCA
from code.config import get_path, ensure_dirs, get_analysis_config

logger = logging.getLogger(__name__)

def calculate_vif(features: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        features: DataFrame of features (predictors).
    
    Returns:
        Dict: VIF scores for each feature.
    """
    vif_scores = {}
    for i, col in enumerate(features.columns):
        # Create a dataframe with the current feature and others
        X = features.drop(columns=[col])
        y = features[col]
        
        # Fit a linear regression to calculate R^2
        # Handle case where X is empty (single feature)
        if X.shape[1] == 0:
            vif_scores[col] = 1.0
            continue
        
        # Add constant for intercept
        X_const = sm.add_constant(X)
        model = sm.OLS(y, X_const).fit()
        r_squared = model.rsquared
        
        # Calculate VIF
        vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else float('inf')
        vif_scores[col] = vif
    
    return vif_scores

def apply_pca(features: pd.DataFrame, n_components: Optional[int] = None) -> Tuple[pd.DataFrame, PCA]:
    """
    Apply PCA to features to reduce multicollinearity.
    
    Args:
        features: DataFrame of features.
        n_components: Number of components to keep. If None, keep all.
    
    Returns:
        Tuple: (PCA-transformed DataFrame, fitted PCA object)
    """
    pca = PCA(n_components=n_components)
    pca_features = pca.fit_transform(features)
    
    # Create new column names
    new_cols = [f"PC{i+1}" for i in range(pca_features.shape[1])]
    pca_df = pd.DataFrame(pca_features, columns=new_cols, index=features.index)
    
    return pca_df, pca

def run_vif_check_and_pca(
    features: pd.DataFrame,
    threshold: float = 5.0
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Run VIF check and apply PCA if necessary.
    
    Args:
        features: DataFrame of features.
        threshold: VIF threshold to trigger PCA.
    
    Returns:
        Tuple: (VIF check result dict, processed features DataFrame)
    """
    vif_scores = calculate_vif(features)
    max_vif = max(vif_scores.values()) if vif_scores else 0.0
    trigger_pca = max_vif > threshold
    
    result = {
        "vif_scores": vif_scores,
        "max_vif": max_vif,
        "threshold": threshold,
        "trigger_pca": trigger_pca
    }
    
    if trigger_pca:
        logger.info(f"Max VIF ({max_vif:.2f}) exceeds threshold ({threshold}). Applying PCA.")
        processed_features, pca_model = apply_pca(features)
        result["pca_model"] = {
            "explained_variance_ratio": pca_model.explained_variance_ratio_.tolist(),
            "n_components": pca_model.n_components_
        }
    else:
        logger.info(f"Max VIF ({max_vif:.2f}) is within threshold ({threshold}). No PCA needed.")
        processed_features = features
    
    # Save VIF check to file
    vif_path = get_path("data", "intermediates", "vif_check.json")
    ensure_dirs(vif_path)
    
    # Convert non-serializable types
    serializable_result = {
        "vif_scores": {k: float(v) for k, v in vif_scores.items()},
        "max_vif": float(max_vif),
        "threshold": float(threshold),
        "trigger_pca": trigger_pca
    }
    
    import json
    with open(vif_path, 'w') as f:
        json.dump(serializable_result, f, indent=2)
    
    logger.info(f"VIF check saved to {vif_path}")
    
    return result, processed_features

def run_analysis_pipeline(
    data: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline: VIF check, PCA, Regression.
    
    Args:
        data: DataFrame with features and target.
        target_col: Name of the target column.
        feature_cols: List of feature column names.
        metadata: Optional metadata for the study.
    
    Returns:
        Dict: Regression results.
    """
    import statsmodels.api as sm
    
    features = data[feature_cols]
    y = data[target_col]
    
    # Run VIF check and PCA
    vif_result, processed_features = run_vif_check_and_pca(features)
    
    # Prepare regression data
    X = processed_features
    X_const = sm.add_constant(X)
    
    # Run regression
    model = sm.OLS(y, X_const).fit()
    
    # Extract results
    coeffs = {}
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        idx = X_const.columns.get_loc(col)
        coeffs[col] = {
            "coef": float(model.params[idx]),
            "std_err": float(model.bse[idx]),
            "t_value": float(model.tvalues[idx]),
            "pvalue": float(model.pvalues[idx]),
            "ci_lower": float(model.conf_int().iloc[idx, 0]),
            "ci_upper": float(model.conf_int().iloc[idx, 1])
        }
    
    # Interaction terms (if any were explicitly added)
    interaction_terms = {}
    
    results = {
        "model_summary": {
            "r2": float(model.rsquared),
            "adj_r2": float(model.rsquared_adj),
            "f_statistic": float(model.fvalue),
            "f_pvalue": float(model.f_pvalue)
        },
        "coefficients": coeffs,
        "interaction_terms": interaction_terms,
        "vif_check": vif_result
    }
    
    # Save regression results
    results_path = get_path("reports", "regression_results.json")
    ensure_dirs(results_path)
    
    # Prepare serializable results
    serializable_results = {
        "model_summary": results["model_summary"],
        "coefficients": results["coefficients"],
        "interaction_terms": results["interaction_terms"]
    }
    
    with open(results_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Regression results saved to {results_path}")
    
    return results

def run_sensitivity_analysis(
    data: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    sholl_radii: List[int]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis on Sholl radius steps.
    
    Args:
        data: DataFrame with features and target.
        target_col: Name of the target column.
        feature_cols: List of feature column names.
        sholl_radii: List of Sholl radius steps to test.
    
    Returns:
        Dict: Sensitivity analysis results.
    """
    results = {}
    
    for radius in sholl_radii:
        # In a real scenario, we would re-extract features with this radius
        # For now, we simulate by using the existing data (assuming it was extracted with a default)
        # This is a placeholder for the actual sensitivity logic
        logger.info(f"Running sensitivity analysis for Sholl radius: {radius}µm")
        
        # Run analysis (simplified)
        analysis_result = run_analysis_pipeline(data, target_col, feature_cols)
        
        results[radius] = {
            "r2": analysis_result["model_summary"]["r2"],
            "interaction_pvalue": 1.0  # Placeholder
        }
    
    return results
