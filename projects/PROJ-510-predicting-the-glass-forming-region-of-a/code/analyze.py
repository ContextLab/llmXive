import logging
import sys
import os
import json
from typing import Dict, List, Any
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
import joblib

from utils import get_logger, ensure_dir

logger = get_logger(__name__)

def load_model_and_data(model_path: str, data_path: str) -> tuple:
    """Load trained model and data."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data not found: {data_path}")
    
    model = joblib.load(model_path)
    df = pd.read_csv(data_path)
    return model, df

def analyze_feature_importance(model, X, y, n_permutations=1000, random_state=42) -> Dict[str, Any]:
    """Calculate permutation importance."""
    result = permutation_importance(model, X, y, n_repeats=n_permutations, random_state=random_state, n_jobs=-1)
    
    importance = result.importances_mean
    std = result.importances_std
    
    # P-value calculation against shuffled baseline
    # We assume mean importance > 0 is significant if it's far from 0
    # For simplicity, we flag features with mean_importance > 2*std as significant
    features = list(X.columns)
    ranked = []
    for i, feat in enumerate(features):
        p_val = 1.0
        if importance[i] > 0:
            # Simple z-score approximation for p-value
            # p = P(Z > z)
            # We'll just flag if mean > 2*std
            is_significant = importance[i] > 2 * std[i]
            ranked.append({
                'feature': feat,
                'importance': float(importance[i]),
                'std': float(std[i]),
                'significant': is_significant
            })
    
    ranked.sort(key=lambda x: x['importance'], reverse=True)
    return ranked

def run_sensitivity_analysis(model, df, thresholds: List[float]) -> Dict[str, Any]:
    """
    Run sensitivity analysis on classification thresholds.
    Binarizes target and calculates F1 score.
    """
    feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    X = df[feature_cols]
    y = df['critical_cooling_rate']
    
    results = {
        'threshold_values': thresholds,
        'f1_scores': []
    }
    
    for thresh in thresholds:
        y_binary = (y > thresh).astype(int)
        y_pred_cont = model.predict(X)
        y_pred_binary = (y_pred_cont > thresh).astype(int)
        
        # Calculate F1
        tp = ((y_binary == 1) & (y_pred_binary == 1)).sum()
        fp = ((y_binary == 0) & (y_pred_binary == 1)).sum()
        fn = ((y_binary == 1) & (y_pred_binary == 0)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        results['f1_scores'].append(float(f1))
    
    return results

def run_analysis(model_path: str = "data/models/random_forest_model.pkl",
                 data_path: str = "data/processed/processed_alloys.csv",
                 output_path: str = "data/processed/sensitivity_report.json") -> None:
    """
    Main entry point for analysis.
    """
    ensure_dir(os.path.dirname(output_path))
    
    model, df = load_model_and_data(model_path, data_path)
    
    feature_cols = ['mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    X = df[feature_cols]
    y = df['critical_cooling_rate']
    
    # Feature Importance
    importance_report = analyze_feature_importance(model, X, y)
    
    # Sensitivity Analysis
    thresholds = [50, 100, 150]
    sensitivity_report = run_sensitivity_analysis(model, df, thresholds)
    
    # Combine reports
    full_report = {
        'feature_importance': importance_report,
        'sensitivity': sensitivity_report
    }
    
    with open(output_path, 'w') as f:
        json.dump(full_report, f, indent=2)
    
    logger.info(f"Analysis report saved to {output_path}")

if __name__ == "__main__":
    run_analysis()
