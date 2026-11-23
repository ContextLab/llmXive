"""
Sensitivity Analysis Module.

Sweeps over thresholds to calculate False Negative Rates (FNR).
"""
import os
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

from config.loader import get_config

def load_model_and_features(models_dir: Path, features_path: Path):
    """Load trained model and features."""
    model_path = models_dir / "trained_models.pkl"
    if not model_path.exists():
        raise FileNotFoundError("Trained models not found. Run train_model.py first.")
    
    with open(model_path, 'rb') as f:
        artifacts = pickle.load(f)
    
    model_info = artifacts.get("models", {})
    scaler = artifacts.get("scaler")
    
    df = pd.read_csv(features_path)
    return model_info, scaler, df

def calculate_fnr(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate False Negative Rate."""
    # y_true: 1 = Pass (Positive), 0 = Fail (Negative)
    # y_pred: 1 = Predicted Pass, 0 = Predicted Fail
    # FN: True=1, Pred=0
    fn = np.sum((y_true == 1) & (y_pred == 0))
    p = np.sum(y_true == 1)
    return fn / p if p > 0 else 1.0

def run_sensitivity_analysis(model, scaler, df: pd.DataFrame, thresholds: list = [0.01, 0.05, 0.1]) -> dict:
    """Run sensitivity analysis over given thresholds."""
    feature_cols = ['lines_of_code', 'cyclomatic_complexity', 'dependency_depth', 'semantic_complexity_score']
    existing_cols = [c for c in feature_cols if c in df.columns]
    
    X = df[existing_cols].values
    y = df['dynamic_execution_outcome'].apply(lambda x: 1 if x == 'Pass' else 0).values
    
    X_scaled = scaler.transform(X)
    
    results = {}
    for thresh in thresholds:
        # Get probabilities
        probs = model.predict_proba(X_scaled)[:, 1]
        preds = (probs >= thresh).astype(int)
        
        fnr = calculate_fnr(y, preds)
        results[thresh] = {"fnr": float(fnr)}
    
    # Find min FNR
    min_fnr = min(r["fnr"] for r in results.values())
    return {
        "thresholds": results,
        "min_fnr": min_fnr,
        "target_fnr_met": min_fnr <= 0.001
    }

def main():
    """Main entry point."""
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    models_dir = Path(config.get("models_dir", "models"))
    processed_dir = data_dir / "processed"

    features_path = processed_dir / "features.csv"
    
    model_info, scaler, df = load_model_and_features(models_dir, features_path)
    
    # Select best model
    best_model_name = model_info.get("best_model", "rf")
    model = model_info.get("models", {}).get("rf" if best_model_name == "random_forest" else "lr")
    
    if model is None:
        print("Error: Model not found in artifacts.")
        return

    results = run_sensitivity_analysis(model, scaler, df)
    
    output_path = models_dir / "threshold_sweep.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Sensitivity analysis complete. Results saved to {output_path}")
    print(f"Min FNR: {results['min_fnr']}")
    print(f"Target (0.1%) Met: {results['target_fnr_met']}")

if __name__ == "__main__":
    main()
