import os
import sys
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import yaml

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_sensitivity_results() -> Optional[pd.DataFrame]:
    """Load sensitivity sweep results from CSV."""
    path = Path("results/sensitivity_fpr_fnr.csv")
    if not path.exists():
        logger.warning(f"Sensitivity results file not found: {path}")
        return None
    
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded sensitivity results with {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load sensitivity results: {e}")
        return None

def check_classification_status() -> str:
    """Check classification status from state file."""
    status_path = Path("state/classification_status.yaml")
    if not status_path.exists():
        logger.warning("Classification status file not found, assuming SKIPPED")
        return "SKIPPED"
    
    try:
        with open(status_path, 'r') as f:
            status_data = yaml.safe_load(f)
            return status_data.get('status', 'SKIPPED')
    except Exception as e:
        logger.error(f"Failed to read classification status: {e}")
        return "SKIPPED"

def generate_n_a_plot(output_path: Path):
    """Generate a placeholder plot when classification was skipped."""
    logger.info("Generating N/A sensitivity plot")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.text(0.5, 0.5, 'Sensitivity Analysis Skipped\nNo Independent Proxy Found', 
            horizontalalignment='center', verticalalignment='center',
            transform=ax.transAxes, fontsize=14, color='red')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Threshold')
    ax.set_ylabel('FPR / FNR')
    ax.set_title('Sensitivity Curve (N/A)')
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved N/A plot to {output_path}")

def generate_sensitivity_curve(df: pd.DataFrame, output_path: Path):
    """Generate the sensitivity curve plot from FPR/FNR data."""
    logger.info("Generating sensitivity curve plot")
    
    if 'threshold' not in df.columns or 'FPR' not in df.columns or 'FNR' not in df.columns:
        logger.error("Missing required columns in sensitivity data")
        raise ValueError("Sensitivity data must contain 'threshold', 'FPR', and 'FNR' columns")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot FPR
    ax.plot(df['threshold'], df['FPR'], label='False Positive Rate (FPR)', 
            color='red', linewidth=2, marker='o', markersize=3)
    
    # Plot FNR
    ax.plot(df['threshold'], df['FNR'], label='False Negative Rate (FNR)', 
            color='blue', linewidth=2, marker='s', markersize=3)
    
    # Highlight the optimal threshold region (around 0.5 or optimal F1)
    # Assuming optimal threshold is near where FPR and FNR cross
    crossing_idx = (df['FPR'] - df['FNR']).abs().idxmin()
    optimal_threshold = df.loc[crossing_idx, 'threshold']
    
    ax.axvline(x=optimal_threshold, color='green', linestyle='--', 
               label=f'Optimal Threshold ({optimal_threshold:.2f})', alpha=0.7)
    
    ax.set_xlabel('Classification Threshold')
    ax.set_ylabel('Error Rate')
    ax.set_title('Sensitivity Analysis: FPR vs FNR across Thresholds')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved sensitivity curve to {output_path}")

def main():
    """Main entry point for generating sensitivity curve plot."""
    logger.info("Starting sensitivity curve generation")
    
    # Ensure output directory exists
    output_dir = Path("results/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sensitivity_curve.png"
    
    # Check classification status
    status = check_classification_status()
    logger.info(f"Classification status: {status}")
    
    if status == "SKIPPED":
        logger.info("Classification was skipped, generating N/A plot")
        generate_n_a_plot(output_path)
    else:
        # Load sensitivity results
        df = load_sensitivity_results()
        if df is None:
            logger.error("Sensitivity results not found, cannot generate plot")
            # Generate N/A plot as fallback
            generate_n_a_plot(output_path)
            return
        
        try:
            generate_sensitivity_curve(df, output_path)
            logger.info("Sensitivity curve generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate sensitivity curve: {e}")
            # Generate N/A plot as fallback
            generate_n_a_plot(output_path)

if __name__ == "__main__":
    main()
