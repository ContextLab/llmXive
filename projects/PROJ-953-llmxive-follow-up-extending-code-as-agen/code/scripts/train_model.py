import os
import sys
import json
import pickle
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, f1_score, recall_score
from scipy.stats import pearsonr
from config.loader import get_config

# Constants
RANDOM_SEED = 42
MIN_FNR_THRESHOLD = 0.001  # 0.1%
THRESHOLD_RANGE = np.linspace(0.01, 0.5, 50)  # Sweep range for sensitivity analysis

def load_features(features_path: str) -> pd.DataFrame:
    """
    Load the features.csv file containing structural metrics and ground truth.
    Raises an error if the file is missing or empty.
    """
    path = Path(features_path)
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    df = pd.read_csv(path)
    
    if df.empty:
        raise ValueError("Features file is empty. Cannot train model on zero rows.")
    
    # Ensure required columns exist
    required_cols = ['task_id', 'dynamic_execution_outcome', 'dependency_depth', 
                     'cyclomatic_complexity', 'lines_of_code']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in features.csv: {missing}")
    
    return df

def prepare_train_val_split(df: pd.DataFrame, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into training and validation sets with a fixed random seed.
    """
    train_df, val_df = train_test_split(
        df, 
        test_size=test_size, 
        random_state=RANDOM_SEED, 
        stratify=df['dynamic_execution_outcome'] if 'dynamic_execution_outcome' in df.columns else None
    )
    return train_df, val_df

def encode_target(outcome: str) -> int:
    """
    Encode the execution outcome into a binary label.
    'Pass' -> 0 (No dynamic execution needed / Safe to skip)
    'Fail', 'Timeout/Fail', 'Unparseable' -> 1 (Need dynamic execution)
    """
    if outcome == 'Pass':
        return 0
    else:
        return 1

def train_logistic_regression(X_train: np.ndarray, y_train: np.ndarray) -> LogisticRegression:
    """
    Train a Logistic Regression model (CPU-only).
    """
    model = LogisticRegression(random_state=RANDOM_SEED, max_iter=1000, solver='lbfgs')
    model.fit(X_train, y_train)
    return model

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestClassifier:
    """
    Train a Random Forest model (CPU-only).
    """
    model = RandomForestClassifier(
        n_estimators=100, 
        random_state=RANDOM_SEED, 
        n_jobs=1,  # Force single thread for CPU safety
        max_depth=None
    )
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, float]:
    """
    Evaluate model performance and return metrics.
    """
    y_pred = model.predict(X_val)
    tn, fp, fn, tp = confusion_matrix(y_val, y_pred).ravel()
    
    # False Negative Rate: FN / (FN + TP)
    # FN = predicted 0 (Safe), but actually 1 (Need Dynamic)
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    return {
        "f1": f1_score(y_val, y_pred),
        "recall": recall_score(y_val, y_pred),
        "fnr": fnr,
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn)
    }

def calculate_correlation_coefficient(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Dict[str, float]:
    """
    Calculate Pearson correlation between structural features and the binary target.
    """
    # Encode target
    y_encoded = df[target_col].apply(encode_target)
    
    correlations = {}
    for col in feature_cols:
        if col in df.columns:
            corr, _ = pearsonr(df[col], y_encoded)
            correlations[col] = float(corr)
    
    return correlations

def run_sensitivity_analysis(model, X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping thresholds and calculating FNR.
    """
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X_val)[:, 1]
    else:
        # Fallback for models without proba (shouldn't happen with our selection)
        probs = model.decision_function(X_val)
        # Normalize roughly if needed, but sklearn LR/RF usually have proba
        probs = (probs - probs.min()) / (probs.max() - probs.min())

    results = []
    min_fnr = 1.0
    best_threshold = 0.5
    unsafe_flag = False

    for thresh in THRESHOLD_RANGE:
        y_pred = (probs >= thresh).astype(int)
        
        tn, fp, fn, tp = confusion_matrix(y_val, y_pred).ravel()
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        results.append({
            "threshold": float(thresh),
            "fnr": float(fnr),
            "fp": int(fp),
            "fn": int(fn)
        })

        if fnr < min_fnr:
            min_fnr = fnr
            best_threshold = thresh

    # Check safety constraint
    if min_fnr > MIN_FNR_THRESHOLD:
        unsafe_flag = True

    return {
        "sweep_results": results,
        "minimum_achievable_fnr": float(min_fnr),
        "optimal_threshold": float(best_threshold),
        "unsafe": unsafe_flag
    }

def run_training_pipeline(features_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Main pipeline: Load data, train models, run analysis, save artifacts.
    """
    config = get_config()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    print(f"Loading features from {features_path}...")
    df = load_features(features_path)

    # Prepare features and target
    feature_cols = ['dependency_depth', 'cyclomatic_complexity', 'lines_of_code']
    # Add semantic_complexity_score if available
    if 'semantic_complexity_score' in df.columns:
        feature_cols.append('semantic_complexity_score')
    
    X = df[feature_cols].values
    y = df['dynamic_execution_outcome'].apply(encode_target).values

    # 2. Split Data
    train_df, val_df = prepare_train_val_split(df)
    X_train, X_val = train_df[feature_cols].values, val_df[feature_cols].values
    y_train, y_val = train_df['dynamic_execution_outcome'].apply(encode_target).values, val_df['dynamic_execution_outcome'].apply(encode_target).values

    # 3. Train Models
    print("Training Logistic Regression...")
    lr_model = train_logistic_regression(X_train, y_train)
    
    print("Training Random Forest...")
    rf_model = train_random_forest(X_train, y_train)

    # 4. Evaluate
    lr_metrics = evaluate_model(lr_model, X_val, y_val)
    rf_metrics = evaluate_model(rf_model, X_val, y_val)

    print(f"LR FNR: {lr_metrics['fnr']:.4f}, RF FNR: {rf_metrics['fnr']:.4f}")

    # 5. Sensitivity Analysis (on the better model, usually RF for non-linear)
    # We use RF as it generally handles structural metrics better
    print("Running sensitivity analysis on Random Forest...")
    sensitivity_results = run_sensitivity_analysis(rf_model, X_val, y_val)

    # 6. Correlation Analysis
    print("Calculating correlations...")
    correlations = calculate_correlation_coefficient(df, feature_cols, 'dynamic_execution_outcome')

    # 7. Save Artifacts
    
    # Save Models
    lr_path = output_path / "logistic_regression.pkl"
    rf_path = output_path / "random_forest.pkl"
    boundary_path = output_path / "decision_boundary.pkl"

    with open(lr_path, 'wb') as f:
        pickle.dump(lr_model, f)
    with open(rf_path, 'wb') as f:
        pickle.dump(rf_model, f)
    
    # Save Decision Boundary (Thresholds and weights)
    decision_boundary_data = {
        "model_type": "RandomForest",
        "threshold": sensitivity_results['optimal_threshold'],
        "weights": rf_model.feature_importances_.tolist(),
        "feature_names": feature_cols
    }
    with open(boundary_path, 'wb') as f:
        pickle.dump(decision_boundary_data, f)

    # Save Threshold Sweep
    sweep_path = output_path.parent / "processed" / "threshold_sweep.json"
    sweep_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sweep_path, 'w') as f:
        json.dump(sensitivity_results, f, indent=2)

    # 8. Generate Report
    report_data = {
        "model_comparison": {
            "logistic_regression": lr_metrics,
            "random_forest": rf_metrics
        },
        "sensitivity_analysis": {
            "minimum_achievable_fnr": sensitivity_results['minimum_achievable_fnr'],
            "optimal_threshold": sensitivity_results['optimal_threshold'],
            "unsafe": sensitivity_results['unsafe']
        },
        "correlation_coefficient": correlations,
        "framing": "associational",  # Explicitly required by FR-006
        "safety_status": "UNSAFE" if sensitivity_results['unsafe'] else "SAFE",
        "features_used": feature_cols,
        "random_seed": RANDOM_SEED
    }

    report_path = output_path.parent / "processed" / "model_report.json"
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"Training complete. Artifacts saved to {output_path}")
    print(f"Safety Check: {'PASSED' if not sensitivity_results['unsafe'] else 'FAILED - FNR > 0.1%'}")
    
    return report_data

def main():
    parser = argparse.ArgumentParser(description="Train predictive models for code execution necessity.")
    parser.add_argument("--features", type=str, default="data/processed/features.csv", help="Path to features.csv")
    parser.add_argument("--output", type=str, default="models", help="Directory to save models")
    args = parser.parse_args()

    try:
        run_training_pipeline(args.features, args.output)
    except Exception as e:
        print(f"Error during training pipeline: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()