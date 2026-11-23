"""
Main visualization module for T028.
Generates scatter plots of motion features vs. agency scores (FR-007).
"""
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Dict, Any

# Import from sibling module as defined in API surface
from visualization.plots import generate_scatter_plots, generate_importance_plot, generate_partial_dependence
from utils.logging_config import get_logger

logger = get_logger(__name__)

def run_visualization(data_path: str, metrics_path: str, output_dir: str):
    """
    Run all visualization tasks for User Story 3.
    
    Args:
        data_path: Path to the cleaned dataset (CSV).
        metrics_path: Path to the model metrics JSON.
        output_dir: Directory to save generated plots.
    """
    logger.info(f"Starting visualization pipeline. Data: {data_path}, Metrics: {metrics_path}")
    
    # Load data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    data = pd.read_csv(data_path)
    
    # Load metrics
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {output_path}")
    
    # Identify motion features from data columns
    # Based on T004 schema and T014/T017 processing, these are the expected motion predictors
    motion_features = ['latency', 'smoothness', 'lead_time']
    available_features = [f for f in motion_features if f in data.columns]
    
    if not available_features:
        logger.warning("No motion features found in data for scatter plots.")
        return

    # 1. Generate scatter plots for each motion feature vs. agency_score (FR-007)
    logger.info(f"Generating scatter plots for features: {available_features}")
    generate_scatter_plots(
        data=data,
        x_cols=available_features,
        y_col='agency_score',
        output_dir=output_path
    )
    
    # 2. Generate feature importance bar chart (FR-007)
    if 'rf_results' in metrics and 'feature_importance' in metrics['rf_results']:
        logger.info("Generating feature importance plot from Random Forest results.")
        generate_importance_plot(
            importance_dict=metrics['rf_results']['feature_importance'],
            output_dir=output_path
        )
    elif 'ols_results' in metrics and 'coefficients' in metrics['ols_results']:
        # Fallback to OLS coefficients if RF not available, normalized by magnitude
        logger.info("Generating feature importance plot from OLS coefficients.")
        coeffs = metrics['ols_results']['coefficients']
        # Filter out intercept if present
        feat_importance = {k: abs(v) for k, v in coeffs.items() if k != 'Intercept'}
        generate_importance_plot(importance_dict=feat_importance, output_dir=output_path)
    else:
        logger.warning("No feature importance data found in metrics.")

    # 3. Generate partial dependence plot for top predictor (FR-007)
    # Determine top predictor from RF importance or OLS magnitude
    top_feature = None
    if 'rf_results' in metrics and 'feature_importance' in metrics['rf_results']:
        importance = metrics['rf_results']['feature_importance']
        if importance:
            top_feature = max(importance, key=importance.get)
    elif 'ols_results' in metrics and 'coefficients' in metrics['ols_results']:
        coeffs = metrics['ols_results']['coefficients']
        # Exclude intercept
        valid_coeffs = {k: abs(v) for k, v in coeffs.items() if k != 'Intercept'}
        if valid_coeffs:
            top_feature = max(valid_coeffs, key=valid_coeffs.get)
    
    if top_feature and top_feature in data.columns:
        logger.info(f"Generating partial dependence plot for top feature: {top_feature}")
        # We need the fitted model for PDP. If stored in metrics, use it; otherwise skip or approximate.
        # For this task, we assume the model object is not serialized in JSON, so we re-fit a simple RF on the fly for PDP.
        # This is a standard practice for visualization-only steps if the model isn't persisted.
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.inspection import PartialDependenceDisplay
        
        X = data[available_features]
        y = data['agency_score']
        
        # Simple RF for PDP visualization
        rf_pdp = RandomForestRegressor(n_estimators=100, random_state=42)
        rf_pdp.fit(X, y)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        PartialDependenceDisplay.from_estimator(rf_pdp, X, features=[top_feature], ax=ax)
        plt.title(f'Partial Dependence: {top_feature} on Agency Score')
        plt.tight_layout()
        pdp_path = output_path / f'partial_dependence_{top_feature}.png'
        plt.savefig(pdp_path)
        plt.close(fig)
        logger.info(f"Saved partial dependence plot to {pdp_path}")
    else:
        logger.warning("Could not identify a top predictor for partial dependence plot.")

    logger.info("Visualization pipeline completed successfully.")

def main():
    """Main entry point for visualization script."""
    # Paths as defined in tasks.md and quickstart.md conventions
    data_path = "data/processed/raw_cleaned.csv"
    metrics_path = "data/results/model_metrics.json"
    output_dir = "data/results/plots"
    
    # Ensure we are running from project root
    if not os.path.exists(data_path):
        print(f"Error: Data file not found at {data_path}. Please ensure preprocessing is complete.")
        sys.exit(1)
    if not os.path.exists(metrics_path):
        print(f"Error: Metrics file not found at {metrics_path}. Please ensure modeling is complete.")
        sys.exit(1)
        
    try:
        run_visualization(data_path, metrics_path, output_dir)
        print("Visualization artifacts generated successfully.")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    main()