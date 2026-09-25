"""
T025: Export final figure to outputs/ with proper labeling.

This script generates the final scatter plot visualization, ensuring
the title includes the correlation coefficient, and exports it to
outputs/visualizations/correlation_scatter.png.

It depends on:
- code/visualize.py (generate_scatter_plot)
- code/analyze.py (compute_spearman_correlation_with_ci)
- data/processed/consistency_scores.csv (input data)
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib
# Use Agg backend for non-interactive environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add project root to path if running as script
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from visualize import generate_scatter_plot, validate_visualization_accessibility
from analyze import compute_spearman_correlation_with_ci
from logging_config import get_logger, log_state_event
from utils import handle_corrupted_file

def ensure_output_directory(path):
    """Ensure the output directory exists."""
    directory = os.path.dirname(path)
    if not os.exists(directory):
        os.makedirs(directory)
        log_state_event(f"Created output directory: {directory}")

def main():
    parser = argparse.ArgumentParser(description="Export final correlation figure with labeled title.")
    parser.add_argument(
        "--input-data",
        type=str,
        default="data/processed/consistency_scores.csv",
        help="Path to the CSV file containing consistency and trust scores."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="outputs/visualizations/correlation_scatter.png",
        help="Path where the final PNG figure will be saved."
    )
    args = parser.parse_args()

    logger = get_logger("export_figure")
    logger.info(f"Starting figure export task T025")
    log_state_event("T025: Exporting final figure")

    # Check if input data exists
    if not os.exists(args.input_data):
        error_msg = f"Input data file not found: {args.input_data}"
        logger.error(error_msg)
        # Per constraints, we must fail loudly, not fabricate data
        raise FileNotFoundError(error_msg)

    try:
        # Load data
        df = pd.read_csv(args.input_data)
        required_cols = ['consistency_score', 'trust_score']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Input CSV must contain columns: {required_cols}")

        # Compute correlation for the title
        rho, ci_low, ci_high = compute_spearman_correlation_with_ci(
            df['consistency_score'].values,
            df['trust_score'].values
        )
        
        # Format title with correlation coefficient
        title = f"Spearman Correlation: ρ = {rho:.3f} (95% CI: [{ci_low:.3f}, {ci_high:.3f}])"
        logger.info(f"Computed correlation for title: {title}")

        # Ensure output directory exists
        ensure_output_directory(args.output_path)

        # Generate the plot
        fig, ax = generate_scatter_plot(
            df['consistency_score'].values,
            df['trust_score'].values,
            title=title,
            xlabel="Intra-Modal Consistency Score",
            ylabel="User Trust Score",
            show_ci=True
        )

        # Validate accessibility before saving
        if not validate_visualization_accessibility(fig):
            logger.warning("Generated visualization failed accessibility checks. Saving anyway but review recommended.")

        # Save the figure
        fig.savefig(args.output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Successfully exported figure to {args.output_path}")
        log_state_event(f"T025: Figure exported to {args.output_path}")

        # Verify file exists and has content
        if not os.path.exists(args.output_path) or os.path.getsize(args.output_path) == 0:
            raise RuntimeError(f"Failed to create valid output file at {args.output_path}")

        logger.info("T025 completed successfully")
        return 0

    except Exception as e:
        handle_corrupted_file(e)
        logger.error(f"T025 failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
