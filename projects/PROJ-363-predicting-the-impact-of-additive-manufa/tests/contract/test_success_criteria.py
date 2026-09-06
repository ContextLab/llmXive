import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports if needed, though this script is mostly self-contained
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def check_sc001_model_r2():
    """
    SC-001: Model R² > Dummy R² OR R² ≥ 0.65 (for selected model).
    """
    state_path = PROJECT_ROOT / "state" / "selected_model.yaml"
    if not state_path.exists():
        raise FileNotFoundError(f"Selected model state not found at {state_path}")

    state = load_yaml(state_path)
    selected_model_info = state.get("selected_model", {})
    subset = selected_model_info.get("subset") # 'X_raw' or 'X_derived'
    
    if not subset:
        raise ValueError("Selected model subset not found in state")

    # Determine which metrics file to check
    if subset == "X_raw":
        metrics_path = PROJECT_ROOT / "results" / "reports" / "model_metrics_raw.json"
    elif subset == "X_derived":
        metrics_path = PROJECT_ROOT / "results" / "reports" / "model_metrics_derived.json"
    else:
        raise ValueError(f"Unknown subset: {subset}")

    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}")

    metrics = load_json(metrics_path)
    
    # Check if SC-001 check was performed and passed in the metrics
    # The training script should have written 'sc001_success_check': True
    sc001_flag = metrics.get("sc001_success_check")
    
    if sc001_flag is True:
        print("SC-001: PASS (Model R² > Dummy R² OR R² ≥ 0.65)")
        return True
    else:
        print(f"SC-001: FAIL (Flag in metrics: {sc001_flag})")
        return False

def check_sc002_permutation_significance():
    """
    SC-002: At least one feature has p < 0.05 in Permutation Importance.
    """
    state_path = PROJECT_ROOT / "state" / "selected_model.yaml"
    if not state_path.exists():
        raise FileNotFoundError(f"Selected model state not found at {state_path}")

    state = load_yaml(state_path)
    selected_model_info = state.get("selected_model", {})
    subset = selected_model_info.get("subset")

    if not subset:
        raise ValueError("Selected model subset not found in state")

    report_path = PROJECT_ROOT / "results" / "reports" / f"unified_statistical_analysis_{subset}.json"
    if not report_path.exists():
        raise FileNotFoundError(f"Statistical report not found at {report_path}")

    report = load_json(report_path)
    
    features = report.get("features", [])
    if not features:
        print("SC-002: FAIL (No features found in report)")
        return False

    significant_count = 0
    for feat in features:
        p_val = feat.get("p_value")
        if p_val is not None and p_val < 0.05:
            significant_count += 1

    if significant_count > 0:
        print(f"SC-002: PASS ({significant_count} features have p < 0.05)")
        return True
    else:
        print("SC-002: FAIL (No features with p < 0.05)")
        return False

def check_sc003_pipeline_duration():
    """
    SC-003: Pipeline completed within 6 hours.
    """
    start_path = PROJECT_ROOT / "results" / "reports" / "pipeline_start.json"
    end_path = PROJECT_ROOT / "results" / "reports" / "pipeline_end.json"

    if not start_path.exists():
        raise FileNotFoundError(f"Pipeline start timestamp not found at {start_path}")
    if not end_path.exists():
        raise FileNotFoundError(f"Pipeline end timestamp not found at {end_path}")

    start_data = load_json(start_path)
    end_data = load_json(end_path)

    from datetime import datetime
    
    # Parse ISO 8601 strings
    start_time = datetime.fromisoformat(start_data["timestamp"])
    end_time = datetime.fromisoformat(end_data["timestamp"])

    duration_seconds = (end_time - start_time).total_seconds()
    duration_hours = duration_seconds / 3600

    limit_hours = 6.0

    if duration_hours <= limit_hours:
        print(f"SC-003: PASS (Duration: {duration_hours:.2f} hours <= {limit_hours} hours)")
        return True
    else:
        print(f"SC-003: FAIL (Duration: {duration_hours:.2f} hours > {limit_hours} hours)")
        return False

def check_sc004_zero_missing():
    """
    SC-004: Final dataset has zero missing values.
    """
    data_path = PROJECT_ROOT / "data" / "processed" / "cleaned_316L.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {data_path}")

    df = pd.read_csv(data_path)
    missing_counts = df.isnull().sum()
    total_missing = missing_counts.sum()

    if total_missing == 0:
        print("SC-004: PASS (Zero missing values in final dataset)")
        return True
    else:
        print(f"SC-004: FAIL ({total_missing} missing values found)")
        return False

def main():
    print("Running Success Criteria Validation (T051)...")
    print("-" * 40)

    all_passed = True

    try:
        if not check_sc001_model_r2():
            all_passed = False
    except Exception as e:
        print(f"SC-001: ERROR - {e}")
        all_passed = False

    try:
        if not check_sc002_permutation_significance():
            all_passed = False
    except Exception as e:
        print(f"SC-002: ERROR - {e}")
        all_passed = False

    try:
        if not check_sc003_pipeline_duration():
            all_passed = False
    except Exception as e:
        print(f"SC-003: ERROR - {e}")
        all_passed = False

    try:
        if not check_sc004_zero_missing():
            all_passed = False
    except Exception as e:
        print(f"SC-004: ERROR - {e}")
        all_passed = False

    print("-" * 40)
    if all_passed:
        print("RESULT: ALL SUCCESS CRITERIA PASSED")
        sys.exit(0)
    else:
        print("RESULT: SOME SUCCESS CRITERIA FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()