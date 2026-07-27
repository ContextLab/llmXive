"""
T047: VIF Robustness on Test Set

Computes Variance Inflation Factor (VIF) on the test split of the data.
Flags any predictor with VIF > 5.
Outputs: data/vif_test_set.json

Dependencies:
- data/split_config.json (to locate test set)
- data/final_predictors.json (to know which columns to check)
- The actual test set parquet file (train_set.parquet is used as a base for split logic, 
  but we specifically look for test_set.parquet or derive it from split_config)
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any

# Add root to path for imports if running as script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.memory_monitor import check_memory_limit

def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_vif_for_columns(df: pd.DataFrame, columns: List[str]) -> Dict[str, float]:
    """
    Calculate VIF for a list of columns in a DataFrame.
    Returns a dictionary mapping column name to VIF score.
    """
    vif_results = {}
    
    # Filter dataframe to only the relevant columns
    # Ensure we have an intercept column for regression if needed, 
    # but standard VIF calculation usually iterates each column as dependent 
    # against others.
    
    if len(columns) < 2:
        return {col: 0.0 for col in columns}

    for i, col in enumerate(columns):
        if col not in df.columns:
            vif_results[col] = np.nan
            continue
        
        # Prepare X and y for this iteration
        # y is the current column
        y = df[col].dropna()
        # X is all other columns in the list
        other_cols = [c for c in columns if c != col]
        X = df[other_cols].loc[y.index]
        
        # Drop rows where y is NaN (already done) or where any X is NaN
        mask = ~X.isna().any(axis=1)
        y = y[mask]
        X = X[mask]
        
        if len(y) < 2 or X.shape[1] == 0:
            vif_results[col] = np.nan
            continue

        try:
            # Fit linear model: y = beta0 + beta1*x1 + ... + error
            # VIF = 1 / (1 - R^2)
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(X, y)
            r_squared = model.score(X, y)
            
            if r_squared >= 1.0:
                vif_results[col] = float('inf')
            else:
                vif = 1.0 / (1.0 - r_squared)
                vif_results[col] = vif
        except Exception as e:
            # Singular matrix or other numerical issues
            vif_results[col] = float('inf')
            
    return vif_results

def main():
    # Check memory limit
    check_memory_limit(limit_mb=6144)

    # Paths
    split_config_path = ROOT / "data" / "split_config.json"
    predictors_path = ROOT / "data" / "final_predictors.json"
    output_path = ROOT / "data" / "vif_test_set.json"
    
    # Load configuration
    try:
        split_config = load_json(split_config_path)
    except FileNotFoundError:
        # Fallback if split_config doesn't explicitly name the test file but we know the convention
        # Based on T019/T023, the split file is usually named test_set.parquet or similar
        # Let's assume the split_config has 'test_file' key or we derive it.
        # If missing, we try to find the file based on common patterns or error out.
        raise FileNotFoundError(f"Cannot find {split_config_path}. Run T019 first.")

    # Determine test file path
    # The split config should contain the path to the test set relative to data/
    test_file_rel = split_config.get('test_file', 'test_set.parquet')
    # Handle cases where it might be a full path or relative
    test_file_path = ROOT / "data" / "processed" / test_file_rel
    
    if not test_file_path.exists():
        # Try alternative naming if standard one fails
        alt_path = ROOT / "data" / "processed" / "test_data.parquet"
        if alt_path.exists():
            test_file_path = alt_path
        else:
            raise FileNotFoundError(f"Test set file not found at {test_file_path} or {alt_path}. Run T019.")

    # Load predictors
    try:
        predictors_data = load_json(predictors_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Cannot find {predictors_path}. Run T023 first.")

    final_predictors = predictors_data.get('final_predictors', [])
    if not final_predictors:
        print("No predictors found in final_predictors.json. Skipping VIF calculation.")
        save_json({"status": "skipped", "reason": "no_predictors"}, output_path)
        return

    # Load test data
    print(f"Loading test data from {test_file_path}...")
    try:
        df = pd.read_parquet(test_file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load test data: {e}")

    # Filter columns that exist in the dataframe
    available_predictors = [col for col in final_predictors if col in df.columns]
    missing_predictors = [col for col in final_predictors if col not in df.columns]
    
    if missing_predictors:
        print(f"Warning: Predictors missing in test data: {missing_predictors}")
    
    if not available_predictors:
        print("No predictors available in test data for VIF calculation.")
        save_json({"status": "skipped", "reason": "no_available_predictors"}, output_path)
        return

    # Calculate VIF
    print(f"Calculating VIF for {len(available_predictors)} predictors on test set...")
    vif_scores = calculate_vif_for_columns(df, available_predictors)

    # Analyze results
    high_vif = {k: v for k, v in vif_scores.items() if v > 5.0}
    status = "PASS" if not high_vif else "FAIL"
    
    result = {
        "status": status,
        "timestamp": pd.Timestamp.now().isoformat(),
        "test_file": str(test_file_path.relative_to(ROOT)),
        "predictors_checked": len(available_predictors),
        "vif_scores": {k: float(v) if np.isfinite(v) else (999999.0 if v == float('inf') else None) for k, v in vif_scores.items()},
        "high_vif_predictors": list(high_vif.keys()),
        "threshold": 5.0,
        "flags": {
            "any_above_threshold": len(high_vif) > 0,
            "max_vif": max(vif_scores.values()) if vif_scores else 0
        }
    }

    save_json(result, output_path)
    print(f"VIF analysis complete. Output saved to {output_path}")
    if high_vif:
        print(f"WARNING: {len(high_vif)} predictors have VIF > 5.0")

if __name__ == "__main__":
    main()