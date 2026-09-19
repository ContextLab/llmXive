"""
T037-T044: Evaluation, Permutation Tests, SHAP Analysis.
Implements T050: Chunked data loading for large files (>5MB).
"""
import json
import os
import sys
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import shap

from config import get_project_root, get_max_rows, get_n_permutations, get_random_seed

# --- T050: Chunked Loading Implementation ---
def load_data_chunked(input_path: str, chunksize: int = 1000) -> pd.DataFrame:
    """
    Load data, optionally in chunks if file size > 5MB to reduce memory peak.
    T050 Implementation:
    1. Check file size.
    2. If > 5MB, read in chunks and concatenate.
    3. If <= 5MB, read directly.
    """
    file_path = Path(input_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file {input_path} not found.")
    
    file_size_bytes = file_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if file_size_mb > 5.0:
        print(f"[Evaluate] File size ({file_size_mb:.2f} MB) > 5MB. Loading in chunks of {chunksize}...")
        chunks = []
        for chunk in pd.read_csv(input_path, chunksize=chunksize):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
        print(f"[Evaluate] Loaded {len(df)} rows in chunks.")
    else:
        print(f"[Evaluate] File size ({file_size_mb:.2f} MB) <= 5MB. Loading directly.")
        df = pd.read_csv(input_path)
    
    return df

# --- Helper Functions ---
def load_model(path: str):
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_model(model, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def save_json(data: Dict, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(path: str) -> Dict:
    with open(path, 'r') as f:
        return json.load(f)

def get_interaction_features() -> List[str]:
    return ['cold_work_Mn_content', 'cold_work_Mg_content', 'cold_work_Si_content', 'cold_work_Cu_content']

def get_main_features() -> List[str]:
    return ['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K']

# --- Model Training Helpers ---
def train_additive_model(X_train, y_train):
    """Train Random Forest without interaction terms."""
    model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=get_random_seed())
    model.fit(X_train, y_train)
    return model

def train_interaction_model(X_train, y_train):
    """Train Random Forest with interaction terms."""
    model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=get_random_seed())
    model.fit(X_train, y_train)
    return model

# --- Statistical Analysis ---
def run_permutation_test(interaction_model, X_val, y_val, n_permutations: int):
    """
    T039: Delta-Permutation Test.
    Shuffles interaction terms and compares error to original.
    """
    interaction_terms = get_interaction_features()
    original_y_pred = interaction_model.predict(X_val)
    original_mae = mean_absolute_error(y_val, original_y_pred)
    
    permuted_maes = []
    np.random.seed(get_random_seed())
    
    for i in range(n_permutations):
        X_perm = X_val.copy()
        # Shuffle each interaction term independently
        for term in interaction_terms:
            if term in X_perm.columns:
                X_perm[term] = np.random.permutation(X_perm[term].values)
        
        pred_perm = interaction_model.predict(X_perm)
        mae_perm = mean_absolute_error(y_val, pred_perm)
        permuted_maes.append(mae_perm)
    
    # P-value: proportion of permuted errors >= original error
    p_value = sum(1 for mae in permuted_maes if mae >= original_mae) / n_permutations
    
    return {
        "p_value": p_value,
        "original_mae": original_mae,
        "mean_permuted_mae": np.mean(permuted_maes),
        "method": "delta_permutation_test"
    }

def calculate_permutation_importance(interaction_model, X_val, y_val, n_permutations: int = 100):
    """
    T040: Calculate permutation importance (drop in R2) for interaction terms.
    """
    interaction_terms = get_interaction_features()
    original_score = interaction_model.score(X_val, y_val)
    importance_scores = {}
    
    np.random.seed(get_random_seed())
    
    for term in interaction_terms:
        if term not in X_val.columns:
            continue
        
        X_perm = X_val.copy()
        X_perm[term] = np.random.permutation(X_perm[term].values)
        
        shuffled_score = interaction_model.score(X_perm, y_val)
        drop = original_score - shuffled_score
        importance_scores[term] = drop
    
    return importance_scores

def run_shap_analysis(model, X_data, feature_names: List[str]):
    """
    T041: SHAP Interaction Value analysis.
    """
    # Check for pure aluminum flag
    project_root = get_project_root()
    metrics_path = project_root / "artifacts" / "reports" / "training_metrics.json"
    pure_alum_flag = False
    if metrics_path.exists():
        try:
            metrics = load_json(str(metrics_path))
            pure_alum_flag = metrics.get("pure_aluminum_flag", False)
        except Exception:
            pass

    if pure_alum_flag:
        print("[SHAP] Pure aluminum detected. Skipping SHAP analysis.")
        return {"status": "skipped", "reason": "pure_aluminum_flag"}

    try:
        explainer = shap.TreeExplainer(model, nsamples=1000, random_state=get_random_seed())
        shap_values = explainer.shap_values(X_data)
        
        # Simplified report structure
        report = {
            "status": "success",
            "top_features": [], # Placeholder for logic to rank
            "interaction_terms": []
        }
        
        # Basic feature importance from SHAP (mean abs)
        if isinstance(shap_values, list):
            # For regression, shap_values is usually a single array
             shap_vals = shap_values[0] if len(shap_values) > 0 else shap_values
        else:
            shap_vals = shap_values
        
        mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)
        sorted_idx = np.argsort(mean_abs_shap)[::-1]
        
        for i in sorted_idx:
            if i < len(feature_names):
                report["top_features"].append({
                    "feature": feature_names[i],
                    "mean_abs_shap": float(mean_abs_shap[i])
                })
        
        return report
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Pipeline Orchestration ---
def run_evaluation_pipeline():
    """
    Main orchestration for T037-T044.
    """
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "engineered_features.csv"
    model_path = project_root / "artifacts" / "models" / "kinetic_model.pkl"
    additive_model_path = project_root / "artifacts" / "models" / "additive_model.pkl"
    
    # Load Data (T050)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file {data_path} not found. Run T024 first.")
    
    df = load_data_chunked(str(data_path))
    
    # Prepare features
    main_feats = get_main_features()
    interaction_feats = get_interaction_features()
    all_feats = main_feats + interaction_feats
    target = 'time_to_peak_min'
    
    X = df[all_feats]
    y = df[target]
    
    # Split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=get_random_seed()
    )
    
    # Train Interaction Model (if not exists, though T030 should have done it)
    if not model_path.exists():
        print("[Evaluate] Interaction model not found. Training now.")
        int_model = train_interaction_model(X_train, y_train)
        save_model(int_model, str(model_path))
    else:
        int_model = load_model(str(model_path))
    
    # Train Additive Model (T037)
    X_train_add = X_train[main_feats]
    X_val_add = X_val[main_feats]
    add_model = train_additive_model(X_train_add, y_train)
    save_model(add_model, str(additive_model_path))
    
    # Permutation Test (T039)
    n_perms = get_n_permutations()
    perm_results = run_permutation_test(int_model, X_val, y_val, n_perms)
    
    # Permutation Importance (T040)
    perm_importance = calculate_permutation_importance(int_model, X_val, y_val)
    
    # SHAP Analysis (T041)
    shap_report = run_shap_analysis(int_model, X_val, all_feats)
    
    # Generate Reports
    # T042: Statistical Significance
    stat_sig = {
        "p_value": perm_results["p_value"],
        "method": perm_results["method"],
        "interaction_term_importance": float(np.mean(list(perm_importance.values()))),
        "conclusion": "Interactions are significant" if perm_results["p_value"] < 0.05 else "Interactions not significant"
    }
    save_json(stat_sig, str(project_root / "artifacts" / "reports" / "statistical_significance.json"))
    
    # T043: SHAP Report
    shap_report["pure_aluminum_flag"] = False # Should be set from metrics if needed
    save_json(shap_report, str(project_root / "artifacts" / "reports" / "shap_interaction_report.json"))
    
    # T044: Success Criteria
    # Load training metrics for R2 check
    train_metrics_path = project_root / "artifacts" / "reports" / "training_metrics.json"
    r2_pass = False
    mae_pass = False
    p_value_pass = False
    
    if train_metrics_path.exists():
        train_metrics = load_json(str(train_metrics_path))
        r2_pass = train_metrics.get("test_r2", 0) > 0.6
        mae_pass = train_metrics.get("test_mae", float('inf')) < (train_metrics.get("baseline_mean", 100) * 0.1) # Example threshold logic
    
    p_value_pass = perm_results["p_value"] < 0.05
    
    success_report = {
        "r2_pass": r2_pass,
        "p_value_pass": p_value_pass,
        "mae_pass": mae_pass,
        "overall_status": "PASS" if (r2_pass and p_value_pass and mae_pass) else "FAIL"
    }
    save_json(success_report, str(project_root / "artifacts" / "reports" / "success_criteria_verification.json"))
    
    print("Evaluation pipeline complete.")

def main():
    run_evaluation_pipeline()

if __name__ == "__main__":
    main()