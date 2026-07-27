"""
Task T040b: Re-fit Model after Predictor Drop.

This script reads the final predictors list (after VIF resolution from T040),
loads the training data, and re-fits the logistic regression model if a predictor
was dropped. It updates data/final/logistic_results.json with the new results.

Dependencies:
- code/models/fit_logistic.py (for fitting logic)
- code/data/split.py (for loading splits)
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path to allow relative imports if needed, 
# though we will use explicit module paths where possible.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.fit_logistic import fit_logistic_models, save_models_and_results
from data.split import load_subset_size

def load_final_predictors():
    """Load the list of final predictors after multicollinearity resolution."""
    path = PROJECT_ROOT / "data" / "final_predictors.json"
    if not path.exists():
        raise FileNotFoundError(f"final_predictors.json not found at {path}. Run T040 first.")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data.get("predictors", [])

def load_training_data():
    """Load the training dataset used for model fitting."""
    # The split task creates train_set.parquet in data/processed/
    path = PROJECT_ROOT / "data" / "processed" / "train_set.parquet"
    if not path.exists():
        raise FileNotFoundError(f"train_set.parquet not found at {path}. Run T019/T062 first.")
    
    return pd.read_parquet(path)

def main():
    print("Starting T040b: Re-fit Model after Predictor Drop")
    
    # 1. Load final predictors
    try:
        final_predictors = load_final_predictors()
        print(f"Loaded final predictors: {final_predictors}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 2. Load training data
    try:
        train_df = load_training_data()
        print(f"Loaded training data with shape: {train_df.shape}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 3. Check if we have the required columns
    # The task implies we might have dropped a predictor, so we fit with whatever
    # is in final_predictors. We need to ensure the target variable exists.
    # Assuming the target is 'compatibility_label' based on T013c.
    target_col = 'compatibility_label'
    if target_col not in train_df.columns:
        # Try to find a similar column name if exact match fails
        candidates = [c for c in train_df.columns if 'label' in c.lower() or 'target' in c.lower()]
        if candidates:
            target_col = candidates[0]
            print(f"Target column not found as '{target_col}', using '{target_col}' instead.")
        else:
            raise ValueError("Could not identify target column in training data.")

    available_predictors = [p for p in final_predictors if p in train_df.columns]
    missing_predictors = [p for p in final_predictors if p not in train_df.columns]

    if missing_predictors:
        print(f"Warning: The following predictors were requested but not found in data: {missing_predictors}")
        print("Proceeding with available predictors only.")
    
    if not available_predictors:
        raise ValueError("No valid predictors found to fit the model.")

    print(f"Fitting model with predictors: {available_predictors}")

    # 4. Fit the model
    # We reuse the logic from fit_logistic.py but adapt the predictor list
    try:
        # Prepare features
        X = train_df[available_predictors].astype(float)
        y = train_df[target_col].astype(int)

        # Fit models (Null and Full)
        # Note: fit_logistic_models expects X, y and returns results dict
        results = fit_logistic_models(X, y, available_predictors)

        # 5. Save results
        output_path = PROJECT_ROOT / "data" / "final" / "logistic_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add metadata about this specific run (T040b)
        results["run_context"] = "T040b_refit_after_drop"
        results["predictors_used"] = available_predictors
        results["predictors_dropped"] = missing_predictors

        save_models_and_results(results, output_path, models_dir=str(PROJECT_ROOT / "data" / "models"))
        
        print(f"Successfully saved logistic results to {output_path}")
        return 0

    except Exception as e:
        print(f"Error during model fitting: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
