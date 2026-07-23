"""
Orchestration script to generate all required visualizations.
This script is invoked by the run-book to produce the figure artifacts.
"""
import argparse
import sys
from pathlib import Path
import pandas as pd
from analysis.visualizer import Visualizer
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_completion_time_plot(data_path: str, output_dir: str):
    """Generate the completion time box plot."""
    logger.info(f"Loading data from {data_path}")
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    data = pd.read_csv(data_path)
    visualizer = Visualizer(output_dir=output_dir)
    fig = visualizer.plot_completion_time(data)
    if fig is None:
        raise ValueError("Failed to generate completion time plot (invalid data or logic)")
    logger.info("Completion time plot generated.")

def generate_error_count_plot(data_path: str, output_dir: str):
    """Generate the error count box plot."""
    data = pd.read_csv(data_path)
    visualizer = Visualizer(output_dir=output_dir)
    fig = visualizer.plot_error_count(data)
    if fig is None:
        raise ValueError("Failed to generate error count plot")
    logger.info("Error count plot generated.")

def generate_sus_score_plot(data_path: str, output_dir: str):
    """Generate the SUS score box plot."""
    data = pd.read_csv(data_path)
    visualizer = Visualizer(output_dir=output_dir)
    fig = visualizer.plot_sus_score(data)
    if fig is None:
        raise ValueError("Failed to generate SUS score plot")
    logger.info("SUS score plot generated.")

def main():
    parser = argparse.ArgumentParser(description="Run visualization generation pipeline")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to cleaned sessions CSV (data/processed/cleaned_sessions.csv)")
    parser.add_argument("--output-dir", type=str, default="figures",
                        help="Directory to save generated figures")
    args = parser.parse_args()

    logger.info(f"Starting visualization pipeline with input: {args.input}")
    
    try:
        generate_completion_time_plot(args.input, args.output_dir)
        generate_error_count_plot(args.input, args.output_dir)
        generate_sus_score_plot(args.input, args.output_dir)
        logger.info("Visualization pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()