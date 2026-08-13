import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import shap
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/shap_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "step4_final.csv"
MODEL_PATH = PROJECT_ROOT / "data" / "models" / "best_model.pkl"
OUTPUT_DIR_SHAP = PROJECT_ROOT / "data" / "artifacts"
OUTPUT_DIR_RESULTS = PROJECT_ROOT / "data" / "results"
SHAP_SUMMARY_PNG = OUTPUT_DIR_SHAP / "shap_summary.png"
FEATURE_RANKING_CSV = OUTPUT_DIR_RESULTS / "feature_ranking.csv"
STABILITY_METRICS_JSON = OUTPUT_DIR_RESULTS / "stability_metrics.json"

def ensure_output_dirs():
    OUTPUT_DIR_SHAP.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR_RESULTS.mkdir(parents=True, exist_ok=True)

def load_processed_data():
    """Load the cleaned and processed dataset."""
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(f"Processed data not found at {PROCESSED_DATA_PATH}. "
                                "Run ingestion pipeline first.")
    df = pd.read_csv(PROCESSED_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows from {PROCESSED_DATA_PATH}")
    return df

def load_or_train_model():
    """Load the best model from disk or train a new one if missing."""
    if MODEL_PATH.exists():
        logger.info(f"Loading model from {MODEL_PATH}")
        model = joblib.load(MODEL_PATH)
    else:
        logger.warning(f"Model not found at {MODEL_PATH}. Training a new Random Forest model.")
        df = load_processed_data()
        # Define features and target
        exclude_cols = ['composition', 'weibull_modulus', 'sample_count', 'is_range_flag', 
                        'range_original', 'primary_anion_cation_group', 'is_imputed', 'sintering_temp']
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        
        X = df[feature_cols].fillna(0)
        y = df['weibull_modulus']
        
        # Train a simple RF as fallback
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X, y)
        joblib.dump(model, MODEL_PATH)
        logger.info(f"Saved fallback model to {MODEL_PATH}")
    return model

def generate_shap_analysis(model, X, y):
    """Generate SHAP values using KernelExplainer for tree-based models."""
    logger.info("Computing SHAP values...")
    # Use a background sample for KernelExplainer to reduce computation
    background = shap.kmeans(X, 10)
    explainer = shap.KernelExplainer(model.predict, background)
    shap_values = explainer.shap_values(X, nsamples=100) # nsamples limits computation time
    return shap_values

def plot_shap_summary(shap_values, feature_names, output_path):
    """Generate and save the SHAP summary plot."""
    logger.info(f"Generating SHAP summary plot: {output_path}")
    plt.figure(figsize=(10, 8))
    # shap.summary_plot handles both array and list of arrays
    shap.summary_plot(shap_values, features=None, feature_names=feature_names, 
                      show=False, plot_type="dot", color_bar=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved SHAP summary plot to {output_path}")

def save_feature_ranking(shap_values, feature_names, output_path):
    """Calculate mean absolute SHAP values and save ranking."""
    logger.info(f"Saving feature ranking to {output_path}")
    # Handle case where shap_values might be a list (for multi-output) or array
    if isinstance(shap_values, list):
        # Take the first output if multi-output, or average if needed
        # For regression, shap_values is usually an array
        abs_shap = np.abs(shap_values[0]) if len(shap_values) > 0 else np.abs(shap_values)
    else:
        abs_shap = np.abs(shap_values)
    
    mean_abs_shap = np.mean(abs_shap, axis=0)
    
    ranking_df = pd.DataFrame({
        'feature': feature_names,
        'mean_abs_shap': mean_abs_shap
    }).sort_values(by='mean_abs_shap', ascending=False)
    
    ranking_df.to_csv(output_path, index=False)
    logger.info(f"Feature ranking saved. Top feature: {ranking_df.iloc[0]['feature']}")

def calculate_cv_stability(model, X, y, feature_names, n_folds=5, output_path=None):
    """Calculate feature importance stability across CV folds."""
    logger.info("Calculating CV stability metrics...")
    importance_scores = []
    
    # Use cross_val_predict to get predictions, but we need feature importance per fold
    # We will manually split and train
    from sklearn.model_selection import KFold
    kfold = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    fold_importances = []
    for train_idx, test_idx in kfold.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train a model on the fold
        fold_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        fold_model.fit(X_train, y_train)
        
        # Get feature importance
        imp = fold_model.feature_importances_
        fold_importances.append(imp)
    
    fold_importances = np.array(fold_importances)
    
    # Calculate Mean and Std Dev for each feature
    mean_imp = np.mean(fold_importances, axis=0)
    std_imp = np.std(fold_importances, axis=0)
    
    # Coefficient of Variation (CV) = Std / Mean
    # Avoid division by zero
    cv_scores = np.divide(std_imp, mean_imp, out=np.zeros_like(std_imp), where=mean_imp!=0)
    
    stability_df = pd.DataFrame({
        'feature': feature_names,
        'mean_importance': mean_imp,
        'std_importance': std_imp,
        'cv_score': cv_scores
    }).sort_values(by='cv_score') # Lower CV is more stable
    
    metrics = {
        'n_folds': n_folds,
        'feature_stability': stability_df.to_dict(orient='records'),
        'overall_cv_mean': float(np.mean(cv_scores)),
        'overall_cv_std': float(np.std(cv_scores))
    }
    
    if output_path:
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Stability metrics saved to {output_path}")
    
    return metrics

def main():
    """Main entry point for SHAP analysis and artifact generation."""
    logger.info("Starting SHAP Analysis Pipeline")
    ensure_output_dirs()
    
    try:
        # 1. Load Data
        df = load_processed_data()
        
        # Identify features (exclude metadata columns)
        exclude_cols = ['composition', 'weibull_modulus', 'sample_count', 'is_range_flag', 
                        'range_original', 'primary_anion_cation_group', 'is_imputed', 'sintering_temp']
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        
        if not feature_cols:
            raise ValueError("No feature columns found in processed data.")
        
        X = df[feature_cols].fillna(0)
        y = df['weibull_modulus']
        
        # 2. Load Model
        model = load_or_train_model()
        
        # 3. Generate SHAP Values
        # Note: For tree models, TreeExplainer is faster, but KernelExplainer is model-agnostic.
        # We use TreeExplainer here for efficiency if the model is tree-based.
        if isinstance(model, (RandomForestRegressor,)) or hasattr(model, 'tree_'):
            logger.info("Using TreeExplainer for efficiency.")
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
        else:
            logger.info("Using KernelExplainer.")
            shap_values = generate_shap_analysis(model, X, y)
        
        # 4. Generate Plots and Rankings
        plot_shap_summary(shap_values, feature_cols, str(SHAP_SUMMARY_PNG))
        save_feature_ranking(shap_values, feature_cols, str(FEATURE_RANKING_CSV))
        
        # 5. Calculate Stability
        stability_metrics = calculate_cv_stability(model, X, y, feature_cols, output_path=str(STABILITY_METRICS_JSON))
        
        logger.info("SHAP Analysis Pipeline completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())