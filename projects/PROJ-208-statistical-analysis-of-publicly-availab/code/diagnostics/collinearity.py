"""
Collinearity diagnostics for the mixed-effects model.

Implements Variance Inflation Factor (VIF) calculation, flags high collinearity,
and enforces descriptive language for joint relationships.

Requirement FR-006: Calculate VIF from full model design matrix, flag collinearity (VIF≥5),
and enforce descriptive language for joint relationship (not independent effects).
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config import get_config, get_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VIF_THRESHOLD = 5.0  # Threshold for flagging collinearity


def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset from the processed data directory."""
    config = get_config()
    data_path = get_path("cleaned_issues_csv", config)
    
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. "
                              "Please run the preprocessing pipeline first.")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records from {data_path}")
    return df


def prepare_design_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepare the design matrix (X) for VIF calculation.
    
    Selects numeric predictor variables used in the mixed-effects model
    and creates a design matrix with an intercept.
    
    Returns:
        Tuple of (design matrix DataFrame, list of feature names)
    """
    # Define the features used in the mixed-effects model
    # Based on typical model: resolution_time ~ language + stars + forks + age + ...
    feature_candidates = [
        'log_resolution_time',  # Target variable (will be excluded from predictors)
        'programming_language_encoded',
        'star_count',
        'fork_count',
        'issue_age_hours',
        'label_count',
        'has_assignee',
        'milestone_assigned',
        'is_pull_request',
        'repository_size_category'
    ]
    
    # Filter to features that exist in the dataframe
    available_features = [f for f in feature_candidates if f in df.columns]
    
    # Exclude the target variable from predictors
    predictor_features = [f for f in available_features if f != 'log_resolution_time']
    
    if len(predictor_features) == 0:
        raise ValueError("No predictor features found in the dataset for VIF calculation.")
    
    logger.info(f"Using {len(predictor_features)} predictor features for VIF: {predictor_features}")
    
    # Select and clean the data
    X = df[predictor_features].copy()
    
    # Handle missing values by dropping rows
    X = X.dropna()
    
    if len(X) == 0:
        raise ValueError("No valid rows after dropping missing values.")
    
    # Add constant for intercept (VIF calculation requires it)
    X_with_intercept = sm.add_constant(X)
    
    return X_with_intercept, predictor_features


def calculate_vif(X: pd.DataFrame, feature_names: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for each predictor.
    
    Args:
        X: Design matrix with constant term
        feature_names: List of original feature names (excluding constant)
    
    Returns:
        DataFrame with VIF values for each feature
    """
    vif_data = []
    
    # Calculate VIF for each feature (excluding the constant)
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data.append({
                'feature': col,
                'vif': vif,
                'vif_flagged': vif >= VIF_THRESHOLD
            })
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append({
                'feature': col,
                'vif': np.nan,
                'vif_flagged': False
            })
    
    return pd.DataFrame(vif_data)


def flag_collinearity(vif_results: pd.DataFrame) -> Dict[str, Any]:
    """
    Flag features with high collinearity and generate descriptive language.
    
    FR-006: Enforce descriptive language for joint relationship (not independent effects).
    
    Args:
        vif_results: DataFrame with VIF values
    
    Returns:
        Dictionary with collinearity analysis results and descriptive text
    """
    flagged = vif_results[vif_results['vif_flagged']]
    unflagged = vif_results[~vif_results['vif_flagged']]
    
    flagged_features = flagged['feature'].tolist() if not flagged.empty else []
    unflagged_features = unflagged['feature'].tolist() if not unflagged.empty else []
    
    # Generate descriptive language per FR-006
    if flagged_features:
        joint_relationship_desc = (
            f"The following features exhibit multicollinearity (VIF ≥ {VIF_THRESHOLD}): "
            f"{', '.join(flagged_features)}. "
            "These variables are likely related to each other, suggesting a joint relationship "
            "with the outcome rather than independent effects. Interpretation should focus on "
            "the collective contribution of these correlated predictors rather than attributing "
            "causal effects to individual variables."
        )
    else:
        joint_relationship_desc = (
            f"No features exceeded the VIF threshold of {VIF_THRESHOLD}. "
            "This suggests that multicollinearity is not a significant concern in this model, "
            "and predictors may be interpreted with greater confidence regarding their individual "
            "associations with the outcome."
        )
    
    return {
        'high_collinearity_features': flagged_features,
        'low_collinearity_features': unflagged_features,
        'count_flagged': len(flagged_features),
        'count_unflagged': len(unflagged_features),
        'threshold': VIF_THRESHOLD,
        'descriptive_language': joint_relationship_desc,
        'interpretation': (
            "Associational analysis: The model identifies correlations between predictors and "
            "resolution time. Due to potential multicollinearity, these should be interpreted as "
            "joint relationships rather than independent causal effects."
        )
    }


def analyze_collinearity(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Main function to perform collinearity analysis.
    
    Args:
        df: Optional DataFrame to use (if None, loads from disk)
    
    Returns:
        Dictionary containing VIF results, flagged features, and descriptive text
    """
    if df is None:
        df = load_cleaned_data()
    
    # Prepare design matrix
    X, feature_names = prepare_design_matrix(df)
    
    # Calculate VIF
    vif_results = calculate_vif(X, feature_names)
    
    # Flag collinearity
    collinearity_flags = flag_collinearity(vif_results)
    
    # Compile results
    results = {
        'vif_table': vif_results.to_dict('records'),
        'collinearity_flags': collinearity_flags,
        'design_matrix_shape': X.shape,
        'n_observations': len(X),
        'n_predictors': len(feature_names)
    }
    
    return results


def save_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save collinearity analysis results to JSON.
    
    Args:
        results: Dictionary of analysis results
        output_path: Optional path to save results (defaults to config)
    
    Returns:
        Path to the saved file
    """
    if output_path is None:
        config = get_config()
        output_path = get_path("collinearity_results_json", config)
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert any numpy types to native Python types for JSON serialization
    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(i) for i in obj]
        return obj
    
    serializable_results = convert_to_serializable(results)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Saved collinearity results to {output_path}")
    return output_path


def main():
    """Main entry point for collinearity analysis."""
    logger.info("Starting collinearity analysis (VIF calculation)...")
    
    try:
        # Perform analysis
        results = analyze_collinearity()
        
        # Save results
        output_file = save_results(results)
        
        # Print summary
        flags = results['collinearity_flags']
        print(f"\nCollinearity Analysis Summary:")
        print(f"  Observations: {results['n_observations']}")
        print(f"  Predictors: {results['n_predictors']}")
        print(f"  Features with VIF ≥ {flags['threshold']}: {flags['count_flagged']}")
        
        if flags['high_collinearity_features']:
            print(f"  Flagged features: {', '.join(flags['high_collinearity_features'])}")
        
        print(f"\nDescriptive Language (FR-006):")
        print(f"  {flags['descriptive_language']}")
        
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Collinearity analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
