"""
T032 Implementation: Save all plots to data/results/plots/ and generate interpretation.md.

This script orchestrates the final visualization step:
1. Ensures the output directory `data/results/plots/` exists.
2. Imports and calls existing visualization functions from `code/visualization/plots.py`
   to generate scatter plots, importance bars, and partial dependence plots.
3. Imports and calls the interpretation logic from `code/interpretation_logic.py`
   to generate the summary text based on model metrics.
4. Writes the plots to disk and the interpretation to `data/results/interpretation.md`.
"""
import os
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Import from existing project modules based on API surface
# Note: We assume the project root is the working directory.
# The API surface lists `code/visualization/plots.py` and `code/interpretation_logic.py`.

# Adjust imports to match the project structure implied by API surface
# The API surface says: `from visualization.plots import ...`
# and `from interpretation_logic import ...`
# This suggests the `code` directory is in `sys.path` or we are running from `code`.
# To be safe and compliant with "stay inside project tree", we use relative imports logic
# or assume standard execution from root where `code` is a package or in path.
# Given the API surface `import as: from visualization.plots import ...`,
# we will assume `code` is added to sys.path or we are running `python code/...`.

# Let's add the parent directory to path to resolve `visualization` and `interpretation_logic`
# if they are siblings of this script (which is in code/visualization/).
# Actually, the API surface says `code/visualization/plots.py` exists.
# So `visualization` is likely a package inside `code`.
# And `interpretation_logic.py` is directly in `code`.

import sys
from pathlib import Path

# Add the 'code' directory to sys.path to allow imports like 'visualization' and 'interpretation_logic'
# This assumes this script is run as `python code/visualization/t032_save_plots_and_interpret.py`
# or the working directory is the project root.
current_file = Path(__file__).resolve()
code_dir = current_file.parent.parent # code/
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from visualization.plots import generate_importance_plot, generate_scatter_plots, generate_partial_dependence
from interpretation_logic import load_model_metrics, generate_interpretation
from utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Starting T032: Saving plots and generating interpretation.")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    plots_dir = project_root / "data" / "results" / "plots"
    metrics_path = project_root / "data" / "results" / "model_metrics.json"
    interpretation_path = project_root / "data" / "results" / "interpretation.md"
    
    # Ensure plots directory exists
    plots_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {plots_dir}")
    
    # Load model metrics
    if not metrics_path.exists():
        logger.error(f"Model metrics file not found: {metrics_path}")
        logger.error("T032 requires model_metrics.json from T026. Cannot proceed.")
        raise FileNotFoundError(f"Missing required input: {metrics_path}")
    
    metrics = load_model_metrics(metrics_path)
    logger.info("Model metrics loaded successfully.")
    
    # Load cleaned data for plotting (needed by plot generators)
    cleaned_data_path = project_root / "data" / "processed" / "cleaned_data.csv"
    if not cleaned_data_path.exists():
        logger.error(f"Cleaned data file not found: {cleaned_data_path}")
        raise FileNotFoundError(f"Missing required input: {cleaned_data_path}")
    
    import pandas as pd
    df = pd.read_csv(cleaned_data_path)
    
    # 1. Generate Scatter Plots (T028)
    logger.info("Generating scatter plots...")
    generate_scatter_plots(df, output_dir=plots_dir)
    logger.info(f"Scatter plots saved to {plots_dir}")
    
    # 2. Generate Feature Importance Bar Chart (T029)
    logger.info("Generating feature importance plot...")
    # Extract importance from metrics if available, otherwise rely on plot function internals
    importance_scores = metrics.get("rf_importance", {})
    if not importance_scores:
        # Fallback: try to get from ols coefficients if RF not available, though RF is preferred for importance
        importance_scores = {k: abs(v) for k, v in metrics.get("ols_coefficients", {}).items() if k != "intercept"}
    
    generate_importance_plot(importance_scores, output_path=plots_dir / "feature_importance.png")
    logger.info(f"Feature importance plot saved to {plots_dir / 'feature_importance.png'}")
    
    # 3. Generate Partial Dependence Plot for top predictor (T030)
    logger.info("Generating partial dependence plot...")
    # Identify top predictor
    top_feature = None
    if importance_scores:
        top_feature = max(importance_scores, key=importance_scores.get)
    
    if top_feature:
        generate_partial_dependence(df, top_feature, output_path=plots_dir / f"partial_dependence_{top_feature}.png")
        logger.info(f"Partial dependence plot saved to {plots_dir / f'partial_dependence_{top_feature}.png'}")
    else:
        logger.warning("No top feature identified for partial dependence plot.")
    
    # 4. Generate Interpretation (T031)
    logger.info("Generating interpretation text...")
    interpretation_text = generate_interpretation(metrics)
    
    # 5. Save Interpretation to Markdown
    with open(interpretation_path, "w", encoding="utf-8") as f:
        f.write("# Project Interpretation: Visual Motion and Perceived Agency\n\n")
        f.write("## Summary\n\n")
        f.write(interpretation_text)
        f.write("\n\n---\n")
        f.write(f"*Generated by T032 pipeline on {Path(__file__).name}*")
    
    logger.info(f"Interpretation saved to {interpretation_path}")
    
    # Close all plots to free memory
    plt.close('all')
    
    logger.info("T032 completed successfully.")

if __name__ == "__main__":
    main()
