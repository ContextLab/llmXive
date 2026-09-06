"""
Analysis module for Glass Forming Region prediction.
Handles collinearity checks, feature importance, sensitivity analysis,
and the T029b fallback logic.
"""
import os
import sys
import json
import pickle
import logging
import shutil
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import scipy.stats as stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DATA_PATH = "data/processed/processed_alloys.csv"
MODELS_DIR = "data/models"
BASELINE_MODEL = "random_forest_model.pkl"
STABLE_MODEL = "random_forest_model_stable.pkl"
COLLINEARITY_REPORT = "collinearity_report.json"
COLLINEARITY_DECISION = "collinearity_decision.json"
CV_METRICS_STABLE = "cv_metrics_stable.json"

def load_model_and_data(model_path: str, data_path: str) -> Tuple[Any, pd.DataFrame]:
    """Load a pickled model and a CSV dataset."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    df = pd.read_csv(data_path)
    return model, df

def check_collinearity(df: pd.DataFrame, threshold: float = 0.8) -> Dict[str, Any]:
    """
    Compute Pearson correlation matrix and flag high correlations.
    Returns a report dictionary.
    """
    feature_cols = [col for col in df.columns if col not in ['composition', 'critical_cooling_rate', 'is_ternary']]
    if not feature_cols:
        logger.warning("No numeric feature columns found for collinearity check.")
        return {"collinear_pairs": [], "max_correlation": 0.0, "flags": []}
    
    corr_matrix = df[feature_cols].corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    collinear_pairs = []
    max_corr = 0.0
    
    for col in upper.columns:
        for row in upper.index:
            if pd.notna(upper[col][row]):
                val = upper[col][row]
                if val > threshold:
                    collinear_pairs.append({"feature1": col, "feature2": row, "correlation": val})
                    if val > max_corr:
                        max_corr = val
    
    report = {
        "collinear_pairs": collinear_pairs,
        "max_correlation": float(max_corr),
        "flags": [f"{p['feature1']} vs {p['feature2']} (r={p['correlation']:.3f})" for p in collinear_pairs]
    }
    
    logger.info(f"Collinearity check completed. Found {len(collinear_pairs)} pairs with |r| > {threshold}.")
    return report

def analyze_feature_importance(model: Any, feature_names: List[str]) -> List[Dict[str, Any]]:
    """Calculate mean absolute SHAP values (approximated by feature importances for RF)."""
    # For RF, we use feature_importances_ as a proxy for SHAP in this context
    # to identify the 'least important' feature for dropping.
    importances = model.feature_importances_
    result = []
    for name, imp in zip(feature_names, importances):
        result.append({"feature": name, "importance": float(imp)})
    return sorted(result, key=lambda x: x['importance'], reverse=True)

def retrain_stable_model(df: pd.DataFrame, dropped_feature: str, random_state: int = 42) -> RandomForestRegressor:
    """
    Retrain a Random Forest model excluding the specified feature.
    """
    feature_cols = [col for col in df.columns if col not in ['composition', 'critical_cooling_rate', 'is_ternary', dropped_feature]]
    if not feature_cols:
        raise ValueError(f"No features left after dropping {dropped_feature}.")
    
    X = df[feature_cols]
    y = df['critical_cooling_rate']
    
    model = RandomForestRegressor(random_state=random_state, n_estimators=100)
    model.fit(X, y)
    logger.info(f"Retrained stable model with features excluding: {dropped_feature}")
    return model

def run_collinearity_and_retrain(df: pd.DataFrame, baseline_model_path: str, stable_model_path: str) -> Dict[str, Any]:
    """
    Main logic for T029a: Check collinearity and retrain if necessary.
    """
    report = check_collinearity(df)
    
    # Save collinearity report
    report_path = os.path.join(MODELS_DIR, COLLINEARITY_REPORT)
    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    decision = {"retrain_required": False, "dropped_feature": None}
    
    if report['collinear_pairs']:
        # Identify the feature with lowest importance among collinear pairs
        # We need the current model's importances
        with open(baseline_model_path, 'rb') as f:
            baseline_model = pickle.load(f)
        
        feature_names = [col for col in df.columns if col not in ['composition', 'critical_cooling_rate', 'is_ternary']]
        importances = analyze_feature_importance(baseline_model, feature_names)
        
        # Map feature name to importance
        imp_map = {item['feature']: item['importance'] for item in importances}
        
        # Find lowest importance in collinear pairs
        lowest_imp_feature = None
        min_imp = float('inf')
        
        for pair in report['collinear_pairs']:
            f1, f2 = pair['feature1'], pair['feature2']
            if f1 in imp_map and imp_map[f1] < min_imp:
                min_imp = imp_map[f1]
                lowest_imp_feature = f1
            if f2 in imp_map and imp_map[f2] < min_imp:
                min_imp = imp_map[f2]
                lowest_imp_feature = f2
        
        if lowest_imp_feature:
            logger.info(f"Collinearity detected. Dropping feature: {lowest_imp_feature} (lowest importance).")
            stable_model = retrain_stable_model(df, lowest_imp_feature)
            
            # Save stable model
            with open(stable_model_path, 'wb') as f:
                pickle.dump(stable_model, f)
            
            decision = {"retrain_required": True, "dropped_feature": lowest_imp_feature}
            
            # Save CV metrics for stable model (simplified)
            # In a real scenario, we'd run CV here. For now, we note it.
            cv_metrics_stable_path = os.path.join(MODELS_DIR, CV_METRICS_STABLE)
            with open(cv_metrics_stable_path, 'w') as f:
                json.dump({"note": "Stable model retrained, CV to be run in next step or T021 equivalent"}, f)
        else:
            logger.warning("Could not identify a feature to drop based on importance.")
            decision = {"retrain_required": False, "dropped_feature": None}
    else:
        logger.info("No significant collinearity found. Using baseline model as stable model.")
        # Copy baseline to stable
        shutil.copy2(baseline_model_path, stable_model_path)
        decision = {"retrain_required": False, "dropped_feature": None}
    
    # Save decision
    decision_path = os.path.join(MODELS_DIR, COLLINEARITY_DECISION)
    with open(decision_path, 'w') as f:
        json.dump(decision, f, indent=2)
    
    return decision

def run_analysis():
    """
    Orchestrates the full analysis pipeline including T029a logic.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    baseline_model_path = os.path.join(MODELS_DIR, BASELINE_MODEL)
    stable_model_path = os.path.join(MODELS_DIR, STABLE_MODEL)
    
    # Check if baseline model exists
    if not os.path.exists(baseline_model_path):
        logger.error(f"Baseline model not found at {baseline_model_path}.")
        return 1
    
    # Check if data exists
    if not os.path.exists(DATA_PATH):
        logger.error(f"Processed data not found at {DATA_PATH}.")
        return 1
    
    df = pd.read_csv(DATA_PATH)
    
    # Run T029a logic
    try:
        run_collinearity_and_retrain(df, baseline_model_path, stable_model_path)
    except Exception as e:
        logger.error(f"Error during collinearity check/retrain: {e}")
        # If T029a fails, we rely on T029b fallback logic below
    
    # Ensure stable model exists (T029b Fallback Logic)
    if not os.path.exists(stable_model_path):
        logger.warning(f"Stable model not found after T029a. Falling back to baseline model.")
        shutil.copy2(baseline_model_path, stable_model_path)
        logger.info(f"Copied {BASELINE_MODEL} to {STABLE_MODEL}.")
    
    logger.info("Analysis pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(run_analysis())
