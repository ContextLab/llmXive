import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import sys

# Import sibling modules
from visualization.plots import generate_importance_plot, generate_scatter_plots, generate_partial_dependence
from utils.logging_config import get_logger

logger = get_logger(__name__)

def run_visualization(
    data_path: str,
    metrics_path: str,
    output_dir: str
) -> None:
    """
    Main entry point for visualization tasks.
    1. Loads cleaned data.
    2. Loads model metrics to identify the top predictor.
    3. Generates scatter plots for all motion features.
    4. Generates feature importance plot.
    5. Generates partial dependence plot for the top predictor.
    
    Args:
        data_path: Path to cleaned CSV.
        metrics_path: Path to model_metrics.json.
        output_dir: Directory to save plots.
    """
    logger.info(f"Starting visualization pipeline. Data: {data_path}, Metrics: {metrics_path}")
    
    data_path = Path(data_path)
    metrics_path = Path(metrics_path)
    output_dir = Path(output_dir)
    
    # 1. Load Data
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")
    
    # 2. Load Metrics to find top predictor
    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        sys.exit(1)
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Extract feature importance from metrics
    # Assuming structure: {"rf_importance": [{"feature": ..., "importance": ...}, ...]}
    importance_data = metrics.get('rf_importance', [])
    
    if not importance_data:
        logger.warning("No feature importance data found in metrics. Skipping importance plot.")
        top_feature = None
    else:
        imp_df = pd.DataFrame(importance_data)
        imp_df = imp_df.sort_values(by='importance', ascending=False)
        top_feature = imp_df.iloc[0]['feature']
        logger.info(f"Top predictor identified: {top_feature}")
        
        # Generate Importance Plot
        importance_output = output_dir / "feature_importance.png"
        generate_importance_plot(imp_df, importance_output)
        logger.info(f"Saved importance plot to {importance_output}")
    
    # 3. Generate Scatter Plots
    # Identify motion features (exclude 'participant_id', 'agency_score')
    motion_features = [col for col in df.columns if col not in ['participant_id', 'agency_score']]
    if motion_features:
        scatter_output_dir = output_dir
        generate_scatter_plots(df, motion_features, 'agency_score', scatter_output_dir)
        logger.info(f"Generated scatter plots for {len(motion_features)} features.")
    else:
        logger.warning("No motion features found for scatter plots.")
    
    # 4. Generate Partial Dependence Plot for Top Predictor
    if top_feature:
        # We need the model to generate the PDP. 
        # Since the model isn't passed directly here, we have two options:
        # A. Re-train the model (expensive, but ensures consistency).
        # B. Assume the model is saved in a standard location or passed via config.
        # Given the task description "Implement partial dependence plot for the top predictor",
        # and the dependency on US2 (model fitting), we should ideally load the model.
        # However, the `model_fitting.py` task (T022b) likely saved the model.
        # Let's look for a saved model or re-run a quick fit if necessary.
        # For this specific task T030, we will assume the model was saved as `data/results/model.pkl`
        # by the modeling phase. If not, we might need to re-run the fitting logic.
        
        model_path = Path("data/results/model_rf.pkl")
        if not model_path.exists():
            logger.warning(f"Model file not found at {model_path}. Attempting to re-fit or skip.")
            # If we can't load the model, we cannot generate a PDP.
            # We will skip this step with a warning.
            logger.warning("Skipping Partial Dependence Plot: Model not found.")
        else:
            import joblib
            model = joblib.load(model_path)
            
            # Ensure the model was trained on the same features
            # We'll use the full dataframe, assuming the model handles the columns
            # or we subset to the columns the model expects if we had that info.
            # For safety, we pass the dataframe columns that match the model's training.
            # If the model was trained on a subset, we need to know which.
            # Assuming standard practice: model was trained on `motion_features`.
            X_for_pdp = df[motion_features]
            
            pdp_output = output_dir / f"pdp_{top_feature}.png"
            generate_partial_dependence(
                model, 
                X_for_pdp, 
                top_feature, 
                pdp_output,
                title=f"Partial Dependence: {top_feature}"
            )
            logger.info(f"Saved partial dependence plot to {pdp_output}")
    else:
        logger.info("No top feature identified; skipping partial dependence plot.")
    
    logger.info("Visualization pipeline complete.")

def main():
    """
    CLI entry point.
    Expects environment variables or default paths:
    - DATA_PATH: data/processed/cleaned_data.csv
    - METRICS_PATH: data/results/model_metrics.json
    - OUTPUT_DIR: data/results/plots
    """
    data_path = os.getenv("DATA_PATH", "data/processed/cleaned_data.csv")
    metrics_path = os.getenv("METRICS_PATH", "data/results/model_metrics.json")
    output_dir = os.getenv("OUTPUT_DIR", "data/results/plots")
    
    run_visualization(data_path, metrics_path, output_dir)

if __name__ == "__main__":
    main()