import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path if running as script
if 'code' not in sys.path[0]:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from utils.constants import DATA_PROCESSED_DIR, DATA_INTERMEDIATE_DIR
from utils.io import compute_file_hash, log_artifact

try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
except ImportError:
    raise ImportError(
        "Missing dependency 'statsmodels'. Please install it via: pip install statsmodels"
    )

def calculate_vif(X: pd.DataFrame, feature_names: List[str]) -> List[float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature in the dataframe.
    
    Args:
        X: DataFrame containing feature values (numeric).
        feature_names: List of column names corresponding to X.
        
    Returns:
        List of VIF values corresponding to each feature.
    """
    if X.empty:
        return []
    
    # Add constant for intercept if not present (required for VIF calculation)
    X_with_const = sm.add_constant(X)
    
    vif_data = []
    for i, col in enumerate(X_with_const.columns):
        if col == 'const':
            vif_data.append(0.0)  # VIF is not defined for the intercept
            continue
        try:
            vif = variance_inflation_factor(X_with_const.values, i)
            vif_data.append(vif)
        except Exception as e:
            # Handle cases where VIF cannot be calculated (e.g., constant column)
            vif_data.append(float('inf'))
    
    return vif_data

def flag_high_collinearity(vif_scores: List[Dict[str, Any]], threshold: float = 5.0) -> List[Dict[str, Any]]:
    """
    Flag features with VIF above the specified threshold.
    
    Args:
        vif_scores: List of dicts with 'feature_name' and 'vif_value'.
        threshold: VIF threshold above which collinearity is considered high.
        
    Returns:
        List of flagged features with their VIF values.
    """
    return [
        item for item in vif_scores 
        if item['vif_value'] > threshold
    ]

def run_collinearity_diagnostics(
    feature_matrix_path: str,
    output_path: str,
    threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Run full collinearity diagnostics: calculate VIF, flag high collinearity,
    and save results.
    
    Args:
        feature_matrix_path: Path to the CSV file containing the feature matrix.
        output_path: Path where the VIF results JSON will be saved.
        threshold: VIF threshold for flagging high collinearity.
        
    Returns:
        Dictionary containing the full VIF analysis results.
    """
    import statsmodels.api as sm

    # Load data
    if not os.path.exists(feature_matrix_path):
        raise FileNotFoundError(
            f"Feature matrix not found at: {feature_matrix_path}. "
            "Ensure T017 has completed successfully."
        )
    
    df = pd.read_csv(feature_matrix_path)
    
    # Ensure numeric data only
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found in the feature matrix.")
    
    X = df[numeric_cols]
    feature_names = numeric_cols.tolist()
    
    # Calculate VIF
    vif_values = calculate_vif(X, feature_names)
    
    # Format results
    vif_scores = [
        {
            "feature_name": name,
            "vif_value": float(vif)
        }
        for name, vif in zip(feature_names, vif_values)
    ]
    
    # Flag high collinearity
    flagged = flag_high_collinearity(vif_scores, threshold)
    
    # Prepare output
    results = {
        "vif_scores": vif_scores,
        "high_collinearity_features": [item['feature_name'] for item in flagged],
        "threshold_used": threshold,
        "total_features": len(vif_scores),
        "high_collinearity_count": len(flagged)
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Log artifact
    if os.path.exists(output_path):
        file_hash = compute_file_hash(output_path)
        log_artifact(
            path=output_path,
            hash_value=file_hash,
            artifact_type="collinearity_diagnostics"
        )
    
    return results

def main():
    """Main entry point for collinearity diagnostics."""
    # Define paths based on project structure
    feature_matrix_path = os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv")
    output_path = os.path.join(DATA_INTERMEDIATE_DIR, "vif_scores.json")
    
    # Ensure directories exist
    os.makedirs(DATA_INTERMEDIATE_DIR, exist_ok=True)
    
    print(f"Running collinearity diagnostics on: {feature_matrix_path}")
    print(f"Output will be saved to: {output_path}")
    
    try:
        results = run_collinearity_diagnostics(
            feature_matrix_path=feature_matrix_path,
            output_path=output_path,
            threshold=5.0
        )
        
        print(f"Analysis complete. Total features: {results['total_features']}")
        print(f"High collinearity features (VIF > 5): {results['high_collinearity_count']}")
        
        if results['high_collinearity_count'] > 0:
            print("Flagged features:")
            for feat in results['high_collinearity_features']:
                print(f"  - {feat}")
        else:
            print("No features flagged for high collinearity.")
            
        # Verify output file exists and is non-empty
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"SUCCESS: Output file created and verified: {output_path}")
        else:
            raise RuntimeError("Output file was not created or is empty.")
            
    except Exception as e:
        print(f"ERROR: Collinearity diagnostics failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
