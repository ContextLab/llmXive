"""
Module: code/models/importance.py

Computes permutation importance for trained glass-forming classifiers and
generates SHAP summary plots.

Outputs:
  - results/permutation_importance.csv
  - results/shap_plots/shap_summary_random_forest.png
  - results/shap_plots/shap_summary_gradient_boosting.png
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

# Ensure matplotlib uses a non-interactive backend for headless environments
import matplotlib
matplotlib.use('Agg')

from sklearn.inspection import permutation_importance

# Import paths relative to project root (code/models)
# We assume the script is run from the project root or added to PYTHONPATH
# The training script saves models to models/trained_models.pkl
MODEL_PATH = Path("models/trained_models.pkl")
DATA_PATH = Path("data/derived/descriptor_vector_vif_filtered.csv")
OUTPUT_CSV = Path("results/permutation_importance.csv")
SHAP_DIR = Path("results/shap_plots")

def setup_logging():
    """Configure logging for this script."""
    log_file = Path("logs/importance_analysis.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_data():
    """Load the filtered descriptor dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}. "
                                "Run descriptor filtering (T025) first.")
    
    df = pd.read_csv(DATA_PATH)
    
    # Identify feature columns (all except 'phase_label' and 'sample_id' if present)
    target_col = 'phase_label'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in {DATA_PATH}")
    
    feature_cols = [c for c in df.columns if c not in [target_col, 'sample_id']]
    if not feature_cols:
        raise ValueError("No feature columns found in dataset.")
    
    X = df[feature_cols].values
    y = df[target_col].values
    feature_names = feature_cols
    
    logging.info(f"Loaded {len(X)} samples with {len(feature_cols)} features.")
    return X, y, feature_names

def load_models():
    """Load trained models from the pickle file."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}. "
                                "Run training script (T020) first.")
    
    models = joblib.load(MODEL_PATH)
    logging.info(f"Loaded models: {list(models.keys())}")
    return models

def compute_permutation_importance(model, X, y, feature_names, n_repeats=10, random_state=42):
    """
    Compute permutation importance and return a DataFrame.
    """
    logging.info("Computing permutation importance...")
    
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        n_jobs=-1
    )
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'mean_importance': result.importances_mean,
        'std_importance': result.importances_std,
        'min_importance': result.importances_min,
        'max_importance': result.importances_max
    })
    
    # Sort by mean importance descending
    importance_df = importance_df.sort_values(by='mean_importance', ascending=False)
    
    return importance_df

def generate_shap_plots(models, X, feature_names):
    """
    Generate SHAP summary plots for each model and save as PNG.
    """
    SHAP_DIR.mkdir(parents=True, exist_ok=True)
    
    for name, model in models.items():
        logging.info(f"Generating SHAP plots for model: {name}")
        
        # Create SHAP explainer
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X)
        
        # Create the plot
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
        
        # Save the plot
        output_path = SHAP_DIR / f"shap_summary_{name}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logging.info(f"Saved SHAP plot to: {output_path}")

def save_results(importance_df):
    """Save permutation importance results to CSV."""
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    importance_df.to_csv(OUTPUT_CSV, index=False)
    logging.info(f"Saved permutation importance to: {OUTPUT_CSV}")

def main():
    """Main entry point for the importance analysis script."""
    setup_logging()
    
    try:
        # Load data and models
        X, y, feature_names = load_data()
        models = load_models()
        
        # Compute permutation importance for each model
        all_importance_dfs = {}
        
        for name, model in models.items():
            imp_df = compute_permutation_importance(model, X, y, feature_names)
            all_importance_dfs[name] = imp_df
            logging.info(f"Top 5 features for {name}:")
            logging.info(imp_df.head())
        
        # Combine results into a single DataFrame with multi-level columns or separate
        # For simplicity, we'll save a combined wide-format CSV
        combined_df = pd.DataFrame()
        for name, imp_df in all_importance_dfs.items():
            # Ensure consistent ordering of features across models
            imp_df = imp_df.set_index('feature')
            imp_df.columns = [f"{name}_{col}" for col in imp_df.columns]
            combined_df = combined_df.join(imp_df, how='outer')
        
        # Reset index to make 'feature' a column
        combined_df = combined_df.reset_index()
        combined_df.rename(columns={'index': 'feature'}, inplace=True)
        
        save_results(combined_df)
        
        # Generate SHAP plots
        generate_shap_plots(models, X, feature_names)
        
        logging.info("Importance analysis completed successfully.")
        
    except Exception as e:
        logging.error(f"Importance analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()