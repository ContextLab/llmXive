"""
Script to generate all visualization plots from cleaned data.
This script is invoked by the main analysis pipeline.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from analysis.visualizer import Visualizer
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_completion_time_plot(input_path: str, output_dir: str) -> str:
    """Generate and save the completion time plot."""
    data = pd.read_csv(input_path)
    visualizer = Visualizer(output_dir=output_dir)
    return visualizer.plot_completion_time(data)


def generate_sus_score_plot(input_path: str, output_dir: str) -> str:
    """Generate and save the SUS score plot."""
    data = pd.read_csv(input_path)
    visualizer = Visualizer(output_dir=output_dir)
    return visualizer.plot_sus_score(data)


def main():
    """Main entry point for the visualization runner."""
    parser = argparse.ArgumentParser(description='Generate visualization plots')
    parser.add_argument('--input', type=str, required=True,
                      help='Path to cleaned data CSV')
    parser.add_argument('--output_dir', type=str, default='figures',
                      help='Output directory for figures')
    args = parser.parse_args()

    # Validate input file
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info(f"Loading data from: {args.input}")
    data = pd.read_csv(args.input)

    # Validate required columns
    required_cols = ['interface_type', 'completion_time_seconds', 'error_count', 'sus_score']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)

    # Initialize visualizer
    visualizer = Visualizer(output_dir=args.output_dir)

    # Generate all plots
    logger.info("Generating completion time plot...")
    visualizer.plot_completion_time(data)

    logger.info("Generating error count plot...")
    visualizer.plot_error_count(data)

    logger.info("Generating SUS score plot...")
    visualizer.plot_sus_score(data)

    # Generate explanation engagement plot if column exists
    if 'explanation_engagement_time_seconds' in data.columns:
        logger.info("Generating explanation engagement plot...")
        visualizer.plot_explanation_engagement(data)

    logger.info("All visualizations generated successfully.")
    logger.info(f"Output directory: {args.output_dir}")


if __name__ == '__main__':
    main()