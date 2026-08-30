"""
Collinearity handling module for T022.

Detects VIF >= 5, flags results, and provides descriptive framing
without claiming independent effects when collinearity is present.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np

from utils.logger import get_logger
from utils.validators import load_schema, validate_json_against_schema

logger = get_logger(__name__)

VIF_THRESHOLD = 5.0
COLLINEARITY_FLAG = "collinearity_detected"
DEPENDENCY_FLAG = "dependent_effects_warning"

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        df: DataFrame containing the features
        feature_cols: List of column names to calculate VIF for
        
    Returns:
        Dictionary mapping feature names to VIF values
    """
    if not feature_cols:
        return {}
        
    vif_data = {}
    X = df[feature_cols].dropna()
    
    if X.empty or X.shape[0] < 2:
        logger.warning("Insufficient data for VIF calculation")
        return {col: float('inf') for col in feature_cols}
    
    # Add intercept
    X_with_intercept = sm.add_constant(X)
    
    for feature in feature_cols:
        try:
            # Regress this feature against all other features
            y = X_with_intercept[feature]
            X_other = X_with_intercept.drop(columns=[feature])
            
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(X_other, y)
            
            r_squared = model.score(X_other, y)
            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else float('inf')
            vif_data[feature] = vif
            
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature}: {e}")
            vif_data[feature] = float('inf')
    
    return vif_data

def check_collinearity_flags(
    vif_results: Dict[str, float],
    threshold: float = VIF_THRESHOLD
) -> Tuple[bool, List[str]]:
    """
    Check if any VIF values exceed the threshold.
    
    Args:
        vif_results: Dictionary of feature -> VIF values
        threshold: VIF threshold for flagging (default 5.0)
        
    Returns:
        Tuple of (is_flagged, list_of_flagged_features)
    """
    flagged_features = []
    for feature, vif in vif_results.items():
        if vif >= threshold:
            flagged_features.append(feature)
    
    is_flagged = len(flagged_features) > 0
    return is_flagged, flagged_features

def generate_descriptive_framing(
    coefficients: Dict[str, float],
    vif_results: Dict[str, float],
    is_collinear: bool,
    flagged_features: List[str],
    data_source_type: str = "unknown"
) -> Dict[str, Any]:
    """
    Generate descriptive framing for results based on collinearity status.
    
    Args:
        coefficients: Dictionary of feature -> coefficient values
        vif_results: Dictionary of feature -> VIF values
        is_collinear: Whether collinearity was detected
        flagged_features: List of features with high VIF
        data_source_type: Type of data source ("real" or "synthetic")
        
    Returns:
        Dictionary containing framed results and warnings
    """
    framing = {
        "interpretation_type": "descriptive_association" if is_collinear else "standard_interpretation",
        "collinearity_warning": is_collinear,
        "flagged_features": flagged_features,
        "warnings": [],
        "interpretation_notes": []
    }
    
    if is_collinear:
        warning_msg = (
            f"Collinearity detected (VIF >= {VIF_THRESHOLD}) for features: {', '.join(flagged_features)}. "
            "Results are framed descriptively. Independent effects cannot be reliably claimed."
        )
        framing["warnings"].append(warning_msg)
        
        # Add specific notes for flagged features
        for feat in flagged_features:
            vif_val = vif_results.get(feat, 0)
            framing["interpretation_notes"].append(
                f"Feature '{feat}' has VIF = {vif_val:.2f}. "
                "Coefficient reflects association controlling for other variables, "
                "but independent causal interpretation is limited due to collinearity."
            )
        
        # Adjust interpretation label based on data source
        if data_source_type == "real":
            framing["interpretation_label"] = "Empirical Association (Collinearity Present)"
        else:
            framing["interpretation_label"] = "Simulated Association (Collinearity Present)"
    else:
        if data_source_type == "real":
            framing["interpretation_label"] = "Empirical Association"
        else:
            framing["interpretation_label"] = "Simulated Causal Effect"
    
    return framing

def run_collinearity_analysis(
    regression_results_path: str,
    data_path: str,
    output_dir: str = "data/processed",
    feature_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main entry point for collinearity analysis and handling.
    
    Args:
        regression_results_path: Path to CSV with regression coefficients
        data_path: Path to the preprocessed data
        output_dir: Directory to save output files
        feature_cols: Optional list of feature columns to check (defaults to common predictors)
        
    Returns:
        Dictionary with analysis results and file paths
    """
    logger.info(f"Starting collinearity analysis for {regression_results_path}")
    
    # Load data
    df = pd.read_csv(data_path)
    reg_df = pd.read_csv(regression_results_path)
    
    # Default feature columns if not provided
    if feature_cols is None:
        feature_cols = ["avatar_condition", "comparison_tendency", "pre_self_esteem"]
    
    # Filter to existing columns
    available_cols = [col for col in feature_cols if col in df.columns]
    if not available_cols:
        raise ValueError(f"No feature columns found in data. Available: {df.columns.tolist()}")
    
    # Calculate VIF
    vif_results = calculate_vif(df, available_cols)
    
    # Check for collinearity
    is_collinear, flagged_features = check_collinearity_flags(vif_results)
    
    # Determine data source type
    data_source_type = "synthetic" if "synthetic" in data_path.lower() else "real"
    
    # Generate framing
    coefficients = dict(zip(reg_df["feature"], reg_df["coefficient"]))
    framing = generate_descriptive_framing(
        coefficients, vif_results, is_collinear, flagged_features, data_source_type
    )
    
    # Prepare full results
    results = {
        "vif_results": vif_results,
        "collinearity_detected": is_collinear,
        "flagged_features": flagged_features,
        "threshold_used": VIF_THRESHOLD,
        "framing": framing,
        "regression_coefficients": coefficients
    }
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save VIF results to JSON
    vif_output_path = output_path / "collinearity_vif_results.json"
    with open(vif_output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Update regression CSV with collinearity flags
    if is_collinear:
        for feat in flagged_features:
            if feat in reg_df["feature"].values:
                idx = reg_df[reg_df["feature"] == feat].index
                reg_df.loc[idx, "collinearity_flag"] = True
                reg_df.loc[idx, "interpretation_note"] = framing["interpretation_notes"][
                    next(i for i, f in enumerate(flagged_features) if f == feat)
                ]
        reg_df["collinearity_warning"] = framing["warnings"][0] if framing["warnings"] else ""
    
    # Save updated regression results
    updated_reg_path = output_path / "regression_results_with_collinearity_flags.csv"
    reg_df.to_csv(updated_reg_path, index=False)
    
    logger.info(f"Collinearity analysis complete. Output saved to {vif_output_path}")
    logger.info(f"Collinearity detected: {is_collinear}")
    if is_collinear:
        logger.warning(f"Flagged features: {flagged_features}")
    
    return {
        "vif_file": str(vif_output_path),
        "updated_regression_file": str(updated_reg_path),
        "collinearity_detected": is_collinear,
        "flagged_features": flagged_features
    }

def main():
    """Main execution for T022 collinearity handling."""
    logger.info("Executing T022: Collinearity Handling")
    
    # Default paths - adjust based on project structure
    data_path = "data/processed/preprocessed_data.csv"
    regression_path = "data/processed/regression_coefficients.csv"
    output_dir = "data/processed"
    
    # Check if files exist
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return None
    
    if not os.path.exists(regression_path):
        logger.error(f"Regression results not found: {regression_path}")
        return None
    
    try:
        results = run_collinearity_analysis(
            regression_path,
            data_path,
            output_dir
        )
        return results
    except Exception as e:
        logger.error(f"Collinearity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()