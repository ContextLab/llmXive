"""
Collinearity diagnostics module for metabolomic data analysis.

Implements Variance Inflation Factor (VIF) calculation to detect
multicollinearity among selected metabolites.

FR-012: Mandatory diagnostic for collinearity.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Add project root to path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.constants import DATA_PROCESSED_DIR, RESULTS_DIR


def calculate_vif(df: pd.DataFrame, feature_columns: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    VIF measures how much the variance of an estimated regression coefficient
    increases if your predictors are correlated.
    
    VIF = 1 / (1 - R²)
    where R² is the coefficient of determination when regressing the feature
    against all other features.
    
    Args:
        df: DataFrame containing the features
        feature_columns: List of column names to calculate VIF for
        
    Returns:
        DataFrame with columns: 'feature', 'vif'
        
    Raises:
        ValueError: If any feature has zero variance
    """
    vif_data = []
    
    # Use only the specified features
    X = df[feature_columns].copy()
    
    # Check for constant features (zero variance)
    for col in X.columns:
        if X[col].var() == 0:
            raise ValueError(f"Feature '{col}' has zero variance. Cannot calculate VIF.")
    
    for i, col in enumerate(X.columns):
        # Regress feature i against all other features
        y = X[col]
        X_other = X.drop(columns=[col])
        
        # Handle case where only one feature exists
        if X_other.shape[1] == 0:
            vif = 1.0
        else:
            # Fit linear regression: y ~ X_other
            # Add intercept
            X_with_intercept = sm.add_constant(X_other)
            model = sm.OLS(y, X_with_intercept).fit()
            r_squared = model.rsquared
            
            # Calculate VIF
            if r_squared >= 1.0:
                vif = np.inf
            else:
                vif = 1.0 / (1.0 - r_squared)
        
        vif_data.append({
            'feature': col,
            'vif': vif
        })
    
    return pd.DataFrame(vif_data)


def flag_high_collinearity(vif_df: pd.DataFrame, threshold: float = 5.0) -> Tuple[List[str], pd.DataFrame]:
    """
    Flag metabolites with VIF exceeding the threshold.
    
    Args:
        vif_df: DataFrame with 'feature' and 'vif' columns
        threshold: VIF threshold above which collinearity is considered high (default: 5.0)
        
    Returns:
        Tuple of (list of high-VIF features, DataFrame with flags)
    """
    vif_df = vif_df.copy()
    vif_df['high_collinearity'] = vif_df['vif'] > threshold
    
    high_vif_features = vif_df[vif_df['high_collinearity']]['feature'].tolist()
    
    return high_vif_features, vif_df


def run_collinearity_diagnostics(
    data_path: Optional[str] = None,
    feature_columns: Optional[List[str]] = None,
    threshold: float = 5.0,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run full collinearity diagnostics on metabolomic data.
    
    Args:
        data_path: Path to batch_corrected_matrix.csv. If None, uses default location.
        feature_columns: Specific features to analyze. If None, uses all numeric columns.
        threshold: VIF threshold for flagging (default: 5.0)
        output_path: Path to save results. If None, uses default results directory.
        
    Returns:
        Dictionary containing:
            - vif_results: DataFrame with VIF values
            - high_vif_features: List of features with VIF > threshold
            - summary: Statistics about collinearity
    """
    # Determine paths
    if data_path is None:
        data_path = os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv")
    
    if output_path is None:
        output_path = os.path.join(RESULTS_DIR, "collinearity_analysis.json")
    
    # Load data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Select features
    if feature_columns is None:
        # Use all numeric columns except metadata columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Exclude common metadata columns
        exclude_cols = ['sample_id', 'subject_id', 'batch', 'resistance_label', 'resistance_binary']
        feature_columns = [col for col in numeric_cols if col not in exclude_cols]
    
    if len(feature_columns) == 0:
        raise ValueError("No features found to analyze for collinearity.")
    
    # Calculate VIF
    vif_df = calculate_vif(df, feature_columns)
    
    # Flag high collinearity
    high_vif_features, vif_df_flagged = flag_high_collinearity(vif_df, threshold)
    
    # Generate summary
    summary = {
        'total_features': len(feature_columns),
        'high_collinearity_count': len(high_vif_features),
        'threshold': threshold,
        'max_vif': float(vif_df['vif'].max()),
        'mean_vif': float(vif_df['vif'].mean()),
        'median_vif': float(vif_df['vif'].median()),
        'features_flagged': high_vif_features
    }
    
    # Prepare results
    results = {
        'vif_results': vif_df_flagged.to_dict(orient='records'),
        'high_vif_features': high_vif_features,
        'summary': summary
    }
    
    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Collinearity diagnostics complete. Results saved to: {output_path}")
    print(f"Summary: {summary['high_collinearity_count']}/{summary['total_features']} features have VIF > {threshold}")
    
    return results


def main():
    """Main entry point for running collinearity diagnostics."""
    print("Running collinearity diagnostics (VIF calculation)...")
    
    try:
        results = run_collinearity_diagnostics(
            data_path=None,  # Use default path
            feature_columns=None,  # Auto-detect
            threshold=5.0,
            output_path=None  # Use default output path
        )
        
        # Print summary
        summary = results['summary']
        print(f"\n=== Collinearity Diagnostics Summary ===")
        print(f"Total features analyzed: {summary['total_features']}")
        print(f"Features with high collinearity (VIF > {summary['threshold']}): {summary['high_collinearity_count']}")
        print(f"Max VIF: {summary['max_vif']:.2f}")
        print(f"Mean VIF: {summary['mean_vif']:.2f}")
        print(f"Median VIF: {summary['median_vif']:.2f}")
        
        if summary['features_flagged']:
            print(f"\nFlagged metabolites:")
            for feat in summary['features_flagged']:
                print(f"  - {feat}")
        
        return 0
        
    except Exception as e:
        print(f"Error running collinearity diagnostics: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
