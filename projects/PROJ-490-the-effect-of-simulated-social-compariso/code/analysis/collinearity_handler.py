"""
Collinearity handling module for the ANCOVA analysis pipeline.

This module calculates Variance Inflation Factors (VIF) for model predictors,
flags high collinearity (VIF >= 5), and generates descriptive framing for
results to avoid claiming independent effects when collinearity is present.

Implements T022: Handle collinearity (VIF ≥ 5) by flagging and framing
results descriptively without claiming independent effects.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

# Import from sibling modules based on project API surface
from data.config import get_config
from utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# VIF threshold for flagging collinearity
VIF_THRESHOLD = 5.0


def calculate_vif(df: pd.DataFrame, feature_columns: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors (VIF) for specified features.
    
    Args:
        df: DataFrame containing the data
        feature_columns: List of column names to calculate VIF for
        
    Returns:
        Dictionary mapping feature names to their VIF values
        
    Raises:
        ValueError: If any feature column is not found in the DataFrame
        ValueError: If the DataFrame contains non-numeric data for the features
    """
    # Filter to only the feature columns
    features = df[feature_columns].copy()
    
    # Check for non-numeric data
    if not np.issubdtype(features.values.dtype, np.number):
        # Try to convert to numeric, handling potential categorical variables
        try:
            features = features.apply(pd.to_numeric, errors='raise')
        except (ValueError, TypeError) as e:
            raise ValueError(f"Features must be numeric for VIF calculation: {e}")
    
    # Add constant term for intercept
    features_with_const = add_constant(features)
    
    vif_results = {}
    for i, col in enumerate(features_with_const.columns):
        if col == 'const':
            continue
        
        vif_val = variance_inflation_factor(features_with_const.values, i)
        vif_results[col] = vif_val
        
        logger.debug(f"VIF for {col}: {vif_val:.4f}")
    
    return vif_results


def check_collinearity_flags(vif_results: Dict[str, float], threshold: float = VIF_THRESHOLD) -> Dict[str, Any]:
    """
    Check VIF results for collinearity flags.
    
    Args:
        vif_results: Dictionary of feature VIF values
        threshold: VIF threshold for flagging (default: 5.0)
        
    Returns:
        Dictionary containing:
            - 'has_collinearity': bool, True if any VIF >= threshold
            - 'flagged_features': List of feature names with high VIF
            - 'max_vif': Maximum VIF value
            - 'warning_message': String describing the collinearity issue
    """
    flagged_features = [
        feature for feature, vif_val in vif_results.items()
        if vif_val >= threshold
    ]
    
    max_vif = max(vif_results.values()) if vif_results else 0.0
    has_collinearity = len(flagged_features) > 0
    
    warning_message = ""
    if has_collinearity:
        warning_message = (
            f"Collinearity detected: {len(flagged_features)} feature(s) have VIF >= {threshold}. "
            f"Flagged features: {', '.join(flagged_features)}. "
            f"Maximum VIF: {max_vif:.2f}. "
            f"Results should be framed descriptively without claiming independent effects."
        )
        logger.warning(warning_message)
    else:
        logger.info(f"No collinearity detected. Max VIF: {max_vif:.2f}")
    
    return {
        'has_collinearity': has_collinearity,
        'flagged_features': flagged_features,
        'max_vif': max_vif,
        'warning_message': warning_message
    }


def generate_descriptive_framing(
    coefficients: List[Dict[str, Any]],
    collinearity_flags: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate descriptive framing for regression coefficients when collinearity is present.
    
    This function modifies the interpretation of coefficients to avoid claiming
    independent effects when collinearity is detected.
    
    Args:
        coefficients: List of coefficient dictionaries with 'name', 'estimate', 'std_err', 'p_value'
        collinearity_flags: Output from check_collinearity_flags
        
    Returns:
        List of coefficient dictionaries with added 'framing' and 'interpretation' fields
    """
    framed_coefficients = []
    
    if collinearity_flags['has_collinearity']:
        flagged_set = set(collinearity_flags['flagged_features'])
        framing_note = (
            "Due to collinearity (VIF >= 5), this coefficient represents an association "
            "conditional on other variables in the model. Independent causal effects "
            "cannot be claimed."
        )
    else:
        framing_note = "Standard interpretation applies."
    
    for coef in coefficients:
        name = coef.get('name', 'unknown')
        
        # Create a copy to avoid modifying the original
        framed_coef = coef.copy()
        
        # Add framing information
        framed_coef['framing'] = 'descriptive_association' if collinearity_flags['has_collinearity'] else 'standard'
        framed_coef['interpretation_note'] = framing_note if collinearity_flags['has_collinearity'] else None
        framed_coef['is_flagged'] = name in flagged_set if collinearity_flags['has_collinearity'] else False
        
        # Adjust interpretation text if flagged
        if name in flagged_set:
            original_interpretation = framed_coef.get('interpretation', '')
            if original_interpretation:
                framed_coef['interpretation'] = (
                    f"{original_interpretation} Note: Collinearity present; "
                    f"effect is conditional on other predictors."
                )
        
        framed_coefficients.append(framed_coef)
    
    return framed_coefficients


def run_collinearity_analysis(
    df: pd.DataFrame,
    feature_columns: List[str],
    coefficients: Optional[List[Dict[str, Any]]] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run complete collinearity analysis pipeline.
    
    This function:
    1. Calculates VIF for all features
    2. Checks for collinearity flags
    3. Generates descriptive framing for coefficients if needed
    4. Optionally updates diagnostics file
    
    Args:
        df: DataFrame with the data
        feature_columns: List of feature column names
        coefficients: Optional list of coefficient dictionaries to frame
        output_path: Optional path to update model_diagnostics.json
        
    Returns:
        Dictionary containing:
            - vif_results: Dict of VIF values
            - collinearity_flags: Dict with flag information
            - framed_coefficients: List of framed coefficients (if provided)
            - collinearity_warning: String warning message
    """
    logger.info(f"Running collinearity analysis for features: {feature_columns}")
    
    # Calculate VIF
    vif_results = calculate_vif(df, feature_columns)
    
    # Check for flags
    collinearity_flags = check_collinearity_flags(vif_results)
    
    # Frame coefficients if provided
    framed_coefficients = None
    if coefficients is not None:
        framed_coefficients = generate_descriptive_framing(coefficients, collinearity_flags)
    
    # Prepare result dictionary
    result = {
        'vif_results': vif_results,
        'collinearity_flags': collinearity_flags,
        'collinearity_warning': collinearity_flags['warning_message']
    }
    
    if framed_coefficients is not None:
        result['framed_coefficients'] = framed_coefficients
    
    # Update diagnostics file if output_path provided
    if output_path is not None:
        update_diagnostics_with_collinearity(output_path, result)
    
    return result


def update_diagnostics_with_collinearity(
    diagnostics_path: Path,
    collinearity_result: Dict[str, Any]
) -> None:
    """
    Update the model_diagnostics.json file with collinearity information.
    
    Args:
        diagnostics_path: Path to the model_diagnostics.json file
        collinearity_result: Result dictionary from run_collinearity_analysis
    """
    logger.info(f"Updating diagnostics file: {diagnostics_path}")
    
    # Load existing diagnostics if it exists
    if diagnostics_path.exists():
        try:
            with open(diagnostics_path, 'r') as f:
                diagnostics = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing diagnostics: {e}. Creating new file.")
            diagnostics = {}
    else:
        diagnostics = {}
    
    # Ensure 'assumptions' key exists
    if 'assumptions' not in diagnostics:
        diagnostics['assumptions'] = {}
    
    # Update with collinearity information
    diagnostics['assumptions']['collinearity_warning'] = collinearity_result['collinearity_warning']
    diagnostics['assumptions']['vif_results'] = collinearity_result['vif_results']
    diagnostics['assumptions']['vif_max'] = collinearity_result['collinearity_flags']['max_vif']
    diagnostics['assumptions']['has_collinearity'] = collinearity_result['collinearity_flags']['has_collinearity']
    diagnostics['assumptions']['flagged_features'] = collinearity_result['collinearity_flags']['flagged_features']
    
    # Write updated diagnostics
    with open(diagnostics_path, 'w') as f:
        json.dump(diagnostics, f, indent=2)
    
    logger.info("Diagnostics file updated with collinearity information")


def main() -> None:
    """
    Main entry point for collinearity analysis.
    
    This function:
    1. Loads the imputed data
    2. Runs collinearity analysis on model features
    3. Updates the model diagnostics file
    """
    config = get_config()
    imputed_data_path = config['paths']['imputed_data']
    diagnostics_path = config['paths']['model_diagnostics']
    
    logger.info("Starting collinearity analysis")
    
    # Load imputed data
    if not Path(imputed_data_path).exists():
        logger.error(f"Imputed data file not found: {imputed_data_path}")
        return
    
    df = pd.read_csv(imputed_data_path)
    
    # Define feature columns (excluding outcome and covariate)
    # For ANCOVA: outcome=post_self_esteem, covariate=pre_self_esteem
    # Predictors: avatar_condition, comparison_tendency, interaction
    feature_columns = ['avatar_condition', 'comparison_tendency']
    
    # Check for interaction term if it exists
    if 'interaction' in df.columns:
        feature_columns.append('interaction')
    
    # Run collinearity analysis
    result = run_collinearity_analysis(
        df=df,
        feature_columns=feature_columns,
        output_path=Path(diagnostics_path)
    )
    
    logger.info("Collinearity analysis completed")
    logger.info(f"Collinearity warning: {result['collinearity_warning']}")

if __name__ == '__main__':
    main()