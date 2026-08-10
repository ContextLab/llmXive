"""
Collinearity diagnostics for metabolomic features.

Implements Variance Inflation Factor (VIF) calculation to detect 
multicollinearity among selected metabolites.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from statsmodels.stats.outliers_influence import variance_inflation_factor
from code.utils.constants import DATA_PROCESSED_DIR, RESULTS_DIR
from code.utils.io import log_artifact, compute_file_hash

VIF_THRESHOLD = 5.0
VIF_DIAGNOSTICS_FILE = "collinearity_diagnostics.json"

def calculate_vif(X: pd.DataFrame, feature_names: List[str] = None) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        X: DataFrame of features (n_samples x n_features)
        feature_names: Optional list of feature names. If None, uses column names.
        
    Returns:
        pd.Series: VIF values indexed by feature name
        
    Raises:
        ValueError: If features are constant or contain NaN
    """
    if X.isnull().any().any():
        raise ValueError("Input data contains NaN values. Impute or remove missing values first.")
        
    if X.std().min() == 0:
        raise ValueError("Features with zero variance detected. Remove constant features.")
        
    if feature_names is None:
        feature_names = X.columns.tolist()
        
    # Add intercept column for VIF calculation (statsmodels expects it)
    X_with_intercept = pd.concat([pd.Series([1.0] * len(X), name='Intercept'), X], axis=1)
    
    vif_data = []
    for i, col in enumerate(X.columns):
        try:
            vif = variance_inflation_factor(X_with_intercept.values, i + 1)  # +1 because of intercept
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            vif_data.append({'feature': col, 'vif': np.nan, 'error': str(e)})
    
    return pd.Series([d['vif'] for d in vif_data], index=feature_names)

def flag_high_collinearity(vif_series: pd.Series, threshold: float = VIF_THRESHOLD) -> pd.DataFrame:
    """
    Flag features with VIF above the threshold.
    
    Args:
        vif_series: Series of VIF values from calculate_vif
        threshold: VIF threshold for flagging (default 5.0)
        
    Returns:
        DataFrame with flagged features and their VIF values
    """
    flagged = vif_series[vif_series > threshold].reset_index()
    flagged.columns = ['feature', 'vif']
    flagged['flag'] = True
    return flagged

def run_collinearity_diagnostics(
    feature_matrix: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Run full collinearity diagnostics pipeline.
    
    Args:
        feature_matrix: DataFrame of metabolite features
        output_path: Path to save diagnostics JSON. If None, uses RESULTS_DIR.
        
    Returns:
        Dictionary containing diagnostics results
    """
    if output_path is None:
        output_path = Path(RESULTS_DIR) / VIF_DIAGNOSTICS_FILE
        
    # Calculate VIF
    vif_series = calculate_vif(feature_matrix)
    
    # Flag high collinearity
    flagged = flag_high_collinearity(vif_series)
    
    # Generate summary statistics
    summary = {
        'total_features': len(vif_series),
        'high_collinearity_count': len(flagged),
        'max_vif': float(vif_series.max()),
        'mean_vif': float(vif_series.mean()),
        'threshold': VIF_THRESHOLD,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Compile full results
    results = {
        'summary': summary,
        'vif_values': vif_series.reset_index().rename(columns={'index': 'feature', 0: 'vif'}).to_dict('records'),
        'flagged_features': flagged.to_dict('records')
    }
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Log artifact
    log_artifact(str(output_path))
    
    print(f"Collinearity diagnostics saved to {output_path}")
    print(f"Total features analyzed: {summary['total_features']}")
    print(f"Features with VIF > {VIF_THRESHOLD}: {summary['high_collinearity_count']}")
    print(f"Max VIF: {summary['max_vif']:.2f}")
    
    return results

def main():
    """
    Main entry point for collinearity diagnostics.
    Loads processed data, runs VIF analysis, and saves results.
    """
    # Load processed feature matrix
    feature_file = Path(DATA_PROCESSED_DIR) / "batch_corrected_matrix.csv"
    
    if not feature_file.exists():
        raise FileNotFoundError(
            f"Processed feature matrix not found at {feature_file}. "
            "Please run the preprocessing pipeline first (T017)."
        )
    
    print(f"Loading feature matrix from {feature_file}...")
    X = pd.read_csv(feature_file, index_col=0)
    
    # Ensure numeric columns only
    X = X.select_dtypes(include=[np.number])
    
    print(f"Analyzing {X.shape[1]} features...")
    
    # Run diagnostics
    results = run_collinearity_diagnostics(X)
    
    return results

if __name__ == "__main__":
    main()
