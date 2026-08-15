"""
Task T030: Generate SHAP summary plot and feature importance table.

Reads trained models and feature data, computes SHAP values for the best model,
generates a summary plot, and writes a JSON ranking of feature importances.
"""
import os
import sys
import json
import pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import shap
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from utils.constants import DATA_DIR

# Constants
MODELS_PATH = DATA_DIR / "artifacts" / "trained_models.pkl"
FEATURES_PATH = DATA_DIR / "processed" / "solubility_features.csv"
SHAP_VALUES_PATH = DATA_DIR / "artifacts" / "shap_values.npy"
SHAP_PLOT_PATH = DATA_DIR / "artifacts" / "shap_analysis.png"
SHAP_RANKING_PATH = DATA_DIR / "artifacts" / "shap_ranking.json"
SAMPLE_SIZE = 100
RANDOM_STATE = 42

def load_models():
    """Load trained models from pickle file."""
    if not MODELS_PATH.exists():
        raise FileNotFoundError(f"Models file not found: {MODELS_PATH}")
    
    with open(MODELS_PATH, 'rb') as f:
        return pickle.load(f)

def load_features():
    """Load processed feature dataset."""
    import pandas as pd
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Features file not found: {FEATURES_PATH}")
    
    df = pd.read_csv(FEATURES_PATH)
    
    # Identify feature columns (exclude target and non-numeric metadata)
    # Assuming 'logS' is the target. Adjust if target name differs.
    target_col = 'logS'
    if target_col in df.columns:
        feature_cols = [c for c in df.columns if c != target_col]
    else:
        # Fallback: assume all numeric columns except known metadata are features
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Ensure 'logS' is excluded if it somehow got into numeric selection
        if target_col in feature_cols:
            feature_cols.remove(target_col)
    
    X = df[feature_cols].values
    feature_names = feature_cols
    
    return X, feature_names, df

def compute_shap_summary(X, model, feature_names, sample_size, random_state):
    """
    Compute SHAP values and return summary statistics.
    Uses KernelExplainer for model-agnostic support (XGBoost/RF).
    """
    # Sample background data for KernelExplainer
    np.random.seed(random_state)
    if X.shape[0] > sample_size:
        indices = np.random.choice(X.shape[0], sample_size, replace=False)
        background = X[indices]
    else:
        background = X

    # Determine explainer based on model type
    # Try XGBoost first, then fallback to KernelExplainer
    explainer = None
    try:
        if hasattr(model, 'get_xgb_model') or hasattr(model, 'trees'):
            # XGBoost model
            explainer = shap.TreeExplainer(model)
        else:
            # Random Forest or other
            explainer = shap.TreeExplainer(model)
    except Exception:
        # Fallback to KernelExplainer for any model
        print("TreeExplainer failed, falling back to KernelExplainer...")
        explainer = shap.KernelExplainer(model.predict, background)

    # Compute SHAP values
    # For KernelExplainer, this might be slow on full dataset, so use subset
    X_sample = X[:min(100, X.shape[0])]
    shap_values = explainer.shap_values(X_sample)

    # Handle case where shap_values might be a list (for multi-output, though unlikely here)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    return shap_values, X_sample, background

def generate_plot(shap_values, X_sample, feature_names, output_path):
    """Generate and save SHAP summary plot."""
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_sample, feature_names=feature_names, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def generate_ranking(shap_values, feature_names, output_path):
    """Generate feature importance ranking JSON."""
    # Calculate absolute mean SHAP value for each feature
    abs_shap = np.abs(shap_values)
    mean_abs_shap = np.mean(abs_shap, axis=0)
    
    # Sort by importance
    sorted_indices = np.argsort(mean_abs_shap)[::-1]
    
    ranking = []
    for idx in sorted_indices:
        ranking.append({
            "feature": feature_names[idx],
            "mean_abs_shap": float(mean_abs_shap[idx]),
            "rank": len(ranking) + 1
        })
    
    with open(output_path, 'w') as f:
        json.dump(ranking, f, indent=2)

def main():
    print(f"Loading models from {MODELS_PATH}...")
    models = load_models()
    
    # Identify best model (assuming 'xgboost_model' or 'rf_model' based on T021/T024 logic)
    # T024 compares XGBoost vs Abraham. T021 trains XGBoost and RF.
    # We'll prefer XGBoost if available, else RF.
    best_model = None
    if 'xgboost_model' in models:
        best_model = models['xgboost_model']
        model_name = 'xgboost'
    elif 'rf_model' in models:
        best_model = models['rf_model']
        model_name = 'rf'
    else:
        raise ValueError("No valid model found in trained_models.pkl. Expected 'xgboost_model' or 'rf_model'.")
    
    print(f"Using {model_name} model for SHAP analysis.")
    
    print(f"Loading features from {FEATURES_PATH}...")
    X, feature_names, df = load_features()
    
    print(f"Computing SHAP values on {X.shape[0]} samples...")
    shap_values, X_sample, background = compute_shap_summary(
        X, best_model, feature_names, SAMPLE_SIZE, RANDOM_STATE
    )
    
    # Save SHAP values (T029 dependency fulfillment, though T029 says to write to shap_values.npy)
    # T029 output: data/artifacts/shap_values.npy
    np.save(SHAP_VALUES_PATH, shap_values)
    print(f"Saved SHAP values to {SHAP_VALUES_PATH}")
    
    print(f"Generating SHAP summary plot to {SHAP_PLOT_PATH}...")
    generate_plot(shap_values, X_sample, feature_names, SHAP_PLOT_PATH)
    
    print(f"Generating feature ranking to {SHAP_RANKING_PATH}...")
    generate_ranking(shap_values, feature_names, SHAP_RANKING_PATH)
    
    print("Task T030 completed successfully.")

if __name__ == "__main__":
    main()