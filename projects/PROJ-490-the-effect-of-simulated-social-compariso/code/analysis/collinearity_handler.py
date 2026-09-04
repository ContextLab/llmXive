import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from utils.logger import get_logger

logger = get_logger(__name__)

VIF_THRESHOLD = 5.0

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing the features.
        feature_cols: List of column names to calculate VIF for.
        
    Returns:
        DataFrame with 'feature', 'vif', and 'flagged' columns.
    """
    logger.info(f"Calculating VIF for features: {feature_cols}")
    
    # Ensure we have a numeric dataframe
    X = df[feature_cols].copy()
    X = X.dropna()
    
    if X.empty or len(X) < 2:
        logger.warning("Insufficient data for VIF calculation.")
        return pd.DataFrame(columns=['feature', 'vif', 'flagged'])
    
    # Add constant for intercept if not present (required for VIF calculation)
    if not np.all(np.any(X != 0, axis=0)):
        # Check for columns with zero variance which might cause issues
        pass
    
    try:
        vif_data = []
        for i, col in enumerate(X.columns):
            try:
                vif = variance_inflation_factor(X.values, i)
                flagged = vif >= VIF_THRESHOLD
                vif_data.append({
                    'feature': col,
                    'vif': vif,
                    'flagged': flagged
                })
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {col}: {e}")
                vif_data.append({
                    'feature': col,
                    'vif': np.nan,
                    'flagged': False
                })
        
        return pd.DataFrame(vif_data)
    except Exception as e:
        logger.error(f"Error calculating VIF: {e}")
        raise

def check_collinearity_flags(vif_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check VIF results and generate flags for collinearity issues.
    
    Args:
        vif_df: DataFrame with VIF results from calculate_vif.
        
    Returns:
        Dictionary with collinearity status and flagged features.
    """
    flagged_features = vif_df[vif_df['flagged']]['feature'].tolist()
    has_collinearity = len(flagged_features) > 0
    
    return {
        'has_collinearity': has_collinearity,
        'flagged_features': flagged_features,
        'max_vif': float(vif_df['vif'].max()) if not vif_df.empty else 0.0,
        'threshold': VIF_THRESHOLD
    }

def generate_descriptive_framing(
    vif_df: pd.DataFrame, 
    collinearity_flags: Dict[str, Any],
    coefficients: Optional[Dict[str, float]] = None
) -> str:
    """
    Generate a descriptive framing of results when collinearity is detected.
    Ensures results are described without claiming independent effects.
    
    Args:
        vif_df: DataFrame with VIF results.
        collinearity_flags: Dictionary from check_collinearity_flags.
        coefficients: Optional dictionary of regression coefficients.
        
    Returns:
        Descriptive string suitable for reports.
    """
    lines = []
    
    if collinearity_flags['has_collinearity']:
        lines.append("COLLINEARITY WARNING DETECTED")
        lines.append(f"The following variables exhibit high multicollinearity (VIF >= {VIF_THRESHOLD}):")
        for feature in collinearity_flags['flagged_features']:
            vif_val = vif_df[vif_df['feature'] == feature]['vif'].values[0]
            lines.append(f"  - {feature}: VIF = {vif_val:.2f}")
        
        lines.append("")
        lines.append("Interpretation Note:")
        lines.append("Due to the presence of high multicollinearity among predictors,")
        lines.append("the estimated coefficients should be interpreted with caution.")
        lines.append("We cannot reliably disentangle the independent effects of the")
        lines.append("collinear variables. Results are presented as descriptive associations")
        lines.append("within the context of the full model, rather than as isolated causal effects.")
        lines.append("The interaction term and main effects are reported, but claims of")
        lines.append("independent contribution for the flagged variables are avoided.")
    else:
        lines.append("No significant collinearity detected (all VIF < 5).")
        lines.append("Independent effects can be interpreted with standard confidence.")
        
    return "\n".join(lines)

def run_collinearity_analysis(
    df: pd.DataFrame,
    feature_cols: List[str],
    output_dir: Optional[Path] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Run the full collinearity analysis pipeline: calculate VIF, check flags,
    and generate descriptive framing.
    
    Args:
        df: Input DataFrame.
        feature_cols: List of feature columns to analyze.
        output_dir: Optional directory to save VIF results JSON.
        
    Returns:
        Tuple of (flags_dict, descriptive_text).
    """
    logger.info("Running collinearity analysis")
    
    vif_df = calculate_vif(df, feature_cols)
    flags = check_collinearity_flags(vif_df)
    framing = generate_descriptive_framing(vif_df, flags)
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        vif_path = output_dir / "vif_analysis.json"
        # Convert dataframe to serializable dict
        vif_dict = vif_df.to_dict(orient='records')
        with open(vif_path, 'w') as f:
            json.dump({
                'vif_results': vif_dict,
                'collinearity_flags': flags
            }, f, indent=2)
        logger.info(f"Saved VIF analysis to {vif_path}")
        
    return flags, framing

def main():
    """
    Entry point for testing the collinearity handler.
    Generates sample data to demonstrate functionality.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run collinearity analysis")
    parser.add_argument("--input", type=str, help="Path to input CSV")
    parser.add_argument("--output", type=str, help="Path to output directory")
    args = parser.parse_args()
    
    if args.input:
        df = pd.read_csv(args.input)
        # Assume standard columns for this project
        features = ['avatar_condition', 'pre_self_esteem', 'comparison_tendency']
        # Add interaction term if not present
        if 'comparison_tendency' in df.columns and 'avatar_condition' in df.columns:
            df['interaction'] = df['comparison_tendency'] * df['avatar_condition']
            features.append('interaction')
    else:
        # Create synthetic data for demonstration
        logger.info("No input provided. Generating synthetic data for demonstration.")
        np.random.seed(42)
        n = 200
        df = pd.DataFrame({
            'avatar_condition': np.random.binomial(1, 0.5, n),
            'comparison_tendency': np.random.normal(50, 10, n),
            'pre_self_esteem': np.random.normal(50, 10, n)
        })
        # Create high correlation to trigger VIF warning
        df['comparison_tendency'] = df['pre_self_esteem'] * 0.8 + np.random.normal(0, 2, n)
        df['interaction'] = df['avatar_condition'] * df['comparison_tendency']
        
        features = ['avatar_condition', 'pre_self_esteem', 'comparison_tendency', 'interaction']
    
    flags, framing = run_collinearity_analysis(df, features, Path(args.output) if args.output else None)
    
    print("\n--- Collinearity Analysis Results ---")
    print(f"Has Collinearity: {flags['has_collinearity']}")
    print(f"Flagged Features: {flags['flagged_features']}")
    print(f"Max VIF: {flags['max_vif']:.2f}")
    print("\n--- Descriptive Framing ---")
    print(framing)

if __name__ == "__main__":
    main()