"""
T032: Save all plots to data/results/plots/ and generate summary interpretation.

This script orchestrates the generation of visualization artifacts and the
creation of a human-readable interpretation of the model results.
"""
import os
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# Add project root to path to allow relative imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from visualization.plots import (
    generate_scatter_plots,
    generate_importance_plot,
    generate_partial_dependence
)
from interpretation_logic import (
    load_model_metrics,
    generate_interpretation
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Main entry point for T032.
    1. Ensures output directories exist.
    2. Loads model metrics.
    3. Generates and saves plots.
    4. Generates and saves interpretation.md.
    """
    # Define paths
    results_dir = project_root / "data" / "results"
    plots_dir = results_dir / "plots"
    metrics_path = results_dir / "model_metrics.json"
    interpretation_path = results_dir / "interpretation.md"

    # Ensure directories exist
    plots_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {plots_dir}")

    # Check if metrics exist
    if not metrics_path.exists():
        logger.error(f"Required metrics file not found: {metrics_path}")
        logger.error("Cannot generate plots or interpretation without model results.")
        sys.exit(1)

    # Load metrics
    logger.info(f"Loading model metrics from {metrics_path}")
    metrics = load_model_metrics(metrics_path)

    # Load cleaned data for plotting (needed for scatter/pdp)
    # We assume the path is relative to the project root as per convention
    cleaned_data_path = project_root / "data" / "processed" / "cleaned_data.csv"
    if not cleaned_data_path.exists():
        logger.error(f"Required data file not found: {cleaned_data_path}")
        sys.exit(1)

    import pandas as pd
    df = pd.read_csv(cleaned_data_path)

    # 1. Generate Scatter Plots (Feature vs Agency Score)
    logger.info("Generating scatter plots...")
    scatter_paths = generate_scatter_plots(
        df,
        target_col="agency_score",
        feature_cols=["latency", "smoothness", "lead_time"],
        output_dir=plots_dir
    )
    logger.info(f"Saved scatter plots to: {scatter_paths}")

    # 2. Generate Feature Importance Bar Chart
    logger.info("Generating feature importance plot...")
    importance_path = generate_importance_plot(
        metrics,
        output_path=plots_dir / "feature_importance.png"
    )
    logger.info(f"Saved importance plot to: {importance_path}")

    # 3. Generate Partial Dependence Plot for top predictor
    logger.info("Generating partial dependence plot...")
    # Determine top predictor from RF importance or OLS absolute coefficients
    rf_importance = metrics.get("rf_feature_importance", {})
    ols_coeffs = metrics.get("ols_coefficients", {})

    top_predictor = None
    if rf_importance:
        top_predictor = max(rf_importance, key=rf_importance.get)
    elif ols_coeffs:
        # Exclude intercept
        filtered_coeffs = {k: v for k, v in ols_coeffs.items() if k != "intercept"}
        if filtered_coeffs:
            top_predictor = max(filtered_coeffs, key=lambda k: abs(filtered_coeffs[k]))

    if top_predictor:
        pdp_path = generate_partial_dependence(
            df,
            model_type="random_forest", # We use RF for PDP as it's non-linear
            feature=top_predictor,
            target="agency_score",
            output_path=plots_dir / f"partial_dependence_{top_predictor}.png"
        )
        logger.info(f"Saved PDP plot to: {pdp_path}")
    else:
        logger.warning("Could not determine top predictor for PDP.")

    # 4. Generate Interpretation
    logger.info("Generating interpretation...")
    interpretation_text = generate_interpretation(metrics, df)

    # Write interpretation to file
    with open(interpretation_path, "w", encoding="utf-8") as f:
        f.write(interpretation_text)
    
    logger.info(f"Saved interpretation to: {interpretation_path}")
    logger.info("T032 completed successfully.")

if __name__ == "__main__":
    main()
