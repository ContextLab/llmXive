"""Main entry point for the statistical significance analysis pipeline.

Orchestrates the full pipeline including data loading, analysis,
visualization, and reporting.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
import config
import loaders
import stats_engine
import viz
import correction


def integrate_visualizations(
    results: Dict[str, Any], output_dir: str
) -> None:
    """Integrate and save visualization outputs.

    Args:
        results: Dictionary containing analysis results.
        output_dir: Directory to save the plots.
    """
    os.makedirs(output_dir, exist_ok=True)

    corr_matrix = results["corr_matrix"]
    null_dist = results["null_dist"]
    observed_stats = results["observed_stats"]

    # Generate primary threshold visualizations
    viz.plot_primary_threshold_visualizations(
        corr_matrix, null_dist, observed_stats, output_dir
    )


def generate_sensitivity_report(
    results_list: List[Dict[str, Any]], thresholds: List[float], output_path: str
) -> None:
    """Generate a sensitivity report table.

    Args:
        results_list: List of result dictionaries from threshold sweeps.
        thresholds: List of thresholds used.
        output_path: Path to save the CSV report.
    """
    report_data = []
    for res in results_list:
        report_data.append({
            "threshold": res["threshold"],
            "significant_count": res["significant_count"],
        })

    df_report = pd.DataFrame(report_data)
    df_report.to_csv(output_path, index=False)


def main() -> None:
    """Main execution function."""
    # Ensure directories exist
    config.ensure_dirs()

    # Load configuration
    cfg = config.get_config()
    thresholds = cfg["thresholds"]
    n_permutations = cfg["n_permutations"]
    random_seed = cfg["random_seed"]

    # Example: Run analysis on a synthetic dataset for demonstration
    # In a real run, this would load from data/raw
    df = stats_engine.generate_synthetic_dataset(
        n_samples=500, n_vars=20, random_seed=random_seed
    )

    # Run full analysis pipeline for each threshold
    all_results = []
    sensitivity_data = []

    for threshold in thresholds:
        results = stats_engine.run_full_analysis_pipeline(
            df, threshold=threshold, n_permutations=n_permutations, random_seed=random_seed
        )

        # Calculate significant edges
        graph = results["graph"]
        significant_count = graph.number_of_edges()

        sensitivity_data.append({
            "threshold": threshold,
            "significant_count": significant_count,
        })

        # Save exploratory Spearman matrices
        exploratory_path = os.path.join(
            cfg["paths"]["output_exploratory"],
            f"spearman_matrix_{threshold}.csv"
        )
        stats_engine.save_exploratory_spearman_matrices(df, exploratory_path)

        # Integrate visualizations for primary threshold
        if abs(threshold - cfg["default_threshold"]) < 1e-6:
            primary_plots_dir = os.path.join(cfg["paths"]["output_plots"], "primary")
            integrate_visualizations(results, primary_plots_dir)

        all_results.append({
            "threshold": threshold,
            "results": results,
        })

    # Generate sensitivity report
    report_path = os.path.join(cfg["paths"]["output_reports"], "sensitivity_report.csv")
    generate_sensitivity_report(sensitivity_data, thresholds, report_path)

    # Generate general visualizations
    plots_dir = cfg["paths"]["output_plots"]
    os.makedirs(plots_dir, exist_ok=True)

    # Example: Plot sensitivity sweep
    sweep_plot_path = os.path.join(plots_dir, "sensitivity_sweep.png")
    viz.plot_sensitivity_sweep(sensitivity_data, sweep_plot_path)

    print("Analysis complete. Results saved to output/ directories.")


if __name__ == "__main__":
    main()
