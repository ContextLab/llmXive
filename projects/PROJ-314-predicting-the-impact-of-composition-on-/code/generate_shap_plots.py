"""
T041: Generate SHAP summary plots and feature ranking tables.

This script loads the trained model artifacts (or re-trains if necessary),
computes SHAP values, generates the summary plot, and outputs a feature
ranking table (CSV) and a JSON summary of feature importances.

Outputs:
  - data/results/shap_summary_plot.png
  - data/results/feature_ranking.csv
  - data/results/shap_feature_importance.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import matplotlib
# Use non-interactive backend for headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import shap
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code import logger
from code.config import get_project_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the processed dataset from data/processed/."""
    # Expected path based on T018/T019 output
    data_path = project_root / "data" / "processed" / "ceramic_features.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                                "Please run the ingestion pipeline (T016-T020) first.")
    df = pd.read_csv(data_path)
    
    # Identify feature columns (exclude target and metadata)
    target_col = "weibull_modulus"
    exclude_cols = [target_col, "composition", "sample_count", "is_range_flag", 
                    "range_original", "range_uncertainty", "is_imputed"]
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No feature columns found in the dataset.")
    
    X = df[feature_cols]
    y = df[target_col]
    
    return X, y, feature_cols

def load_or_train_model(X: pd.DataFrame, y: pd.Series) -> Any:
    """
    Load the best model from data/results/ or train a fallback model
    if the saved model does not exist.
    """
    model_path = project_root / "data" / "results" / "best_model.joblib"
    
    if model_path.exists():
        log.info(f"Loading existing model from {model_path}")
        model = joblib.load(model_path)
    else:
        log.warning(f"Model not found at {model_path}. Training a fallback RandomForest model.")
        # Fallback training to ensure the script can run if US2 hasn't produced artifacts yet
        # This mirrors T027 logic
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = RandomForestRegressor(
            n_estimators=100, 
            random_state=42, 
            n_jobs=-1
        )
        model.fit(X_scaled, y)
        
        # Save the fallback model and scaler for consistency
        os.makedirs(model_path.parent, exist_ok=True)
        joblib.dump(model, model_path)
        joblib.dump(scaler, str(project_root / "data" / "results" / "scaler.joblib"))
        log.info("Fallback model trained and saved.")
    
    return model

def generate_shap_analysis(model: Any, X: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
    """
    Compute SHAP values and generate the summary plot.
    Returns a dictionary of importance scores.
    """
    log.info("Computing SHAP values...")
    
    # SHAP requires the model to be able to predict on the input data
    # If the model was trained on scaled data, we need to scale X here
    scaler_path = project_root / "data" / "results" / "scaler.joblib"
    if scaler_path.exists():
        scaler = joblib.load(str(scaler_path))
        X_input = scaler.transform(X)
    else:
        X_input = X.values
    
    # Use a subset for SHAP calculation if dataset is large to save time/memory
    # SHAP is computationally expensive
    sample_size = min(1000, len(X_input))
    X_sample = X_input[:sample_size]
    
    # Initialize Explainer
    # For tree-based models, TreeExplainer is much faster
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
    except Exception as e:
        log.warning(f"TreeExplainer failed ({e}), falling back to KernelExplainer. This may be slow.")
        explainer = shap.KernelExplainer(model.predict, X_sample)
        shap_values = explainer.shap_values(X_sample, nsamples=100)
    
    # Handle multi-output SHAP if necessary (Regression usually returns single array)
    if isinstance(shap_values, list):
        shap_values = shap_values[0] # Take the first output for regression
    
    # Calculate mean absolute SHAP values for feature importance
    shap_importance = np.mean(np.abs(shap_values), axis=0)
    importance_dict = {feature_names[i]: float(val) for i, val in enumerate(shap_importance)}
    
    # Sort features by importance
    sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "shap_values": shap_values,
        "X_sample": X_sample,
        "feature_names": feature_names,
        "importance": importance_dict,
        "sorted_features": sorted_features
    }

def plot_shap_summary(shap_data: Dict[str, Any], output_path: Path):
    """Generate and save the SHAP summary plot."""
    log.info(f"Generating SHAP summary plot at {output_path}")
    
    shap_values = shap_data["shap_values"]
    X_sample = shap_data["X_sample"]
    feature_names = shap_data["feature_names"]
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Use SHAP's built-in summary plot functionality
    # We pass the features as a numpy array and the feature names
    # Note: shap.summary_plot modifies the current matplotlib figure
    shap.summary_plot(
        shap_values, 
        X_sample, 
        feature_names=feature_names,
        plot_type="bar", # Use bar plot for clarity in summary
        show=False
    )
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    log.info(f"SHAP summary plot saved to {output_path}")

def save_feature_ranking(shap_data: Dict[str, Any], csv_path: Path, json_path: Path):
    """Save feature ranking as CSV and JSON."""
    log.info("Saving feature ranking tables...")
    
    sorted_features = shap_data["sorted_features"]
    importance = shap_data["importance"]
    
    # Create DataFrame
    ranking_df = pd.DataFrame(
        sorted_features, 
        columns=["feature", "mean_abs_shap_value"]
    )
    
    # Save CSV
    ranking_df.to_csv(csv_path, index=False)
    log.info(f"Feature ranking CSV saved to {csv_path}")
    
    # Save JSON with full details
    output_json = {
        "description": "Feature importance ranking based on mean absolute SHAP values",
        "total_features": len(importance),
        "rankings": [
            {"rank": i+1, "feature": f, "importance": v}
            for i, (f, v) in enumerate(sorted_features)
        ]
    }
    
    with open(json_path, 'w') as f:
        json.dump(output_json, f, indent=2)
    log.info(f"Feature importance JSON saved to {json_path}")

def main():
    """Main entry point for T041."""
    log.info("Starting T041: Generate SHAP summary plots and feature ranking tables.")
    
    # Ensure output directory exists
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load Data
        X, y, feature_cols = load_processed_data()
        log.info(f"Loaded {len(X)} samples with {len(feature_cols)} features.")
        
        # 2. Load or Train Model
        model = load_or_train_model(X, y)
        
        # 3. Compute SHAP
        shap_data = generate_shap_analysis(model, X, feature_cols)
        
        # 4. Generate Plots
        plot_path = results_dir / "shap_summary_plot.png"
        plot_shap_summary(shap_data, plot_path)
        
        # 5. Save Tables
        csv_path = results_dir / "feature_ranking.csv"
        json_path = results_dir / "shap_feature_importance.json"
        save_feature_ranking(shap_data, csv_path, json_path)
        
        log.info("T041 completed successfully.")
        
    except Exception as e:
        log.error(f"T041 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()