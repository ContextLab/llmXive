import os
import sys
import json
import pickle
from pathlib import Path

def verify_artifacts():
    project_root = Path(__file__).resolve().parent.parent
    errors = []

    # Check cleaned_mg.csv
    cleaned_path = project_root / "data" / "processed" / "cleaned_mg.csv"
    if not cleaned_path.exists():
        errors.append(f"Missing: {cleaned_path}")
    else:
        import pandas as pd
        df = pd.read_csv(cleaned_path)
        if len(df) == 0:
            errors.append(f"Empty: {cleaned_path}")

    # Check descriptors.csv
    desc_path = project_root / "data" / "processed" / "descriptors.csv"
    if not desc_path.exists():
        errors.append(f"Missing: {desc_path}")

    # Check model.pkl
    model_path = project_root / "artifacts" / "models" / "best_model.pkl"
    if not model_path.exists():
        errors.append(f"Missing: {model_path}")
    else:
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            if model is None:
                errors.append(f"Invalid model object: {model_path}")
        except Exception as e:
            errors.append(f"Error loading model: {e}")

    # Check metrics.json
    metrics_path = project_root / "artifacts" / "metrics" / "metrics.json"
    if not metrics_path.exists():
        errors.append(f"Missing: {metrics_path}")
    else:
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        required_keys = ['R2', 'MAE', 'feature_importances', 'null_model_r2']
        for key in required_keys:
            if key not in metrics:
                errors.append(f"Missing key '{key}' in {metrics_path}")

    # Check correlation_matrix.csv
    corr_path = project_root / "data" / "processed" / "correlation_matrix.csv"
    if not corr_path.exists():
        errors.append(f"Missing: {corr_path}")

    # Check vif_diagnostic_log.json
    vif_path = project_root / "data" / "processed" / "vif_diagnostic_log.json"
    if not vif_path.exists():
        errors.append(f"Missing: {vif_path}")

    if errors:
        print("Verification FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("Verification PASSED: All artifacts present and valid.")
        sys.exit(0)

if __name__ == "__main__":
    verify_artifacts()