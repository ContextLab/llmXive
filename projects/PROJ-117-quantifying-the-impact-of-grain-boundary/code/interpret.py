"""
Interpretability and Sensitivity Analysis Module.
Generates SHAP plots and performs sensitivity analysis on model performance thresholds.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
from xgboost import XGBRegressor

# Import project config
from config import (
    R2_PERFORMANCE_THRESHOLD,
    R2_THRESHOLD_JUSTIFICATION,
    ARTIFACTS_DIR,
    FIGURES_DIR,
    REPORTS_DIR,
    MODELS_DIR,
    DATA_PROCESSED_DIR
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_model_and_data(model_path: str = None, data_path: str = None) -> Tuple[XGBRegressor, pd.DataFrame, pd.DataFrame]:
    """
    Loads the trained model and the processed dataset.
    """
    if model_path is None:
        model_path = str(MODELS_DIR / "best_model.json")
    if data_path is None:
        data_path = str(DATA_PROCESSED_DIR / "cleaned_dataset.parquet")

    logger.info(f"Loading model from {model_path}")
    model = XGBRegressor()
    model.load_model(model_path)

    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)

    # Assuming the target column is 'diffusivity' based on context
    # and features are everything else. Adjust if schema differs.
    target_col = 'diffusivity'
    if target_col not in df.columns:
        # Fallback or error handling if column name varies
        logger.warning(f"Target column '{target_col}' not found. Checking for 'log_diffusivity' or similar.")
        target_col = [c for c in df.columns if 'diffusivity' in c.lower()][0]
    
    X = df.drop(columns=[target_col])
    y = df[target_col]

    return model, X, y, target_col


def generate_shap_analysis(model: XGBRegressor, X: pd.DataFrame, target_col: str) -> Dict[str, Any]:
    """
    Generates SHAP summary plot and ranked feature importance.
    """
    logger.info("Generating SHAP analysis...")
    
    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Save SHAP values for potential further analysis
    shap_summary_path = FIGURES_DIR / "shap_summary_plot.png"
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.title("SHAP Feature Importance")
    plt.tight_layout()
    plt.savefig(shap_summary_path)
    plt.close()
    logger.info(f"Saved SHAP summary plot to {shap_summary_path}")

    # Create ranked feature importance list
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'importance': np.abs(shap_values).mean(axis=0)
    }).sort_values(by='importance', ascending=False)

    feature_ranking_path = REPORTS_DIR / "feature_ranking.json"
    with open(feature_ranking_path, 'w') as f:
        json.dump(importance_df.to_dict(orient='records'), f, indent=2)
    logger.info(f"Saved feature ranking to {feature_ranking_path}")

    return {
        "shap_plot_path": str(shap_summary_path),
        "ranking_path": str(feature_ranking_path),
        "top_features": importance_df.head(10)['feature'].tolist()
    }


def perform_sensitivity_analysis(model: XGBRegressor, X: pd.DataFrame, y: pd.Series, target_col: str) -> pd.DataFrame:
    """
    Performs sensitivity analysis by sweeping R² thresholds.
    """
    logger.info("Performing sensitivity analysis...")
    
    # Predict
    y_pred = model.predict(X)
    
    # Calculate actual R2
    actual_r2 = r2_score(y, y_pred)
    logger.info(f"Actual Model R²: {actual_r2:.4f}")

    # Define threshold range
    # Sweep from 0.0 to 0.95 in steps of 0.05
    thresholds = np.arange(0.0, 0.96, 0.05)
    
    results = []
    for thresh in thresholds:
        # Define Pass: Model R² > threshold
        passed = actual_r2 > thresh
        # Calculate Pass Rate (proportion of "folds" - here effectively 1 since we use the whole test set)
        # In a real cross-validation scenario, this would be the mean of passes across folds.
        pass_rate = 1.0 if passed else 0.0
        
        results.append({
            "threshold": round(thresh, 2),
            "pass_rate": pass_rate,
            "model_r2": round(actual_r2, 4),
            "justification": R2_THRESHOLD_JUSTIFICATION if round(thresh, 2) == R2_PERFORMANCE_THRESHOLD else ""
        })

    df_results = pd.DataFrame(results)
    
    output_path = REPORTS_DIR / "threshold-variation-table.csv"
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved sensitivity analysis to {output_path}")

    return df_results


def main():
    """
    Main entry point for the interpretability pipeline.
    """
    try:
        model, X, y, target_col = load_model_and_data()
        
        shap_results = generate_shap_analysis(model, X, target_col)
        sensitivity_df = perform_sensitivity_analysis(model, X, y, target_col)
        
        logger.info("Interpretability analysis complete.")
        logger.info(f"R² Threshold Justification: {R2_THRESHOLD_JUSTIFICATION}")
        
    except Exception as e:
        logger.error(f"Interpretability analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()