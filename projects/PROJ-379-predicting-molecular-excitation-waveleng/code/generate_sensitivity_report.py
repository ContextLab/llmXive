import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_sensitivity_results(path: Path) -> dict:
    """Load the sensitivity sweep results from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity results not found at {path}. "
                                "Run code/sensitivity.py first.")
    with open(path, 'r') as f:
        return json.load(f)

def generate_report_csv(results: dict, output_path: Path) -> None:
    """Generate a CSV report summarizing error rates across thresholds."""
    records = []
    thresholds = results.get("thresholds", [])
    metrics = results.get("metrics", {})

    if not thresholds:
        raise ValueError("No thresholds found in sensitivity results.")

    for th in thresholds:
        # Extract metrics for this threshold
        # The sensitivity.py output structure is expected to be:
        # { "thresholds": [...], "metrics": { "20": {...}, "30": {...} ... } }
        th_str = str(th)
        if th_str in metrics:
            m = metrics[th_str]
            records.append({
                "threshold_nm": th,
                "mae": m.get("mae", None),
                "error_rate": m.get("error_rate", None),
                "pass_count": m.get("pass_count", None),
                "total_count": m.get("total_count", None),
                "sc001_status": m.get("sc001_status", "N/A")
            })
        else:
            logger.warning(f"No metrics found for threshold {th}")

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("No data to write to CSV. Check sensitivity results format.")
    
    df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity report CSV written to {output_path}")

def generate_plot(results: dict, output_path: Path) -> None:
    """Generate a plot of error rate vs threshold."""
    thresholds = results.get("thresholds", [])
    metrics = results.get("metrics", {})
    
    x = []
    y_error_rate = []
    y_mae = []

    for th in thresholds:
        th_str = str(th)
        if th_str in metrics:
            m = metrics[th_str]
            x.append(th)
            y_error_rate.append(m.get("error_rate", 0))
            y_mae.append(m.get("mae", 0))

    if not x:
        logger.warning("No data points for plotting.")
        return

    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:blue'
    ax1.set_xlabel('Threshold (nm)')
    ax1.set_ylabel('MAE (nm)', color=color)
    ax1.plot(x, y_mae, color=color, marker='o', label='MAE')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.6)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Error Rate', color=color)
    ax2.plot(x, y_error_rate, color=color, marker='s', label='Error Rate')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()
    plt.title('Sensitivity Analysis: Error Rate vs MAE Threshold')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Sensitivity plot written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate Sensitivity Report (CSV & Plot)")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/sensitivity_results.json",
        help="Path to sensitivity results JSON (output of code/sensitivity.py)"
    )
    parser.add_argument(
        "--output-csv", 
        type=str, 
        default="data/processed/sensitivity_report.csv",
        help="Path for output CSV report"
    )
    parser.add_argument(
        "--output-plot", 
        type=str, 
        default="data/processed/sensitivity_plot.png",
        help="Path for output plot image"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_csv = Path(args.output_csv)
    output_plot = Path(args.output_plot)

    # Ensure output directories exist
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_plot.parent.mkdir(parents=True, exist_ok=True)

    try:
        results = load_sensitivity_results(input_path)
        generate_report_csv(results, output_csv)
        generate_plot(results, output_plot)
        logger.info("Sensitivity report generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate sensitivity report: {e}")
        raise

if __name__ == "__main__":
    main()