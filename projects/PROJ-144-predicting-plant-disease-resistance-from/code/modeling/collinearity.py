import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Add project root to path for imports if running as script
if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parents[2]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

from utils.constants import DATA_PROCESSED_DIR, RESULTS_DIR, LOG_LEVEL
from utils.io import compute_file_hash, log_artifact

logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_vif(X: pd.DataFrame, exclude_constant: bool = True) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature in a DataFrame.
    
    Args:
        X: DataFrame containing features (numeric).
        exclude_constant: If True, excludes the constant column from VIF calculation.
        
    Returns:
        Series with feature names as index and VIF values.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Ensure we have a numeric matrix
    X_numeric = X.select_dtypes(include=[np.number])
    
    if X_numeric.empty:
        raise ValueError("No numeric columns found in input data for VIF calculation.")
        
    # Add constant if needed (statsmodels requires it for OLS)
    if exclude_constant:
        X_with_const = sm.add_constant(X_numeric, has_constant='add')
        # Drop the constant column for calculation as VIF for constant is undefined/infinite
        cols = X_with_const.columns.drop('const')
    else:
        X_with_const = X_numeric
        cols = X_with_const.columns

    vif_data = pd.Series(
        [variance_inflation_factor(X_with_const.values, i) 
         for i in range(len(cols))],
        index=cols
    )
    
    return vif_data

def flag_high_collinearity(vif_series: pd.Series, threshold: float = 5.0) -> List[Dict[str, Any]]:
    """
    Identify features with VIF above the specified threshold.
    
    Args:
        vif_series: Series of VIF values.
        threshold: Threshold above which collinearity is considered high (default 5.0).
        
    Returns:
        List of dictionaries containing feature name, VIF value, and flag status.
    """
    flagged = []
    for feature, vif in vif_series.items():
        is_high = vif > threshold
        flagged.append({
            "feature_name": str(feature),
            "vif_value": float(vif),
            "is_high_collinearity": is_high
        })
    return flagged

def run_collinearity_diagnostics(
    data_path: str, 
    output_path: str, 
    threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Run full collinearity diagnostics on processed metabolomics data.
    
    Args:
        data_path: Path to the processed feature matrix CSV.
        output_path: Path where the results JSON will be saved.
        threshold: VIF threshold for flagging high collinearity.
        
    Returns:
        Dictionary containing the analysis results.
    """
    logger.info(f"Loading data from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
        
    df = pd.read_csv(data_path)
    
    # Identify feature columns (exclude sample_id, labels, etc. if present)
    # Assuming the matrix contains only metabolite features or has a clear structure
    # We select numeric columns that are likely metabolites
    feature_cols = [col for col in df.columns if col not in ['sample_id', 'label', 'binary_label']]
    X = df[feature_cols]
    
    logger.info(f"Calculating VIF for {len(X.columns)} features...")
    try:
        import statsmodels.api as sm
    except ImportError:
        raise ImportError("statsmodels is required for VIF calculation. Install it via requirements.txt.")

    vif_results = calculate_vif(X, exclude_constant=True)
    
    logger.info("Identifying high collinearity features...")
    flagged_features = flag_high_collinearity(vif_results, threshold=threshold)
    
    # Sort by VIF descending
    flagged_features.sort(key=lambda x: x['vif_value'], reverse=True)
    
    # Count high collinearity
    high_coll_count = sum(1 for f in flagged_features if f['is_high_collinearity'])
    
    results = {
        "description": "Collinearity diagnostics (VIF) for metabolite features",
        "threshold": threshold,
        "total_features_analyzed": len(X.columns),
        "high_collinearity_count": high_collarity_count,
        "vif_results": [
            {"feature_name": str(idx), "vif_value": float(val)} 
            for idx, val in vif_results.items()
        ],
        "flagged_features": flagged_features
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    # Log artifact hash
    log_artifact(output_path, "collinearity_vif_results")
    
    return results

def main():
    """Main entry point for T022."""
    # Define paths based on project structure
    # The task requires loading processed data generated by T017
    # Assuming the processed matrix is in data/processed/batch_corrected_matrix.csv
    input_file = os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv")
    output_file = os.path.join(RESULTS_DIR, "shap_analysis.json")
    
    # Check if input exists (T017 dependency)
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found. Ensure T017 has completed successfully.")
        sys.exit(1)
    
    # Load existing shap analysis if it exists (to append VIF results)
    # T024 will aggregate, but T022 must save to shap_analysis.json as per task description
    # We will update the existing file or create a new one with the VIF section
    existing_data = {}
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            existing_data = json.load(f)
    
    # Run diagnostics
    vif_results = run_collinearity_diagnostics(
        data_path=input_file,
        output_path=output_file, # Temporarily save to the path, then merge
        threshold=5.0
    )
    
    # Merge VIF results into the existing structure
    # The task says "save results to results/shap_analysis.json"
    # We assume the structure should have a 'collinearity_vif' key
    existing_data['collinearity_vif'] = vif_results.get('vif_results', [])
    existing_data['collinearity_summary'] = {
        "threshold": vif_results['threshold'],
        "high_collinearity_count": vif_results['high_collinearity_count'],
        "flagged_features": vif_results['flagged_features']
    }
    
    # Re-save with merged data
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=2)
        
    logger.info(f"Collinearity diagnostics complete. Results saved to {output_file}")
    logger.info(f"High collinearity features found: {vif_results['high_collinearity_count']}")

if __name__ == "__main__":
    main()
