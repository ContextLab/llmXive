import argparse
import sys
from pathlib import Path
import pandas as pd
import logging
from analysis.visualizer import plot_completion_time, plot_error_count, plot_sus_score

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_completion_time_plot(input_path: str, output_path: str) -> str:
    """Wrapper to generate completion time plot."""
    return plot_completion_time(pd.read_csv(input_path), output_path)

def generate_error_count_plot(input_path: str, output_path: str) -> str:
    """Wrapper to generate error count plot."""
    return plot_error_count(pd.read_csv(input_path), output_path)

def generate_sus_score_plot(input_path: str, output_path: str) -> str:
    """Wrapper to generate SUS score plot."""
    return plot_sus_score(pd.read_csv(input_path), output_path)

def main():
    parser = argparse.ArgumentParser(description="Run visualization generation pipeline.")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sessions.csv",
                        help="Path to cleaned sessions CSV.")
    parser.add_argument("--output-dir", type=str, default="figures",
                        help="Directory for output figures.")
    
    args = parser.parse_args()
    
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Reading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    # Verify columns
    required = ['interface_type', 'completion_time', 'error_count', 'sus_score']
    if not all(col in df.columns for col in required):
        missing = [c for c in required if c not in df.columns]
        logger.error(f"Missing required columns: {missing}")
        sys.exit(1)
    
    logger.info("Generating plots...")
    
    # Completion Time
    out_ct = output_dir / "completion_time.png"
    plot_completion_time(df, str(out_ct))
    logger.info(f"Saved: {out_ct}")
    
    # Error Count
    out_ec = output_dir / "error_count.png"
    plot_error_count(df, str(out_ec))
    logger.info(f"Saved: {out_ec}")
    
    # SUS Score
    out_sus = output_dir / "sus_score.png"
    plot_sus_score(df, str(out_sus))
    logger.info(f"Saved: {out_sus}")
    
    logger.info("Visualization pipeline complete.")

if __name__ == "__main__":
    main()