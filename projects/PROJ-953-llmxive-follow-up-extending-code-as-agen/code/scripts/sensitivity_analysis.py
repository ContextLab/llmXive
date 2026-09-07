"""
Sensitivity Analysis Script for US3 (T031)

Performs a threshold sweep over {0.01, 0.05, 0.1} to calculate False Negative Rates (FNR).
Loads the trained model and features, evaluates predictions at each threshold,
and outputs results to data/processed/threshold_sweep.json.

FR-005 Compliance:
- Explicitly checks if FNR <= 0.1% (0.001).
- Flags model as "unsafe" if the target is not met.
"""
import os
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Project root relative to this script (code/scripts)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

# Ensure output directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_model_and_features() -> Tuple[Any, pd.DataFrame]:
    """
    Loads the trained model (decision_boundary.pkl) and the features dataset.
    Assumes T030 has generated the model file.
    """
    model_path = MODELS_DIR / "decision_boundary.pkl"
    features_path = DATA_PROCESSED_DIR / "features.csv"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}. "
                                "Please ensure T030 (model training/boundary generation) is completed first.")
    
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found at {features_path}. "
                                "Please ensure T024 (feature generation) is completed first.")

    with open(model_path, "rb") as f:
        model_data = pickle.load(f)
    
    # The model data should contain the trained classifier and potentially the threshold
    # We expect the classifier to be accessible.
    # Assuming model_data structure from T030: {'model': trained_estimator, 'threshold': float, ...}
    if 'model' not in model_data:
        raise ValueError("Loaded model data does not contain a 'model' key.")
    
    model = model_data['model']
    
    features_df = pd.read_csv(features_path)
    
    # Validate required columns
    required_cols = ['task_id', 'dynamic_execution_outcome']
    # For structural features, we need to know which columns were used for training.
    # We will infer them by excluding non-feature columns.
    # However, to be robust, we assume the model's feature_names_ attribute (if sklearn)
    # or we reconstruct based on the training script logic.
    # Since we don't have the exact training script's feature list here, we will
    # assume the features.csv contains the metrics calculated in T021/T022.
    
    return model, features_df, model_data

def calculate_fnr(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculates False Negative Rate.
    FNR = FN / (FN + TP) = FN / Total Actual Positives
    Assumes 1 = Positive (Need Dynamic Execution / Fail), 0 = Negative (Pass / No Need).
    
    In our context:
    - True Positive (TP): Predicted 1, Actual 1
    - False Negative (FN): Predicted 0, Actual 1 (DANGEROUS: Missed a failure)
    """
    # Ensure binary arrays
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Calculate Actual Positives (where y_true == 1)
    actual_positives = np.sum(y_true == 1)
    
    if actual_positives == 0:
        return 0.0  # No positive cases to miss
    
    # False Negatives: Predicted 0 but Actual 1
    false_negatives = np.sum((y_pred == 0) & (y_true == 1))
    
    fnr = false_negatives / actual_positives
    return fnr

def run_sensitivity_analysis(model: Any, features_df: pd.DataFrame, 
                             model_data: Dict[str, Any], 
                             thresholds: List[float]) -> Dict[str, Any]:
    """
    Runs the sensitivity analysis sweep.
    """
    # Identify feature columns. 
    # We assume the model was trained on the structural metrics.
    # Common columns from T021/T022: dependency_depth, cyclomatic_complexity, lines_of_code, semantic_complexity_score
    # We need to exclude non-feature columns like 'task_id', 'code_diff', 'dynamic_execution_outcome'
    exclude_cols = {'task_id', 'code_diff', 'original_code', 'dynamic_execution_outcome', 'status'}
    feature_cols = [col for col in features_df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in features.csv. "
                         "Ensure T024 generated the file with metric columns.")

    X = features_df[feature_cols].fillna(0) # Handle any potential NaNs safely
    
    # Encode ground truth: 1 if 'Fail' or 'Timeout' or 'Unparseable' (needs execution), 0 if 'Pass'
    # Based on T015/T016: dynamic_execution_outcome can be 'Pass', 'Fail', 'Timeout', 'Unparseable'
    # Safety logic: We want to catch all non-Pass cases.
    # Let's map: Pass -> 0, everything else -> 1
    y_true = features_df['dynamic_execution_outcome'].apply(
        lambda x: 0 if x == 'Pass' else 1
    ).values

    results = []
    min_fnr = float('inf')
    unsafe_flag = False
    target_fnr = 0.001 # 0.1%

    for threshold in thresholds:
        # Get probabilities or scores
        if hasattr(model, 'predict_proba'):
            # Logistic Regression, Random Forest
            probs = model.predict_proba(X)[:, 1]
        elif hasattr(model, 'decision_function'):
            # SVM (unlikely given constraints, but safe to check)
            scores = model.decision_function(X)
            # Normalize to 0-1 range for thresholding if needed, but standard threshold is 0
            # For simplicity in this specific task, we assume probabilities are available or we use a standard sigmoid
            # If decision_function, we need to map to probability or use a different threshold logic.
            # Given T029 specifies Logistic Regression and RF, we assume predict_proba.
            probs = model.decision_function(X)
            # If it's decision function, we can't easily threshold at 0.01 without calibration.
            # However, the task asks for thresholds {0.01, 0.05, 0.1}. This implies probability scores.
            # If the model doesn't have predict_proba, we might need to calibrate or assume the model is a probability estimator.
            # Let's assume the model is a probability estimator (LR/RF).
            if not hasattr(model, 'predict_proba'):
                # Fallback: Sigmoid of decision function
                probs = 1 / (1 + np.exp(-probs))
        else:
            raise ValueError("Model does not support probability prediction or decision function.")

        # Apply threshold
        y_pred = (probs >= threshold).astype(int)

        fnr = calculate_fnr(y_true, y_pred)
        
        if fnr < min_fnr:
            min_fnr = fnr

        if fnr > target_fnr:
            unsafe_flag = True

        results.append({
            "threshold": threshold,
            "fnr": float(fnr),
            "fnr_percentage": f"{fnr * 100:.4f}%"
        })

    return {
        "thresholds_evaluated": thresholds,
        "results": results,
        "minimum_achievable_fnr": float(min_fnr),
        "minimum_achievable_fnr_percentage": f"{min_fnr * 100:.4f}%",
        "target_fnr_threshold": target_fnr,
        "target_fnr_percentage": f"{target_fnr * 100:.2f}%",
        "is_safe": not unsafe_flag,
        "safety_status": "SAFE" if not unsafe_flag else "UNSAFE",
        "message": "Model meets FNR constraint." if not unsafe_flag else "Model FAILS FNR constraint (FNR > 0.1%). Marked as UNSAFE."
    }

def main():
    print("Starting Sensitivity Analysis (T031)...")
    
    try:
        model, features_df, model_data = load_model_and_features()
        print(f"Loaded model and {len(features_df)} feature rows.")
        
        # Mandated thresholds from FR-005
        thresholds = [0.01, 0.05, 0.1]
        
        print(f"Running sweep over thresholds: {thresholds}...")
        sweep_results = run_sensitivity_analysis(model, features_df, model_data, thresholds)
        
        output_path = DATA_PROCESSED_DIR / "threshold_sweep.json"
        
        with open(output_path, 'w') as f:
            json.dump(sweep_results, f, indent=2)
        
        print(f"Sensitivity analysis complete. Results written to {output_path}")
        print(f"Model Safety Status: {sweep_results['safety_status']}")
        print(f"Minimum Achievable FNR: {sweep_results['minimum_achievable_fnr_percentage']}")
        
        if not sweep_results['is_safe']:
            print("WARNING: Model is marked UNSAFE. Proceed with caution.")
            
    except Exception as e:
        print(f"Error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()
