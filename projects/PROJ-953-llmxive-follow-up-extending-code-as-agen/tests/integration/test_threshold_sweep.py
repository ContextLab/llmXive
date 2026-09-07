"""
Integration test for sensitivity analysis sweep (T027).

This test verifies that the threshold sweep logic correctly:
1. Loads the trained model and feature data.
2. Sweeps over the mandated thresholds {0.01, 0.05, 0.1}.
3. Calculates the False Negative Rate (FNR) for each threshold.
4. Outputs the results to `data/processed/threshold_sweep.json`.
5. Flags the model as "unsafe" if FNR > 0.1% for any threshold.

Prerequisites:
- `data/processed/features.csv` must exist (from T024).
- `models/decision_boundary.pkl` must exist (from T030 - though T030 depends on this,
  we will simulate the model training here for the integration test to be self-contained
  or mock the training step if T028/T029 are not yet run. However, per instructions,
  we must implement the test that *uses* the training pipeline.
  Since T028/T029 are not completed yet, we will implement the test to *run* the
  training and then the sweep, ensuring the full pipeline works end-to-end.
"""
import os
import json
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.train_model import (
    load_features,
    prepare_train_val_split,
    train_logistic_regression,
    train_random_forest,
    evaluate_model,
    calculate_correlation_coefficient
)
from code.scripts import train_model as train_model_module

# Constants
THRESHOLDS_TO_SWEEP = [0.01, 0.05, 0.1]
MAX_ACCEPTABLE_FNR = 0.001  # 0.1%
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "threshold_sweep.json"
FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "features.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "decision_boundary.pkl"

def ensure_directories():
    """Ensure output directories exist."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

def run_threshold_sweep():
    """
    Executes the sensitivity analysis sweep as described in T031.
    This function is the core logic for the integration test.
    """
    ensure_directories()

    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Required input file not found: {FEATURES_PATH}. "
            "Please ensure T024 (features generation) is completed first."
        )

    # 1. Load Data
    print(f"Loading features from {FEATURES_PATH}...")
    data = load_features(str(FEATURES_PATH))
    if not data:
        raise ValueError("Loaded features data is empty.")

    # 2. Prepare Train/Val Split
    X, y, X_val, y_val = prepare_train_val_split(data, random_seed=42)

    # 3. Train Model (Random Forest as primary choice for this study)
    print("Training Random Forest model...")
    model, _ = train_random_forest(X_train=X, y_train=y, random_seed=42)

    # 4. Calculate Correlation (T033)
    print("Calculating correlation coefficient...")
    corr_coef = calculate_correlation_coefficient(X, y)

    # 5. Perform Threshold Sweep
    results = []
    min_fnr = float('inf')
    unsafe_flag = False

    print(f"Sweeping thresholds: {THRESHOLDS_TO_SWEEP}")
    for threshold in THRESHOLDS_TO_SWEEP:
        # Evaluate model at specific threshold
        # evaluate_model returns a dict with metrics including 'fnr'
        metrics = evaluate_model(model, X_val, y_val, threshold=threshold)
        fnr = metrics.get('fnr', 1.0) # Default to worst if missing
        
        results.append({
            "threshold": threshold,
            "fnr": fnr
        })

        if fnr < min_fnr:
            min_fnr = fnr

        if fnr > MAX_ACCEPTABLE_FNR:
            unsafe_flag = True

    # 6. Determine Safety Status
    safety_status = "safe" if not unsafe_flag else "unsafe for static-only classification"
    if min_fnr > MAX_ACCEPTABLE_FNR:
        unsafe_flag = True # Even the best case is unsafe

    # 7. Construct Output
    output_data = {
        "thresholds_swept": THRESHOLDS_TO_SWEEP,
        "results": results,
        "minimum_achievable_fnr": min_fnr,
        "target_fnr": MAX_ACCEPTABLE_FNR,
        "target_met": min_fnr <= MAX_ACCEPTABLE_FNR,
        "safety_status": safety_status,
        "correlation_coefficient": corr_coef,
        "model_type": "RandomForest",
        "notes": "Associational results only. FR-006 compliance."
    }

    # 8. Write Output
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Sweep results written to {OUTPUT_PATH}")
    
    # 9. Save Model for downstream tasks (T030)
    import pickle
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {MODEL_PATH}")

    return output_data

def test_threshold_sweep_integration():
    """
    Integration test entry point.
    Runs the sweep and asserts basic structural correctness of the output.
    """
    try:
        results = run_threshold_sweep()
        
        # Assertions
        assert "results" in results, "Output missing 'results' key"
        assert len(results["results"]) == len(THRESHOLDS_TO_SWEEP), "Mismatch in threshold count"
        
        for entry in results["results"]:
            assert "threshold" in entry, "Result entry missing 'threshold'"
            assert "fnr" in entry, "Result entry missing 'fnr'"
            assert isinstance(entry["fnr"], float), "FNR must be a float"
            assert 0.0 <= entry["fnr"] <= 1.0, "FNR must be between 0 and 1"
        
        assert "minimum_achievable_fnr" in results, "Missing minimum_achievable_fnr"
        assert "safety_status" in results, "Missing safety_status"
        assert results["safety_status"] in ["safe", "unsafe for static-only classification"], "Invalid safety_status"
        
        # Verify the file was actually written
        assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} was not created"
        
        print("Integration test PASSED.")
        
    except Exception as e:
        pytest.fail(f"Threshold sweep integration test failed: {str(e)}")

if __name__ == "__main__":
    # Allow running directly for debugging
    test_threshold_sweep_integration()