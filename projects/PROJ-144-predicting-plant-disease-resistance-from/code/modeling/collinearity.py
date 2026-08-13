import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.constants import DATA_PROCESSED_DIR, RESULTS_DIR, DATA_INTERMEDIATE_DIR
from utils.io import log_artifact

def calculate_vif(df_features: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature in the dataframe.
    
    Args:
        df_features: DataFrame with shape (n_samples, n_features). 
                     Must NOT contain the target column or intercept.
                     
    Returns:
        DataFrame with columns 'feature_name' and 'vif_value'.
    """
    # Drop any non-numeric columns just in case
    numeric_df = df_features.select_dtypes(include=[np.number])
    
    if numeric_df.shape[1] == 0:
        raise ValueError("No numeric features found for VIF calculation.")
        
    if numeric_df.shape[0] < numeric_df.shape[1]:
        # Warning but proceed if possible, though VIF is unstable
        print(f"Warning: More features ({numeric_df.shape[1]}) than samples ({numeric_df.shape[0]}). VIF may be unstable.")

    vif_data = []
    feature_names = numeric_df.columns.tolist()
    
    # Calculate VIF for each feature
    for i, feature in enumerate(feature_names):
        try:
            vif = variance_inflation_factor(numeric_df.values, i)
            vif_data.append({
                'feature_name': feature,
                'vif_value': float(vif)
            })
        except Exception as e:
            # Handle cases where VIF cannot be calculated (e.g., perfect multicollinearity)
            print(f"Warning: Could not calculate VIF for feature {feature}: {e}")
            vif_data.append({
                'feature_name': feature,
                'vif_value': None
            })
    
    return pd.DataFrame(vif_data)

def flag_high_collinearity(vif_df: pd.DataFrame, threshold: float = 5.0) -> list:
    """
    Identify features with VIF above a specified threshold.
    
    Args:
        vif_df: DataFrame from calculate_vif containing 'feature_name' and 'vif_value'.
        threshold: VIF threshold to flag high collinearity (default 5.0).
        
    Returns:
        List of feature names with high collinearity.
    """
    if vif_df.empty:
        return []
        
    # Filter out None values before comparison
    valid_vif = vif_df[vif_df['vif_value'].notna()]
    high_collinearity = valid_vif[valid_vif['vif_value'] > threshold]['feature_name'].tolist()
    return high_collinearity

def run_collinearity_diagnostics(top_n: int = 10, output_path: str = None) -> dict:
    """
    Run full collinearity diagnostics:
    1. Load top N metabolites from feature importance ranking.
    2. Load processed data matrix.
    3. Subset data to top N metabolites.
    4. Calculate VIF.
    5. Flag high collinearity.
    6. Save results.
    
    Args:
        top_n: Number of top metabolites to analyze (default 10).
        output_path: Path to save VIF results JSON. Defaults to data/intermediate/vif_scores.json.
        
    Returns:
        Dictionary containing VIF analysis results.
    """
    if output_path is None:
        output_path = os.path.join(DATA_INTERMEDIATE_DIR, "vif_scores.json")
        
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Load top metabolites ranking
    ranking_path = os.path.join(RESULTS_DIR, "feature_importance_ranking.json")
    if not os.path.exists(ranking_path):
        raise FileNotFoundError(f"Feature importance ranking not found at {ranking_path}. "
                              "Ensure T020 has been executed.")
        
    with open(ranking_path, 'r') as f:
        ranking_data = json.load(f)
        
    top_metabolites = ranking_data.get('top_metabolites', [])[:top_n]
    
    if not top_metabolites:
        print("Warning: No top metabolites found in ranking. Saving empty VIF results.")
        result = {
            "top_metabolites_analyzed": [],
            "vif_scores": [],
            "high_collinearity_features": [],
            "framing": "These results represent associations, not causation"
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        log_artifact(output_path, "VIF analysis (empty)")
        return result
        
    # 2. Load processed data matrix
    matrix_path = os.path.join(DATA_PROCESSED_DIR, "batch_corrected_matrix.csv")
    if not os.path.exists(matrix_path):
        raise FileNotFoundError(f"Processed data matrix not found at {matrix_path}. "
                              "Ensure T017 has been executed.")
                             
    df_matrix = pd.read_csv(matrix_path, index_col=0)
    
    # 3. Subset data to top N metabolites
    # Ensure we only use features that exist in the matrix
    available_features = [m for m in top_metabolites if m in df_matrix.columns]
    
    if len(available_features) == 0:
        print("Warning: None of the top metabolites found in the processed matrix. Saving empty VIF results.")
        result = {
            "top_metabolites_analyzed": top_metabolites,
            "vif_scores": [],
            "high_collinearity_features": [],
            "framing": "These results represent associations, not causation"
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        log_artifact(output_path, "VIF analysis (no matching features)")
        return result
        
    df_subset = df_matrix[available_features]
    
    # 4. Calculate VIF
    # Ensure no intercept column exists (shouldn't be in metabolomics matrix, but check)
    if 'intercept' in df_subset.columns:
        df_subset = df_subset.drop(columns=['intercept'])
        
    try:
        vif_df = calculate_vif(df_subset)
    except Exception as e:
        print(f"Warning: VIF calculation failed: {e}. Saving empty results.")
        result = {
            "top_metabolites_analyzed": available_features,
            "vif_scores": [],
            "high_collinearity_features": [],
            "error": str(e),
            "framing": "These results represent associations, not causation"
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        log_artifact(output_path, "VIF analysis (failed)")
        return result
    
    # 5. Flag high collinearity
    high_collinearity = flag_high_collinearity(vif_df, threshold=5.0)
    
    # 6. Prepare results
    result = {
        "top_metabolites_analyzed": available_features,
        "vif_scores": vif_df.to_dict(orient='records'),
        "high_collinearity_features": high_collinearity,
        "framing": "These results represent associations, not causation"
    }
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    log_artifact(output_path, f"VIF analysis for {len(available_features)} top metabolites")
    
    print(f"VIF analysis complete. Results saved to {output_path}")
    if high_collinearity:
        print(f"High collinearity detected in features: {high_collinearity}")
        
    return result

def main():
    """Main entry point for collinearity diagnostics."""
    print("Starting collinearity diagnostics (T022)...")
    
    try:
        result = run_collinearity_diagnostics(top_n=10)
        
        # Verify output file exists
        output_path = os.path.join(DATA_INTERMEDIATE_DIR, "vif_scores.json")
        if os.path.exists(output_path):
            print(f"SUCCESS: VIF results written to {output_path}")
            return 0
        else:
            print("ERROR: Output file was not created.")
            return 1
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error during VIF calculation: {e}")
        # Per task spec: log warning and save empty/null if calculation fails, 
        # but we still return error code if the primary flow fails unexpectedly
        # However, the function handles graceful degradation internally.
        # If we reach here, it's a critical failure.
        return 1

if __name__ == "__main__":
    sys.exit(main())