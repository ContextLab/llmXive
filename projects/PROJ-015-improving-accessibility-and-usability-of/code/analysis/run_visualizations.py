import argparse
import sys
from pathlib import Path
import pandas as pd
import logging

from analysis.visualizer import plot_completion_time, plot_error_count, plot_sus_score
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_completion_time_plot(input_path: str, output_path: str) -> None:
    """Wrapper to generate completion time plot."""
    df = pd.read_csv(input_path)
    plot_completion_time(df, output_path)

def generate_error_count_plot(input_path: str, output_path: str) -> None:
    """Wrapper to generate error count plot."""
    df = pd.read_csv(input_path)
    plot_error_count(df, output_path)

def generate_sus_score_plot(input_path: str, output_path: str) -> None:
    """Wrapper to generate SUS score plot."""
    df = pd.read_csv(input_path)
    plot_sus_score(df, output_path)

def main() -> None:
    """CLI entry point for running all visualizations."""
    parser = argparse.ArgumentParser(description="Run visualization generation pipeline.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/cleaned_sessions.csv",
        help="Path to cleaned sessions CSV."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="figures",
        help="Output directory for figures."
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting visualization generation...")
    
    try:
        generate_completion_time_plot(str(input_path), str(output_dir / "completion_time.png"))
        generate_error_count_plot(str(input_path), str(output_dir / "error_count.png"))
        generate_sus_score_plot(str(input_path), str(output_dir / "sus_score.png"))
        logger.info("Visualization pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Error during visualization generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()