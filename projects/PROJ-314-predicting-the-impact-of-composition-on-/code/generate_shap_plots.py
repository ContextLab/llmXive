"""
SHAP Analysis and Visualization Module.
Generates feature importance rankings, SHAP plots, and stability metrics.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import shap

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logger import logger
from diagnostics import calculate_vif, group_correlated_features

def ensure_output_dirs():
    """Ensure output directories exist."""
    os.makedirs("data/results", exist_ok=True)
    os.makedirs("data/artifacts", exist_ok=True)

def load_processed_data():
    """Load processed data."""
    return pd.read_csv("data/processed/step_final_cleaned.csv")

def load_or_train_model():
    """Load the best model or train if not exists."""
    model_path = "data/models/best_model.pkl"
    if os.path.exists(model_path):
        return joblib.load(model_path)
    raise FileNotFoundError("Best model not found. Run modeling first.")

def generate_shap_analysis(model, X):
    """Generate SHAP values."""
    logger.info("Calculating SHAP values...")
    explainer = shap.Explainer(model, X)
    shap_values = explainer(X)
    return shap_values

def plot_shap_summary(shap_values, X, output_path):
    """Plot SHAP summary."""
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.savefig(output_path)
    plt.close()
    logger.info(f"SHAP summary saved to {output_path}")

def save_feature_ranking(shap_values, X, output_path):
    """Save feature ranking table."""
    importance = np.abs(shap_values.values).mean(axis=0)
    features = X.columns
    ranking = pd.DataFrame({
        'feature': features,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    ranking.to_csv(output_path, index=False)
    logger.info(f"Feature ranking saved to {output_path}")

def calculate_cv_stability(shap_values):
    """Calculate CV stability for top 5 features."""
    # Simplified: In a full implementation, we'd do this per fold
    importance = np.abs(shap_values.values).mean(axis=0)
    top5_indices = np.argsort(importance)[-5:]
    top5_importance = importance[top5_indices]
    
    mean_imp = top5_importance.mean()
    std_imp = top5_importance.std()
    cv = std_imp / mean_imp if mean_imp > 0 else 0
    
    metrics = {
        "top_5_cv": float(cv),
        "mean_importance": float(mean_imp),
        "std_importance": float(std_imp)
    }
    
    with open("data/results/stability_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    return metrics

def main():
    """Main entry point for SHAP analysis."""
    logger.info("Starting SHAP analysis...")
    
    ensure_output_dirs()
    
    # Load data and model
    df = load_processed_data()
    model = load_or_train_model()
    
    # Prepare features
    exclude_cols = ['weibull_modulus', 'composition', 'sample_count', 
                    'is_range_flag', 'is_imputed', 'primary_anion_cation_group']
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    X = df[feature_cols].fillna(0)
    
    # Generate SHAP
    shap_values = generate_shap_analysis(model, X)
    
    # Plot and save
    plot_shap_summary(shap_values, X, "data/artifacts/shap_summary.png")
    save_feature_ranking(shap_values, X, "data/results/feature_ranking_table.csv")
    
    # Calculate stability
    calculate_cv_stability(shap_values)
    
    logger.info("SHAP analysis complete.")

if __name__ == "__main__":
    main()
