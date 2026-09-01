"""
Analysis module for the Glass Forming Region prediction pipeline.
Handles model analysis, collinearity detection, feature importance, and sensitivity analysis.
"""
import logging
import sys
import os
import json
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import f1_score
from scipy.stats import pearsonr
import shap

# Constants
DATA_PATH = "data/processed/processed_alloys.csv"
MODEL_PATH = "data/models/random_forest_model.pkl"
STABLE_MODEL_PATH = "data/models/random_forest_model_stable.pkl"
CV_METRICS_PATH = "data/models/cv_metrics.json"
CV_METRICS_STABLE_PATH = "data/models/cv_metrics_stable.json"
COLLINEARITY_REPORT_PATH = "data/models/collinearity_report.json"
COLLINEARITY_DECISION_PATH = "data/models/collinearity_decision.json"
CORRELATION_THRESHOLD = 0.8
RANDOM_STATE = 42

logger = logging.getLogger(__name__)

def load_model_and_data(model_path: str, data_path: str) -> Tuple[Any, pd.DataFrame]:
    """Load the trained model and processed dataset."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    df = pd.read_csv(data_path)
    return model, df

def check_collinearity(df: pd.DataFrame, threshold: float = CORRELATION_THRESHOLD) -> Dict[str, Any]:
    """
    Compute Pearson correlation matrix of engineered features and flag pairs with |ρ| > threshold.
    Returns a report with flagged pairs and the full correlation matrix.
    """
    # Select only numeric feature columns (exclude target and metadata)
    feature_cols = [col for col in df.columns if col not in ['critical_cooling_rate', 'composition']]
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")

    numeric_df = df[feature_cols].select_dtypes(include=[np.number])
    corr_matrix = numeric_df.corr()
    
    flagged_pairs = []
    features = corr_matrix.columns.tolist()
    
    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            f1, f2 = features[i], features[j]
            corr_val = corr_matrix.loc[f1, f2]
            if abs(corr_val) > threshold:
                flagged_pairs.append({
                    "feature_1": f1,
                    "feature_2": f2,
                    "correlation": float(corr_val)
                })
    
    report = {
        "threshold": threshold,
        "flagged_pairs": flagged_pairs,
        "has_collinearity": len(flagged_pairs) > 0,
        "full_correlation_matrix": corr_matrix.to_dict()
    }
    
    logger.info(f"Collinearity check complete. Found {len(flagged_pairs)} pairs with |ρ| > {threshold}.")
    return report

def analyze_feature_importance(model: Any, df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Compute mean absolute SHAP values for feature importance.
    Returns a dict mapping feature names to their mean absolute SHAP values.
    """
    X = df[feature_cols]
    
    # Use a subset for SHAP if dataset is large to save time
    if len(X) > 1000:
        X_sample = X.sample(n=1000, random_state=RANDOM_STATE)
    else:
        X_sample = X
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    # Handle both regression and classification SHAP outputs
    if isinstance(shap_values, list):
        # For multi-class or complex outputs, take the first class or average
        shap_values = shap_values[0] if len(shap_values) > 0 else shap_values[0]
    
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    importance_dict = {feature_cols[i]: float(mean_abs_shap[i]) for i in range(len(feature_cols))}
    return importance_dict

def retrain_stable_model(
    df: pd.DataFrame, 
    dropped_feature: str, 
    target_col: str = 'critical_cooling_rate'
) -> Tuple[Any, Dict[str, Any]]:
    """
    Retrain a Random Forest model excluding the specified feature.
    Performs 5-fold CV and returns the model and CV metrics.
    """
    feature_cols = [col for col in df.columns if col != target_col and col != 'composition']
    if dropped_feature in feature_cols:
        feature_cols.remove(dropped_feature)
    
    X = df[feature_cols]
    y = df[target_col]
    
    model = RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE)
    
    # 5-fold CV
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_root_mean_squared_error')
    rmse_scores = np.sqrt(-cv_scores)
    
    cv_metrics = {
        "fold_scores": [float(score) for score in rmse_scores],
        "mean_rmse": float(np.mean(rmse_scores)),
        "dropped_feature": dropped_feature
    }
    
    # Train on full data
    model.fit(X, y)
    
    return model, cv_metrics

def run_analysis():
    """
    Main analysis pipeline:
    1. Load model and data.
    2. Check collinearity.
    3. If collinearity exists, retrain stable model; else copy existing.
    4. Save reports and decisions.
    """
    logger.info("Starting Analysis Pipeline")
    
    # Ensure directories exist
    os.makedirs("data/models", exist_ok=True)
    
    # Load data and model
    model, df = load_model_and_data(MODEL_PATH, DATA_PATH)
    
    # Identify feature columns
    feature_cols = [col for col in df.columns if col not in ['critical_cooling_rate', 'composition']]
    
    # Step 1: Check collinearity
    collinearity_report = check_collinearity(df)
    
    # Save collinearity report
    with open(COLLINEARITY_REPORT_PATH, 'w') as f:
        json.dump(collinearity_report, f, indent=2)
    logger.info(f"Saved collinearity report to {COLLINEARITY_REPORT_PATH}")
    
    decision = {}
    
    if collinearity_report["has_collinearity"]:
        logger.info("Collinearity detected. Identifying feature to drop...")
        
        # Compute SHAP importance from initial model
        shap_importance = analyze_feature_importance(model, df, feature_cols)
        
        # Find the feature with lowest mean absolute SHAP among collinear pairs
        collinear_features = set()
        for pair in collinearity_report["flagged_pairs"]:
            collinear_features.add(pair["feature_1"])
            collinear_features.add(pair["feature_2"])
        
        if not collinear_features:
            raise ValueError("Collinearity detected but no features identified in pairs.")
        
        # Find lowest importance feature among collinear ones
        dropped_feature = min(collinear_features, key=lambda x: shap_importance.get(x, float('inf')))
        logger.info(f"Dropping feature with lowest SHAP importance among collinear pairs: {dropped_feature}")
        
        # Retrain stable model
        stable_model, cv_metrics_stable = retrain_stable_model(df, dropped_feature)
        
        # Save stable model
        with open(STABLE_MODEL_PATH, 'wb') as f:
            pickle.dump(stable_model, f)
        logger.info(f"Saved stable model to {STABLE_MODEL_PATH}")
        
        # Save CV metrics
        with open(CV_METRICS_STABLE_PATH, 'w') as f:
            json.dump(cv_metrics_stable, f, indent=2)
        logger.info(f"Saved stable CV metrics to {CV_METRICS_STABLE_PATH}")
        
        decision = {
            "retrain_required": True,
            "dropped_feature": dropped_feature
        }
    else:
        logger.info("No significant collinearity detected. Copying initial model as stable model.")
        
        # Copy initial model
        with open(MODEL_PATH, 'rb') as src:
            model_content = src.read()
        with open(STABLE_MODEL_PATH, 'wb') as dst:
            dst.write(model_content)
        
        # Copy CV metrics
        with open(CV_METRICS_PATH, 'r') as src:
            cv_metrics = json.load(src)
        with open(CV_METRICS_STABLE_PATH, 'w') as dst:
            json.dump(cv_metrics, dst, indent=2)
        
        decision = {
            "retrain_required": False
        }
    
    # Save decision
    with open(COLLINEARITY_DECISION_PATH, 'w') as f:
        json.dump(decision, f, indent=2)
    logger.info(f"Saved collinearity decision to {COLLINEARITY_DECISION_PATH}")
    
    logger.info("Analysis pipeline completed successfully.")
    return decision

def main():
    """Entry point for the analysis script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_analysis()

if __name__ == "__main__":
    main()