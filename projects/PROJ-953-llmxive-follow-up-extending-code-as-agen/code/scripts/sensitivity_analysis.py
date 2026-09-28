import os
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

def load_model_and_features(model_path: str, features_path: str):
    """Load the trained model and the features dataset."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found at {features_path}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    df = pd.read_csv(features_path)
    return model, df

def calculate_fnr(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate False Negative Rate (FNR).
    FNR = FN / (FN + TP)
    In our context:
    - True Positive (TP): Model says "Need Dynamic" and Ground Truth is "Pass" (Need Dynamic is correct)
    - False Negative (FN): Model says "Static Safe" (0) but Ground Truth is "Pass" (1) -> Missed a failure risk?
    Wait, let's re-read the context of "Need for dynamic execution".
    Usually:
    Label 1 = "Need Dynamic" (High Risk/Complex)
    Label 0 = "Static Safe" (Low Risk)
    If we predict 0 (Safe) but it was actually 1 (Need Dynamic), that is a False Negative (we missed the need for dynamic execution).
    This is the dangerous case: we skipped dynamic execution when it was needed.
    """
    # y_true: 1 = Need Dynamic, 0 = Static Safe
    # y_pred: 1 = Predicted Need Dynamic, 0 = Predicted Static Safe
    # FN: True=1, Pred=0
    fn = np.sum((y_true == 1) & (y_pred == 0))
    total_positives = np.sum(y_true == 1)
    if total_positives == 0:
        return 0.0
    return fn / total_positives

def run_sensitivity_analysis(model, df, output_path: str):
    """
    Perform sensitivity analysis over thresholds {0.01, 0.05, 0.1}.
    Calculate FNR for each and determine if the model is safe (FNR <= 0.001).
    """
    thresholds = [0.01, 0.05, 0.1]
    results = {}
    min_fnr = float('inf')
    is_safe = True

    # Extract features and true labels
    # Assuming the target column is named 'dynamic_execution_outcome' or similar, mapped to 0/1
    # Based on T015, the column is 'dynamic_execution_outcome'.
    # We need to map the string outcomes to 0/1.
    # Usually: 'Pass' (Safe? No, 'Pass' means the test passed, but the task is about 'Need for Dynamic Execution')
    # Let's infer from T030/T035 context: "Need Dynamic" vs "Static Safe".
    # If the ground truth 'dynamic_execution_outcome' is 'Pass', does that mean it needed dynamic execution to verify?
    # Or does 'Pass' mean the code was safe?
    # Re-reading T012: "run the test suite to record Pass/Fail/Timeout outcomes".
    # T035: "Need for dynamic execution".
    # Context: We want to predict if we *need* to run the test suite.
    # If the code is trivial (low complexity), we might predict "Static Safe" (don't run).
    # If the code is complex, we predict "Need Dynamic" (run it).
    # The "Ground Truth" for "Need Dynamic" is likely derived from the fact that the task *was* executed and had a specific outcome?
    # Actually, usually in these papers, the label is "Does this task require dynamic execution to solve/verify?"
    # If the task is a simple text edit, maybe not. If it's a bug fix, yes.
    # However, T015 says "dynamic_execution_outcome" is the label.
    # Let's assume the label 1 = "Need Dynamic" (i.e., the task is non-trivial and required execution to solve/verify).
    # If the outcome is 'Pass', 'Fail', or 'Timeout', it implies dynamic execution was performed and yielded a result.
    # If the outcome is 'Unparseable', it might be excluded or treated differently.
    # For this analysis, we assume the target column 'dynamic_execution_outcome' has been mapped to binary 0/1 in the features.csv
    # OR we need to map it here.
    # Let's assume features.csv has a column 'need_dynamic_label' (0 or 1).
    # If not, we might need to infer: if 'dynamic_execution_outcome' is not 'Unparseable', it was run -> Label 1?
    # But the model predicts "Need Dynamic".
    # Let's look at T029: "Train Logistic Regression... to predict Need Dynamic".
    # We will assume the features.csv has a column 'target' or 'label' with 0/1.
    # If not present, we will try to map 'dynamic_execution_outcome' to 1 if it's in ['Pass', 'Fail', 'Timeout'] and 0 if 'Unparseable'?
    # No, 'Unparseable' tasks are skipped in T019. So all rows in features.csv should be parseable.
    # If they are parseable, they were run. So maybe the label is based on complexity?
    # Let's assume the target column is 'target' (0 or 1). If missing, we raise an error.

    if 'target' not in df.columns:
        # Fallback: try to map 'dynamic_execution_outcome' if it's the only option
        # But 'Pass'/'Fail' are outcomes, not necessarily "Need Dynamic" labels.
        # However, in the absence of a specific 'need_dynamic' column, we assume the task was "Need Dynamic" if it was executed.
        # Since T019 filters Unparseable, all remaining tasks were executed.
        # This implies all are 1? That makes no sense for a classifier.
        # Let's assume the pipeline generated a 'target' column in T024.
        raise ValueError("Column 'target' not found in features.csv. Ensure T024 generated the correct label column.")

    y_true = df['target'].values
    X = df.drop(columns=['target'])

    # If X has non-numeric columns, drop them
    X = X.select_dtypes(include=[np.number])

    if X.shape[1] == 0:
        raise ValueError("No numeric features found to predict with.")

    for thresh in thresholds:
        # Get probabilities
        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba(X)[:, 1]
        else:
            # Fallback for models without predict_proba
            probs = model.decision_function(X)
            # Normalize if needed, but assume model outputs score
            # For simplicity, assume 0.5 threshold logic if no proba, but we are sweeping thresholds on proba
            probs = (probs - probs.min()) / (probs.max() - probs.min() + 1e-9)

        y_pred = (probs >= thresh).astype(int)
        fnr = calculate_fnr(y_true, y_pred)
        results[thresh] = fnr
        if fnr < min_fnr:
            min_fnr = fnr
        
        # Check safety constraint: FNR <= 0.001 (0.1%)
        if fnr > 0.001:
            is_safe = False

    output_data = {
        "thresholds": results,
        "min_achievable_fnr": min_fnr,
        "target_fnr": 0.001,
        "is_safe": is_safe,
        "status": "SAFE" if is_safe else "UNSAFE"
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    return output_data

def main():
    # Paths
    model_path = "models/decision_boundary.pkl" # Expected from T030
    features_path = "data/processed/features.csv"
    output_path = "data/processed/threshold_sweep.json"

    print(f"Loading model from {model_path} and features from {features_path}...")
    try:
        model, df = load_model_and_features(model_path, features_path)
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

    print("Running sensitivity analysis...")
    results = run_sensitivity_analysis(model, df, output_path)

    print(f"Sensitivity analysis complete. Results saved to {output_path}")
    print(f"Model Status: {results['status']}")
    print(f"Thresholds FNRs: {results['thresholds']}")
    print(f"Min Achievable FNR: {results['min_achievable_fnr']}")

if __name__ == "__main__":
    main()
