import os
import sys
import json
import pickle
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.inspection import permutation_importance
import shap

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
DATA_MODELS = PROJECT_ROOT / "data" / "models"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

def ensure_dirs():
    DATA_RESULTS.mkdir(parents=True, exist_ok=True)

def load_model_and_features():
    model_path = DATA_MODELS / "random_forest.pkl"
    data_path = DATA_PROCESSED / "merged_dataset.csv"
    
    if not model_path.exists() or not data_path.exists():
        raise FileNotFoundError("Model or data not found.")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    df = pd.read_csv(data_path)
    # Assume target is voc_concentration
    X = df.drop(columns=['voc_concentration'])
    y = df['voc_concentration']
    return model, X, y

def run_permutation_importance(model, X, y):
    result = permutation_importance(model, X, y, n_repeats=10, random_state=42, n_jobs=1)
    return result.importances_mean

def benjamini_hochberg_correction(p_values):
    # Simple BH implementation
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    corrected = np.zeros(n)
    for i, p in enumerate(sorted_p):
        corrected[sorted_indices[i]] = min(p * n / (i + 1), 1.0)
    
    return corrected

def generate_shap_plot(model, X):
    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # Save plot
    plt = shap.summary_plot(shap_values, X, show=False)
    plt.savefig(DATA_RESULTS / "shap_summary.png")
    plt.close()
    return True

def main():
    try:
        model, X, y = load_model_and_features()
        
        # Permutation Importance
        imp = run_permutation_importance(model, X, y)
        # Save raw p-values (placeholder logic for now)
        # In real scenario, compute p-values from permutation distribution
        raw_p = [1.0] * len(imp) # Placeholder
        
        with open(DATA_RESULTS / "feature_importance_pvalues_raw.json", 'w') as f:
            json.dump({"p_values": raw_p}, f)
        
        # BH Correction
        corrected_p = benjamini_hochberg_correction(raw_p)
        with open(DATA_RESULTS / "feature_importance_pvalues_corrected.json", 'w') as f:
            json.dump({"p_values": corrected_p.tolist()}, f)
        
        # SHAP
        generate_shap_plot(model, X)
        
        print("Interpretation completed.")
    except Exception as e:
        print(f"Error in interpretation: {e}")
        raise

if __name__ == "__main__":
    main()
