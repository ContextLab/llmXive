import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from utils.logging import setup_logging, get_logger, log_counterbalance_strategy
from config import get_project_root, ensure_directories
from stimuli.process import process_stimuli_batch, categorize_complexity, main as stimuli_main
from stimuli.serialize import load_raw_complexity_scores, apply_categorization, save_final_csv, main as serialize_main
from data.load import load_response_logs, main as load_main
from data.process import aggregate_d_scores, save_aggregated_scores, main as process_main
from data.counterbalance import generate_counterbalance_assignments, main as counterbalance_main
from analysis.pca import run_pca_check, main as pca_main
from analysis.permutation import run_permutation_test, main as permutation_main
from analysis.results import save_json_results, main as results_main
from viz.plot import plot_boxplot, plot_sensitivity, plot_loio_sensitivity

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Pipeline for analyzing visual complexity and implicit bias"
    )

    parser.add_argument(
        '--null-effect',
        action='store_true',
        help='Run in null-effect mode (synthetic data for CI testing)'
    )

    parser.add_argument(
        '--skip-stimuli',
        action='store_true',
        help='Skip stimulus processing step'
    )

    parser.add_argument(
        '--skip-analysis',
        action='store_true',
        help='Skip statistical analysis step'
    )

    parser.add_argument(
        '--split-ratio',
        type=float,
        default=0.5,
        help='Ratio of participants starting with Low vs High complexity'
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the pipeline."""
    args = parse_args()

    # Setup logging
    setup_logging()
    logger.info("Starting pipeline...")

    root = get_project_root()
    ensure_directories()

    # Step 1: Generate counterbalance assignments (always run)
    logger.info("Step 1: Generating counterbalance assignments...")
    counterbalance_main()

    # Log strategy
    log_counterbalance_strategy(seed=42, split_ratio=args.split_ratio)

    # Step 2: Process stimuli (unless skipped)
    if not args.skip_stimuli:
        logger.info("Step 2: Processing stimuli...")
        try:
            stimuli_main()
        except FileNotFoundError as e:
            if not args.null_effect:
                logger.error(f"Stimuli processing failed: {e}")
                raise
            else:
                logger.warning("Skipping stimuli processing in null-effect mode")

    # Step 3: Load and process response data
    logger.info("Step 3: Loading and processing response data...")
    try:
        load_main()
        process_main()
    except RuntimeError as e:
        if not args.null_effect:
            logger.error(f"Data processing failed: {e}")
            raise
        else:
            logger.warning("Skipping data processing in null-effect mode")

    # Step 4: PCA check
    logger.info("Step 4: Running PCA check...")
    try:
        pca_main()
    except Exception as e:
        logger.warning(f"PCA check failed: {e}")

    # Step 5: Statistical analysis (unless skipped)
    if not args.skip_analysis:
        logger.info("Step 5: Running statistical analysis...")
        try:
            permutation_main()
            results_main()
        except Exception as e:
            logger.error(f"Statistical analysis failed: {e}")
            raise

    # Step 6: Visualization
    logger.info("Step 6: Generating visualizations...")
    try:
        # Load data for plotting
        d_scores_path = root / "data" / "processed" / "aggregated_d_scores.csv"
        if d_scores_path.exists():
            import pandas as pd
            df = pd.read_csv(d_scores_path)
            output_path = root / "data" / "results" / "d_score_comparison.png"
            plot_boxplot(df, output_path=output_path)

            # Load sensitivity results
            sensitivity_path = root / "data" / "results" / "sensitivity_results.json"
            if sensitivity_path.exists():
                import json
                with open(sensitivity_path, 'r') as f:
                    sens_results = json.load(f)

                # Plot sensitivity
                sens_plot_path = root / "data" / "results" / "sensitivity_plot.png"
                plot_sensitivity(sens_results, output_path=sens_plot_path)

                # Plot LOIO
                loio_results = sens_results.get('loio_results', [])
                if loio_results:
                    loio_plot_path = root / "data" / "results" / "loio_plot.png"
                    plot_loio_sensitivity(loio_results, output_path=loio_plot_path)
        else:
            logger.warning(f"D-scores file not found: {d_scores_path}")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")

    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
