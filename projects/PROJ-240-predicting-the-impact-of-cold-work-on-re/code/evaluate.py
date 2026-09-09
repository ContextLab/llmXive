"""
Evaluation Pipeline (T032-T039).
Implements statistical significance testing, SHAP analysis, and chunked loading (T044).
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
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score
import shap

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_project_root, get_outlier_percentile, get_n_permutations, get_random_seed, get_data_split_ratio

def load_model(path: Path) -> Any:
    """Load a pickled model."""
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_model(model: Any, path: Path):
    """Save a model to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f, protocol=4)

def save_json(data: Dict, path: Path):
    """Save data to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(path: Path) -> Dict:
    """Load data from JSON."""
    with open(path, 'r') as f:
        return json.load(f)

def get_interaction_features() -> List[str]:
    """Return list of interaction feature names."""
    return [
        "cold_work_Mn_interaction",
        "cold_work_Mg_interaction",
        "cold_work_Si_interaction",
        "cold_work_Cu_interaction"
    ]

def load_data_chunked(input_path: Path) -> pd.DataFrame:
    """
    Load data using chunked reading if file size > 5MB (T044).
    """
    file_size_bytes = input_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    print(f"Input file size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 5.0:
        print("File size > 5MB. Using chunked loading (chunksize=1000).")
        chunks = []
        for chunk in pd.read_csv(input_path, chunksize=1000):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
    else:
        print("File size <= 5MB. Loading directly.")
        df = pd.read_csv(input_path)
        
    return df

def train_additive_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """Train the Additive Model (no interactions)."""
    model = RandomForestRegressor(n_estimators=100, random_state=get_random_seed(), n_jobs=-1)
    model.fit(X, y)
    return model

def train_interaction_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """Train the Interaction Model (full features)."""
    model = RandomForestRegressor(n_estimators=100, random_state=get_random_seed(), n_jobs=-1)
    model.fit(X, y)
    return model

def run_permutation_test(interaction_model: RandomForestRegressor, 
                         X_val: pd.DataFrame, 
                         y_val: pd.Series,
                         n_permutations: int = 1000) -> Dict:
    """
    Run Permutation Test on interaction terms (T034).
    Shuffles interaction terms while holding main effects constant.
    """
    interaction_features = get_interaction_features()
    if not all(f in X_val.columns for f in interaction_features):
        raise ValueError("Interaction features missing from validation set.")

    # Original Error
    original_pred = interaction_model.predict(X_val)
    original_mae = mean_absolute_error(y_val, original_pred)

    permuted_maes = []
    
    # Permutation Logic
    for i in range(n_permutations):
        X_perm = X_val.copy()
        for feat in interaction_features:
            # Shuffle this feature column
            X_perm[feat] = np.random.permutation(X_perm[feat].values)
        
        pred = interaction_model.predict(X_perm)
        mae = mean_absolute_error(y_val, pred)
        permuted_maes.append(mae)

    permuted_maes = np.array(permuted_maes)
    
    # Calculate p-value: proportion of permuted errors >= original error
    # (Assuming lower MAE is better. If permuted is worse (higher), it means the feature mattered.)
    # If the model relies on the interaction, shuffling it should increase error.
    # So we count how many permuted MAEs are >= original MAE.
    p_value = np.sum(permuted_maes >= original_mae) / n_permutations

    return {
        "original_mae": float(original_mae),
        "permuted_mae_mean": float(np.mean(permuted_maes)),
        "permuted_mae_std": float(np.std(permuted_maes)),
        "p_value": float(p_value),
        "n_permutations": n_permutations
    }

def calculate_permutation_importance(model: RandomForestRegressor, 
                                     X_test: pd.DataFrame, 
                                     y_test: pd.Series) -> Dict[str, float]:
    """Calculate permutation importance for interaction terms (T035)."""
    interaction_features = get_interaction_features()
    importance = {}
    
    base_score = model.score(X_test, y_test)
    
    for feat in interaction_features:
        if feat not in X_test.columns:
            importance[feat] = 0.0
            continue
        
        X_perm = X_test.copy()
        X_perm[feat] = np.random.permutation(X_perm[feat].values)
        perm_score = model.score(X_perm, y_test)
        
        # Drop in R2
        importance[feat] = float(base_score - perm_score)
        
    return importance

def run_shap_analysis(model: RandomForestRegressor, X: pd.DataFrame) -> Dict:
    """Run SHAP analysis (T036)."""
    interaction_features = get_interaction_features()
    pure_aluminum_flag = False
    
    # Check for pure aluminum (zero variance in composition)
    comp_cols = ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    if all(col in X.columns for col in comp_cols):
        if all(X[col].std() < 1e-9 for col in comp_cols):
            pure_aluminum_flag = True
            print("Warning: Pure aluminum detected. Skipping SHAP interaction analysis for interaction terms.")
    
    if pure_aluminum_flag:
        return {
            "pure_aluminum_flag": True,
            "main_effects_ranking": [],
            "interaction_terms_ranking": [],
            "message": "SHAP analysis skipped due to pure aluminum (zero variance in composition)."
        }

    # Use TreeExplainer
    explainer = shap.TreeExplainer(model, nsamples=1000, random_state=get_random_seed())
    shap_values = explainer.shap_values(X)
    
    # If it's a regressor, shap_values is a 2D array (n_samples, n_features)
    if isinstance(shap_values, list):
        # For some models, it might be a list of arrays, but RF usually returns one array
        shap_values = shap_values[0] if len(shap_values) == 1 else shap_values

    # Calculate mean absolute SHAP values
    mean_shap = np.abs(shap_values).mean(axis=0)
    
    feature_names = X.columns.tolist()
    shap_importance = list(zip(feature_names, mean_shap))
    shap_importance.sort(key=lambda x: x[1], reverse=True)
    
    # Separate main effects and interactions
    main_effects = [item for item in shap_importance if item[0] not in interaction_features]
    interaction_terms = [item for item in shap_importance if item[0] in interaction_features]
    
    return {
        "pure_aluminum_flag": False,
        "main_effects_ranking": [{"feature": f, "importance": float(v)} for f, v in main_effects],
        "interaction_terms_ranking": [{"feature": f, "importance": float(v)} for f, v in interaction_terms]
    }

def run_evaluation_pipeline():
    """Orchestrate the evaluation pipeline (T032-T039)."""
    project_root = get_project_root()
    
    # Paths
    final_dataset_path = project_root / "data" / "processed" / "final_dataset.csv"
    additive_model_path = project_root / "artifacts" / "models" / "additive_model.pkl"
    interaction_model_path = project_root / "artifacts" / "models" / "kinetic_model.pkl"
    baseline_stats_path = project_root / "artifacts" / "reports" / "baseline_stats.json"
    statistical_significance_path = project_root / "artifacts" / "reports" / "statistical_significance.json"
    shap_report_path = project_root / "artifacts" / "reports" / "shap_interaction_report.json"
    training_metrics_path = project_root / "artifacts" / "reports" / "training_metrics.json"

    if not final_dataset_path.exists():
        raise FileNotFoundError(f"Final dataset not found: {final_dataset_path}")
    
    # Load data (T044: Chunked loading)
    df = load_data_chunked(final_dataset_path)
    print(f"Loaded {len(df)} rows for evaluation.")

    # Prepare X and y
    target = 'time_to_peak_min'
    interaction_features = get_interaction_features()
    # Main features: all numeric except target and interaction features
    main_features = [c for c in df.columns if c != target and c not in interaction_features]
    all_features = main_features + interaction_features

    X = df[all_features]
    y = df[target]

    # Detect Pure Aluminum for training metrics (T029)
    comp_cols = ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    pure_aluminum_flag = False
    if all(col in X.columns for col in comp_cols):
        if all(X[col].std() < 1e-9 for col in comp_cols):
            pure_aluminum_flag = True

    # Load Models
    try:
        additive_model = load_model(additive_model_path)
        print("Loaded Additive Model.")
    except FileNotFoundError:
        print("Additive model not found. Training now...")
        # Train additive model
        additive_model = train_additive_model(X[main_features], y)
        save_model(additive_model, additive_model_path)

    try:
        interaction_model = load_model(interaction_model_path)
        print("Loaded Interaction Model.")
    except FileNotFoundError:
        print("Interaction model not found. Training now...")
        interaction_model = train_interaction_model(X, y)
        save_model(interaction_model, interaction_model_path)

    # 1. Permutation Test (T034)
    # Split data for validation (using simple split for test)
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=get_random_seed())
    
    perm_test_results = run_permutation_test(interaction_model, X_val, y_val, n_permutations=1000)
    print(f"Permutation Test P-Value: {perm_test_results['p_value']}")

    # 2. Permutation Importance (T035)
    X_test, y_test = X_val, y_val # Reusing val as test for simplicity in this context
    perm_importance = calculate_permutation_importance(interaction_model, X_test, y_test)
    
    # 3. SHAP Analysis (T036)
    shap_results = run_shap_analysis(interaction_model, X)

    # 4. Statistical Significance Report (T037)
    stat_sig_report = {
        "p_value": perm_test_results["p_value"],
        "test_statistic": perm_test_results["original_mae"],
        "conclusion": "Significant" if perm_test_results["p_value"] < 0.05 else "Not Significant",
        "permutation_importance": perm_importance
    }
    save_json(stat_sig_report, statistical_significance_path)
    print(f"Saved statistical significance report to {statistical_significance_path}")

    # 5. SHAP Report (T038)
    shap_report = {
        "pure_aluminum_flag": shap_results.get("pure_aluminum_flag", pure_aluminum_flag),
        "main_effects_ranking": shap_results.get("main_effects_ranking", []),
        "interaction_terms_ranking": shap_results.get("interaction_terms_ranking", [])
    }
    save_json(shap_report, shap_report_path)
    print(f"Saved SHAP report to {shap_report_path}")

    # 6. Update Training Metrics (T028) if needed (add p-value check)
    if training_metrics_path.exists():
        metrics = load_json(training_metrics_path)
        metrics["permutation_p_value"] = perm_test_results["p_value"]
        save_json(metrics, training_metrics_path)

def main():
    try:
        run_evaluation_pipeline()
    except Exception as e:
        print(f"Error in evaluation pipeline: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()