"""
Analysis Module.

Handles collinearity detection, feature importance, and sensitivity analysis.
"""
import os
import sys
import json
import pickle
import logging
import shutil
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from scipy.stats import ttest_1samp
from utils import get_logger, ensure_dir

logger = get_logger(__name__)

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
DATA_MODELS_DIR = os.path.join(PROJECT_ROOT, 'data', 'models')
DATA_LOGS_DIR = os.path.join(PROJECT_ROOT, 'data', 'logs')

ensure_dir(DATA_PROCESSED_DIR)
ensure_dir(DATA_MODELS_DIR)
ensure_dir(DATA_LOGS_DIR)

INPUT_PATH = os.path.join(DATA_PROCESSED_DIR, 'processed_alloys.csv')
TEST_SET_PATH = os.path.join(DATA_PROCESSED_DIR, 'test_set.csv')
TEST_TARGET_PATH = os.path.join(DATA_PROCESSED_DIR, 'test_target.csv')
STABLE_MODEL_PATH = os.path.join(DATA_MODELS_DIR, 'random_forest_model_stable.pkl')
MODEL_PATH = os.path.join(DATA_MODELS_DIR, 'random_forest_model.pkl')

FEATURE_IMPORTANCE_PATH = os.path.join(DATA_MODELS_DIR, 'feature_importance.json')
COLLINEARITY_REPORT_PATH = os.path.join(DATA_MODELS_DIR, 'collinearity_report.json')
INITIAL_METRICS_PATH = os.path.join(DATA_MODELS_DIR, 'initial_model_metrics.json')
DROP_CANDIDATE_PATH = os.path.join(DATA_MODELS_DIR, 'drop_candidate.json')
COLLINEARITY_DECISION_PATH = os.path.join(DATA_MODELS_DIR, 'collinearity_decision.json')
SENSITIVITY_REPORT_PATH = os.path.join(DATA_MODELS_DIR, 'sensitivity_report.csv')
SENSITIVITY_STATUS_PATH = os.path.join(DATA_MODELS_DIR, 'sensitivity_status.json')
BEST_AVAILABLE_PATH = os.path.join(DATA_MODELS_DIR, 'random_forest_model_best_available.pkl')

RANDOM_STATE = 42
CORE_FEATURES = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']

def load_model_and_data(model_path: str, data_path: str):
    """Load model and data."""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    df = pd.read_csv(data_path)
    return model, df

def check_collinearity(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
    """Check for collinearity among features."""
    X = df[feature_cols]
    corr_matrix = X.corr().abs()
    
    collinear_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            if corr_matrix.iloc[i, j] > 0.8:
                collinear_pairs.append({
                    "feature1": corr_matrix.columns[i],
                    "feature2": corr_matrix.columns[j],
                    "correlation": float(corr_matrix.iloc[i, j])
                })
    
    with open(COLLINEARITY_REPORT_PATH, 'w') as f:
        json.dump(collinear_pairs, f, indent=2)
    
    return {"collinear_pairs": collinear_pairs}

def analyze_feature_importance(model: RandomForestRegressor, X: pd.DataFrame, y: pd.Series) -> List[Dict]:
    """Compute permutation importance and p-values."""
    result = permutation_importance(model, X, y, n_repeats=1000, random_state=RANDOM_STATE, n_jobs=-1)
    
    importance_scores = result.importances_mean
    p_values = []
    
    for i, r in enumerate(result.importances):
        # One-sample t-test against 0
        t_stat, p_val = ttest_1samp(r, 0)
        p_values.append(float(p_val))
    
    features = X.columns.tolist()
    importance_data = []
    
    for i, feat in enumerate(features):
        importance_data.append({
            "feature": feat,
            "importance_score": float(importance_scores[i]),
            "p_value": float(p_values[i])
        })
    
    # Sort by importance
    importance_data.sort(key=lambda x: x['importance_score'], reverse=True)
    
    with open(FEATURE_IMPORTANCE_PATH, 'w') as f:
        json.dump(importance_data, f, indent=2)
    
    return importance_data

def retrain_stable_model(df: pd.DataFrame, drop_feature: str) -> RandomForestRegressor:
    """Retrain model excluding a feature."""
    feature_cols = [f for f in df.columns if f in CORE_FEATURES and f != drop_feature]
    if not feature_cols:
        raise ValueError("Cannot drop all core features.")
    
    X = df[feature_cols]
    y = df['critical_cooling_rate']
    
    model = RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)
    model.fit(X, y)
    return model, feature_cols

def run_collinearity_and_retrain(df: pd.DataFrame) -> Tuple[RandomForestRegressor, List[str]]:
    """Run collinearity check and retrain if needed."""
    feature_cols = CORE_FEATURES
    
    # Check collinearity
    collinearity_info = check_collinearity(df, feature_cols)
    
    if not collinearity_info['collinear_pairs']:
        logger.info("No collinearity detected.")
        with open(COLLINEARITY_DECISION_PATH, 'w') as f:
            json.dump({"retrain_required": False, "dropped_feature": None, "status": "stable"}, f, indent=2)
        model = RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)
        model.fit(df[feature_cols], df['critical_cooling_rate'])
        return model, feature_cols
    
    # Identify drop candidate
    # Compute SHAP (simplified as feature importance here)
    X = df[feature_cols]
    y = df['critical_cooling_rate']
    initial_model = RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)
    initial_model.fit(X, y)
    
    # Save initial metrics
    from sklearn.metrics import mean_squared_error
    y_pred = initial_model.predict(X)
    rmse = mean_squared_error(y, y_pred, squared=False)
    with open(INITIAL_METRICS_PATH, 'w') as f:
        json.dump({"initial_rmse": float(rmse)}, f, indent=2)
    
    # Find least important among collinear
    # Simplified: use feature importances from the model
    importances = initial_model.feature_importances_
    imp_dict = dict(zip(feature_cols, importances))
    
    # Find collinear features
    collinear_feats = set()
    for pair in collinearity_info['collinear_pairs']:
        collinear_feats.add(pair['feature1'])
        collinear_feats.add(pair['feature2'])
    
    # Find min importance among collinear
    min_feat = None
    min_val = float('inf')
    for f in collinear_feats:
        if imp_dict[f] < min_val:
            min_val = imp_dict[f]
            min_feat = f
    
    # Check if core
    if min_feat in CORE_FEATURES:
        logger.warning("Core descriptors are collinear. Proceeding with best available model.")
        with open(COLLINEARITY_DECISION_PATH, 'w') as f:
            json.dump({"retrain_required": False, "dropped_feature": None, "status": "best_available"}, f, indent=2)
        return initial_model, feature_cols
    
    # Drop and retrain
    logger.info(f"Dropping feature: {min_feat}")
    new_model, new_cols = retrain_stable_model(df, min_feat)
    
    with open(COLLINEARITY_DECISION_PATH, 'w') as f:
        json.dump({"retrain_required": True, "dropped_feature": min_feat, "status": "stable"}, f, indent=2)
    
    return new_model, new_cols

def run_sensitivity_analysis(model: RandomForestRegressor, feature_cols: List[str]) -> None:
    """Run threshold-sweep sensitivity analysis."""
    # Load test data
    test_df = pd.read_csv(TEST_SET_PATH)
    test_y = pd.read_csv(TEST_TARGET_PATH)
    
    # Ensure feature columns match
    X_test = test_df[feature_cols]
    y_test = test_y['critical_cooling_rate']
    
    thresholds = [50, 100, 150]
    results = []
    
    rmse_values = []
    f1_values = []
    
    for T in thresholds:
        # Continuous RMSE (filtered subset)
        mask = y_test >= T
        if mask.sum() == 0:
            rmse_cont = float('nan')
        else:
            y_pred = model.predict(X_test[mask])
            y_true = y_test[mask]
            rmse_cont = mean_squared_error(y_true, y_pred, squared=False)
        
        rmse_values.append(rmse_cont)
        
        # Binarize
        y_bin = (y_test >= T).astype(int)
        y_pred_cont = model.predict(X_test)
        y_pred_bin = (y_pred_cont >= T).astype(int)
        
        # F1 Score
        from sklearn.metrics import f1_score
        try:
            f1 = f1_score(y_bin, y_pred_bin)
        except Exception:
            f1 = 0.0
        
        f1_values.append(f1)
        
        results.append({
            "threshold": T,
            "rmse_continuous": rmse_cont,
            "f1_score": f1
        })
    
    # Stability Check
    rmse_arr = np.array([r for r in rmse_values if not np.isnan(r)])
    f1_arr = np.array(f1_values)
    
    if len(rmse_arr) > 1:
        rmse_var = np.var(rmse_arr)
        rmse_mean = np.mean(rmse_arr)
        f1_var = np.var(f1_arr)
        f1_mean = np.mean(f1_arr)
        
        stability_met = (rmse_var < 0.05 * rmse_mean) and (f1_var < 0.05 * f1_mean)
    else:
        rmse_var = 0.0
        f1_var = 0.0
        stability_met = False
    
    # Write CSV
    df_res = pd.DataFrame(results)
    df_res['rmse_variance'] = rmse_var
    df_res['f1_variance'] = f1_var
    df_res['stability_status'] = 'PASS' if stability_met else 'FAIL'
    df_res.to_csv(SENSITIVITY_REPORT_PATH, index=False)
    
    # Write Status
    status = {
        "stability_met": stability_met,
        "rmse_variance": float(rmse_var),
        "f1_variance": float(f1_var),
        "threshold_values": thresholds,
        "run_status": "PASSED" if stability_met else "FAILED"
    }
    
    with open(SENSITIVITY_STATUS_PATH, 'w') as f:
        json.dump(status, f, indent=2)
    
    if not stability_met:
        logger.warning("SC-003 failed: Sensitivity margin exceeds 5% of mean.")

def run_analysis() -> None:
    """Main entry point for analysis pipeline."""
    logger.info("Starting analysis pipeline.")
    
    # Load processed data
    df = pd.read_csv(INPUT_PATH)
    
    # Run collinearity and retrain
    model, feature_cols = run_collinearity_and_retrain(df)
    
    # Save model
    with open(STABLE_MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    # If best available, copy
    if not os.path.exists(STABLE_MODEL_PATH) and os.path.exists(MODEL_PATH):
        shutil.copy(MODEL_PATH, STABLE_MODEL_PATH)
    
    # Feature Importance
    X = df[feature_cols]
    y = df['critical_cooling_rate']
    analyze_feature_importance(model, X, y)
    
    # Sensitivity
    run_sensitivity_analysis(model, feature_cols)
    
    logger.info("Analysis pipeline completed.")

if __name__ == "__main__":
    run_analysis()
