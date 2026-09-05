"""
Save Analysis Outputs Module.

Orchestrates the saving of all analysis outputs including summary and plots.
"""
import os
import sys
import json
import logging
import argparse
import pandas as pd
import numpy as np

from code.analysis_summary import generate_analysis_summary
from code.plot_top_features import generate_top_feature_plots, create_combined_plot
from code.correlation_analysis import calculate_correlation_pvalues, save_correlation_results

logger = logging.getLogger(__name__)

def ensure_output_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

def load_feature_importance(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    return pd.read_csv(path)

def load_correlation_results(path: str) -> Dict[str, Dict[str, float]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def get_top_features(importance_df: pd.DataFrame, n: int = 5) -> List[str]:
    if importance_df.empty:
        return []
    sorted_df = importance_df.sort_values(
        by=['importance_score', 'feature'],
        ascending=[False, True]
    )
    return sorted_df['feature'].head(n).tolist()

def generate_and_save_top5_plot(
    data_path: str,
    importance_path: str,
    correlations_path: str,
    output_path: str,
    target: str = "conductivity",
    n_top: int = 5
) -> None:
    """
    Generate and save the top 5 feature correlation plot.
    """
    logger.info("Loading data for plotting...")
    df = pd.read_csv(data_path)
    importance_df = load_feature_importance(importance_path)
    # correlation_results = load_correlation_results(correlations_path) # Not strictly needed for plot

    top_features = get_top_features(importance_df, n_top)
    logger.info(f"Top features for plot: {top_features}")

    # Create combined plot
    from code.plot_top_features import create_combined_plot
    create_combined_plot(df, top_features, target, output_path)

def save_feature_importance_csv(
    importance_df: pd.DataFrame,
    output_path: str
) -> None:
    ensure_output_dir(output_path)
    importance_df.to_csv(output_path, index=False)
    logger.info(f"Saved feature importance to {output_path}")

def main():
    """
    Main entry point for saving analysis outputs.
    """
    parser = argparse.ArgumentParser(description="Save analysis outputs.")
    parser.add_argument("--data", type=str, required=True, help="Path to processed data CSV.")
    parser.add_argument("--importance", type=str, required=True, help="Path to feature importance CSV.")
    parser.add_argument("--correlations", type=str, required=True, help="Path to correlation results JSON.")
    parser.add_argument("--output-summary", type=str, required=True, help="Path to output summary JSON.")
    parser.add_argument("--output-plot", type=str, required=True, help="Path to output plot PNG.")
    parser.add_argument("--target", type=str, default="conductivity", help="Target variable name.")
    parser.add_argument("--top-n", type=int, default=5, help="Number of top features.")
    args = parser.parse_args()

    # Setup logging
    from code.logging_config import setup_logging
    setup_logging()

    # Generate Analysis Summary
    logger.info("Generating analysis summary...")
    generate_analysis_summary(
        args.importance,
        args.correlations,
        args.output_summary,
        args.top_n
    )

    # Generate Top 5 Plot
    logger.info("Generating top 5 plot...")
    generate_and_save_top5_plot(
        args.data,
        args.importance,
        args.correlations,
        args.output_plot,
        args.target,
        args.top_n
    )

    logger.info("All outputs saved successfully.")

if __name__ == "__main__":
    main()