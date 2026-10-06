import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from statsmodels.stats.outliers_influence import variance_inflation_factor

def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Load the final processed dataset containing predictors.
    Expects 'data/processed/ingredient_pairs.csv' as per pipeline output.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Processed data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['log_co_occurrence', 'flavor_similarity', 'functional_role']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required predictor columns: {missing}")
    
    return df

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors for a set of predictors.
    
    Args:
        df: DataFrame containing the predictor variables.
        predictors: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping predictor name to its VIF score.
    """
    # Select only the predictor columns
    X = df[predictors].copy()
    
    # Handle categorical variables by encoding if necessary
    # Assuming functional_role is already encoded as numeric in previous steps
    # If not, we would need to handle it, but based on T014b output schema, 
    # it should be numeric or we need to map it.
    # For safety, let's ensure all are numeric
    for col in X.columns:
        if X[col].dtype == 'object':
            # Map to numeric if it's a categorical string
            unique_vals = X[col].unique()
            mapping = {val: idx for idx, val in enumerate(unique_vals)}
            X[col] = X[col].map(mapping)
    
    # Add a constant for the intercept if needed, though VIF is usually calculated
    # on the centered matrix. statsmodels VIF function expects the design matrix.
    # We calculate VIF for each column in X.
    
    vif_data = {}
    for i, col in enumerate(X.columns):
        # VIF for a variable is calculated using the other variables as predictors
        # statsmodels variance_inflation_factor takes the whole matrix and column index
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = float(vif)
        except Exception as e:
            # If calculation fails (e.g., perfect collinearity), record as infinity
            vif_data[col] = float('inf')
    
    return vif_data

def drop_high_vif_predictors(vif_scores: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify predictors with VIF above a threshold.
    
    Args:
        vif_scores: Dictionary of VIF scores.
        threshold: VIF threshold for concern (default 5.0).
        
    Returns:
        List of predictor names with VIF > threshold.
    """
    return [name for name, score in vif_scores.items() if score > threshold]

def perform_likelihood_ratio_test():
    """
    Placeholder for LRT. This task (T023) is specifically for VIF.
    LRT is handled in T024b_LRT_Execution.
    """
    pass

def post_hoc_power_validation():
    """
    Placeholder for power validation.
    """
    pass

def resolve_multicollinearity_and_retest(data_path: str, output_path: str, threshold: float = 5.0):
    """
    Main orchestration function for VIF calculation and reporting.
    Reads processed data, calculates VIF, and writes results to JSON.
    """
    # Load data
    df = load_processed_data(data_path)
    
    # Define predictors based on T023 description
    predictors = ['log_co_occurrence', 'flavor_similarity', 'functional_role']
    
    # Calculate VIF
    vif_scores = calculate_vif(df, predictors)
    
    # Prepare output
    output_data = {
        "predictors": predictors,
        "vif_scores": vif_scores,
        "high_vif_predictors": drop_high_vif_predictors(vif_scores, threshold),
        "threshold": threshold,
        "status": "completed"
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return output_data

def main():
    """
    Entry point for T023 execution.
    """
    # Default paths based on project structure
    input_data_path = "data/processed/ingredient_pairs.csv"
    output_log_path = "data/logs/vif_scores.json"
    
    print(f"Starting VIF Calculation (T023)...")
    print(f"Input: {input_data_path}")
    print(f"Output: {output_log_path}")
    
    try:
        result = resolve_multicollinearity_and_retest(
            data_path=input_data_path,
            output_path=output_log_path
        )
        print(f"VIF Calculation completed successfully.")
        print(f"VIF Scores: {result['vif_scores']}")
        if result['high_vif_predictors']:
            print(f"Warning: High VIF detected for: {result['high_vif_predictors']}")
        else:
            print("No high VIF predictors detected.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure that T018 (Imputation & Bias Check) has completed and produced data/processed/ingredient_pairs.csv")
        raise
    except Exception as e:
        print(f"Unexpected error during VIF calculation: {e}")
        raise

if __name__ == "__main__":
    main()
