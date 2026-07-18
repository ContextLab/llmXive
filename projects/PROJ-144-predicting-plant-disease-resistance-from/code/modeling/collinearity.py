"""
Collinearity diagnostics for selected metabolites.

Implements Variance Inflation Factor (VIF) calculation to detect
multicollinearity among features selected by the model.

Requirement: FR-012 - Mandatory collinearity diagnostics.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.constants import DATA_PROCESSED_DIR, RESULTS_DIR
from utils.io import compute_file_hash, log_artifact

# Threshold for flagging high collinearity
VIF_THRESHOLD = 5.0

def calculate_vif(data: pd.DataFrame, features: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for features in the dataset.
    
    VIF measures how much the variance of an estimated regression coefficient
    increases if your predictors are correlated.
    
    Formula: VIF_j = 1 / (1 - R_j^2)
    where R_j^2 is the R-squared value when feature j is regressed against all other features.
    
    Args:
        data: DataFrame containing the feature matrix (samples x features)
        features: Optional list of specific features to calculate VIF for.
                 If None, uses all numeric columns.
                 
    Returns:
        DataFrame with columns: ['feature', 'vif']
    """
    if features is None:
        # Select only numeric columns
        features = data.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(features) == 0:
        raise ValueError("No numeric features found in the dataset.")
    
    # Filter data to selected features
    X = data[features].copy()
    
    # Drop rows with any NaN values (VIF calculation requires complete cases)
    X = X.dropna()
    
    if X.shape[0] < 2:
        raise ValueError("Not enough samples to calculate VIF (need at least 2).")
    
    if X.shape[0] <= X.shape[1]:
        raise ValueError("Number of samples must be greater than number of features for VIF calculation.")
    
    vif_results = []
    
    for i, feature in enumerate(features):
        # Independent variable
        y = X[feature]
        
        # Dependent variables (all other features)
        X_other = X.drop(columns=[feature])
        
        # Check if there are other features to regress against
        if X_other.shape[1] == 0:
            # Only one feature, VIF is undefined (or 1 by convention)
            vif = 1.0
        else:
            # Calculate R-squared from regression of feature on all other features
            # Using simple matrix algebra: R^2 = 1 - (SSE / SST)
            # Or using numpy's lstsq to solve the linear system
            
            # Add intercept column
            X_other_with_intercept = np.column_stack([np.ones(X_other.shape[0]), X_other.values])
            
            try:
                # Solve the least squares problem
                coeffs, residuals, rank, s = np.linalg.lstsq(X_other_with_intercept, y.values, rcond=None)
                
                # Calculate predicted values
                y_pred = X_other_with_intercept @ coeffs
                
                # Calculate SST (Total Sum of Squares)
                ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
                
                # Calculate SSE (Sum of Squared Errors)
                ss_res = np.sum((y.values - y_pred) ** 2)
                
                # Calculate R-squared
                if ss_tot == 0:
                    r_squared = 0.0
                else:
                    r_squared = 1 - (ss_res / ss_tot)
                
                # Calculate VIF
                if r_squared >= 1.0:
                    # Numerical edge case: perfect multicollinearity
                    vif = np.inf
                else:
                    vif = 1.0 / (1.0 - r_squared)
                    
            except np.linalg.LinAlgError:
                # Singular matrix, perfect multicollinearity
                vif = np.inf
        
        vif_results.append({
            'feature': feature,
            'vif': vif
        })
    
    return pd.DataFrame(vif_results)

def flag_high_collinearity(vif_df: pd.DataFrame, threshold: float = VIF_THRESHOLD) -> pd.DataFrame:
    """
    Flag features with VIF above the threshold.
    
    Args:
        vif_df: DataFrame from calculate_vif with 'feature' and 'vif' columns
        threshold: VIF threshold for flagging (default: 5.0)
                 
    Returns:
        DataFrame with added 'flagged' boolean column
    """
    result = vif_df.copy()
    result['flagged'] = result['vif'] > threshold
    return result

def run_collinearity_diagnostics(
    feature_matrix_path: Optional[str] = None,
    labels_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict:
    """
    Main function to run collinearity diagnostics on processed data.
    
    This function:
    1. Loads the batch-corrected feature matrix
    2. Calculates VIF for all features
    3. Flags features with VIF > 5
    4. Saves results to JSON
    
    Args:
        feature_matrix_path: Path to the batch-corrected feature matrix CSV
                            (default: data/processed/batch_corrected_matrix.csv)
        labels_path: Path to labels CSV (optional, not used for VIF but for context)
        output_path: Path for output JSON (default: results/collinearity_analysis.json)
                     
    Returns:
        Dictionary containing the analysis results
    """
    # Set default paths
    if feature_matrix_path is None:
        feature_matrix_path = os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv")
    
    if output_path is None:
        # Ensure results directory exists
        results_dir = Path(RESULTS_DIR)
        results_dir.mkdir(parents=True, exist_ok=True)
        output_path = os.path.join(RESULTS_DIR, "collinearity_analysis.json")
    
    # Load data
    print(f"Loading feature matrix from: {feature_matrix_path}")
    if not os.path.exists(feature_matrix_path):
        raise FileNotFoundError(f"Feature matrix not found at: {feature_matrix_path}")
    
    df = pd.read_csv(feature_matrix_path)
    
    # Identify feature columns (exclude metadata columns like sample_id, resistance_label, etc.)
    # Typically, features are numeric columns that are not the target variable
    exclude_cols = ['sample_id', 'resistance_label', 'resistance_class', 'study_id']
    feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(feature_cols) == 0:
        raise ValueError("No numeric feature columns found in the dataset.")
    
    print(f"Calculating VIF for {len(feature_cols)} features...")
    
    # Calculate VIF
    vif_df = calculate_vif(df, features=feature_cols)
    
    # Sort by VIF descending
    vif_df = vif_df.sort_values('vif', ascending=False).reset_index(drop=True)
    
    # Flag high collinearity
    flagged_df = flag_high_collinearity(vif_df)
    
    # Generate summary statistics
    high_collinearity_count = flagged_df['flagged'].sum()
    max_vif = vif_df['vif'].max()
    mean_vif = vif_df['vif'].mean()
    median_vif = vif_df['vif'].median()
    
    # Get list of flagged features
    flagged_features = flagged_df[flagged_df['flagged']]['feature'].tolist()
    
    # Prepare results
    results = {
        'metadata': {
            'threshold': VIF_THRESHOLD,
            'total_features': len(feature_cols),
            'samples_used': df.shape[0],
            'features_with_collinearity': int(high_collinearity_count),
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        },
        'summary': {
            'max_vif': float(max_vif) if not np.isinf(max_vif) else "inf",
            'mean_vif': float(mean_vif),
            'median_vif': float(median_vif),
            'high_collinearity_count': int(high_collinearity_count),
            'high_collinearity_percentage': float(high_collinearity_count / len(feature_cols) * 100)
        },
        'flagged_features': flagged_features,
        'all_vif_values': vif_df.to_dict(orient='records')
    }
    
    # Save results to JSON
    print(f"Saving collinearity analysis to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Log artifact
    log_artifact(output_path, description="Collinearity diagnostics (VIF analysis)")
    
    # Print summary
    print("\n=== Collinearity Diagnostics Summary ===")
    print(f"Total features analyzed: {len(feature_cols)}")
    print(f"Features with VIF > {VIF_THRESHOLD}: {high_collinearity_count}")
    print(f"Max VIF: {max_vif}")
    print(f"Mean VIF: {mean_vif:.2f}")
    
    if flagged_features:
        print(f"\nFlagged features (VIF > {VIF_THRESHOLD}):")
        for feat in flagged_features:
            feat_vif = vif_df[vif_df['feature'] == feat]['vif'].values[0]
            print(f"  - {feat}: VIF = {feat_vif:.2f}")
    else:
        print(f"\nNo features flagged for high collinearity (VIF <= {VIF_THRESHOLD}).")
    
    print(f"\nResults saved to: {output_path}")
    
    return results

def main():
    """Entry point for running collinearity diagnostics."""
    try:
        results = run_collinearity_diagnostics()
        print("\nCollinearity diagnostics completed successfully.")
        return 0
    except Exception as e:
        print(f"\nError running collinearity diagnostics: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
