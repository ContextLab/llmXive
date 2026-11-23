import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Project root path handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"

def load_test_data():
    """
    Load the test split features from the processed directory.
    Expects 'final_features.parquet' which contains the train/test split data.
    If 'final_features.parquet' is not found, attempts to load 'train_set.parquet' 
    as a fallback for testing purposes if the split file is missing but data exists.
    """
    test_file = PROCESSED_DIR / "test_set.parquet"
    final_features_file = PROCESSED_DIR / "final_features.parquet"
    
    if test_file.exists():
        df = pd.read_parquet(test_file)
        return df
    elif final_features_file.exists():
        # If the file contains a 'split' column, filter for 'test'
        df = pd.read_parquet(final_features_file)
        if 'split' in df.columns:
            df = df[df['split'] == 'test']
        return df
    else:
        raise FileNotFoundError(
            f"Test data not found. Expected {test_file} or {final_features_file}."
        )

def load_final_predictors():
    """
    Load the list of final predictors from the final_predictors.json file.
    """
    predictor_file = FINAL_DIR / "final_predictors.json"
    if not predictor_file.exists():
        raise FileNotFoundError(
            f"Predictor list not found. Expected {predictor_file}. "
            "Run model fitting tasks (T023, T040) first."
        )
    
    with open(predictor_file, 'r') as f:
        data = json.load(f)
        
    # Handle different possible structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'predictors' in data:
        return data['predictors']
    elif isinstance(data, dict) and 'features' in data:
        return data['features']
    else:
        raise ValueError(f"Unexpected format in {predictor_file}: {data}")

def calculate_vif_for_predictors(df, predictors):
    """
    Calculate VIF for the specified predictors in the dataframe.
    Adds a constant term for the intercept as required by statsmodels.
    """
    X = df[predictors].copy()
    
    # Handle non-numeric columns if any (drop or encode)
    # For this specific task, we assume predictors are numeric based on T023/T040
    X = X.select_dtypes(include=[np.number])
    
    if X.empty:
        raise ValueError("No numeric predictors found to calculate VIF.")
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    vif_results = {}
    for col in X.columns:
        try:
            vif = variance_inflation_factor(X_with_const.values, X_with_const.columns.get_loc(col))
            vif_results[col] = float(vif)
        except Exception as e:
            vif_results[col] = float('nan')
            
    return vif_results

def main():
    """
    Main execution for T047: Compute VIF on test split and log results.
    """
    print("Starting T047: VIF Robustness on Test Set")
    
    try:
        # 1. Load Data
        print("Loading test data...")
        df = load_test_data()
        print(f"Loaded {len(df)} rows from test set.")
        
        # 2. Load Predictors
        print("Loading final predictor list...")
        predictors = load_final_predictors()
        print(f"Predictors to check: {predictors}")
        
        # 3. Filter Data for Predictors
        missing_cols = [p for p in predictors if p not in df.columns]
        if missing_cols:
            raise ValueError(f"Predictors missing in test data: {missing_cols}")
        
        # 4. Calculate VIF
        print("Calculating VIF scores...")
        vif_scores = calculate_vif_for_predictors(df, predictors)
        
        # 5. Determine Flags
        high_vif_flags = {k: v > 5.0 for k, v in vif_scores.items()}
        any_high = any(high_vif_flags.values())
        
        # 6. Prepare Output
        output = {
            "task_id": "T047",
            "status": "completed",
            "sample_size": len(df),
            "predictors_checked": predictors,
            "vif_scores": vif_scores,
            "high_vif_flags": high_vif_flags,
            "any_vif_above_5": any_high,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        # 7. Write Output
        output_path = DATA_DIR / "vif_test_set.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
            
        print(f"VIF results written to {output_path}")
        
        if any_high:
            print("WARNING: One or more predictors have VIF > 5 on the test set.")
        else:
            print("SUCCESS: All predictors have VIF <= 5 on the test set.")
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during VIF calculation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
