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

def load_sensitivity_results() -> pd.DataFrame:
    """Load sensitivity analysis results from CSV."""
    path = Path("data/derived/sensitivity_sweep_results.csv")
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity results file not found at {path}")
    
    df = pd.read_csv(path)
    required_cols = ['threshold', 'fpr', 'fnr', 'accuracy', 'precision', 'recall', 'f1']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Sensitivity results missing required columns: {missing}")
    
    logger.info(f"Loaded sensitivity results with {len(df)} rows")
    return df

def check_classification_status() -> bool:
    """Check if classification was performed (not skipped)."""
    status_path = Path("state/classification_status.yaml")
    if not status_path.exists():
        logger.warning("No classification status file found. Assuming classification was performed.")
        return True
    
    with open(status_path, 'r') as f:
        status_data = yaml.safe_load(f)
    
    if status_data.get('status') == 'SKIPPED':
        logger.info("Classification was skipped (no proxy found).")
        return False
    
    return True

def generate_sensitivity_curve(df: pd.DataFrame, output_path: Path) -> None:
    """Generate the sensitivity curve plot (FPR/FNR vs Threshold)."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot FPR and FNR against threshold
    ax.plot(df['threshold'], df['fpr'], label='False Positive Rate (FPR)', color='red', linewidth=2, marker='o', markersize=4)
    ax.plot(df['threshold'], df['fnr'], label='False Negative Rate (FNR)', color='blue', linewidth=2, marker='s', markersize=4)
    
    # Highlight the optimal threshold (max F1)
    optimal_idx = df['f1'].idxmax()
    optimal_threshold = df.loc[optimal_idx, 'threshold']
    optimal_fpr = df.loc[optimal_idx, 'fpr']
    optimal_fnr = df.loc[optimal_idx, 'fnr']
    
    ax.axvline(x=optimal_threshold, color='green', linestyle='--', linewidth=1.5, label=f'Optimal Threshold ({optimal_threshold:.2f})')
    
    # Mark the optimal point
    ax.scatter([optimal_threshold], [optimal_fpr], color='red', s=100, zorder=5, edgecolors='black')
    ax.scatter([optimal_threshold], [optimal_fnr], color='blue', s=100, zorder=5, edgecolors='black')
    
    # Annotate the optimal point
    ax.annotate(f'FPR: {optimal_fpr:.3f}', xy=(optimal_threshold, optimal_fpr), xytext=(optimal_threshold + 0.1, optimal_fpr),
                arrowprops=dict(facecolor='red', shrink=0.05), color='red', fontsize=9)
    ax.annotate(f'FNR: {optimal_fnr:.3f}', xy=(optimal_threshold, optimal_fnr), xytext=(optimal_threshold + 0.1, optimal_fnr),
                arrowprops=dict(facecolor='blue', shrink=0.05), color='blue', fontsize=9)
    
    ax.set_xlabel('Threshold', fontsize=12)
    ax.set_ylabel('Error Rate', fontsize=12)
    ax.set_title('Sensitivity Analysis: FPR and FNR vs Threshold', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # Save the plot
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Sensitivity curve saved to {output_path}")

def generate_n_a_plot(output_path: Path) -> None:
    """Generate a placeholder plot if classification was skipped."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.text(0.5, 0.5, 'Classification Skipped\n(No Independent Proxy Found)', 
            horizontalalignment='center', verticalalignment='center', 
            fontsize=16, fontweight='bold', transform=ax.transAxes)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"N/A sensitivity plot saved to {output_path}")

def main():
    """Main entry point for generating the sensitivity curve."""
    logger.info("Starting sensitivity curve generation (T046)...")
    
    # Check if classification was performed
    classification_performed = check_classification_status()
    
    if not classification_performed:
        logger.warning("Classification was skipped. Generating N/A plot.")
        output_path = Path("results/figures/sensitivity_curve.png")
        generate_n_a_plot(output_path)
        logger.info("T046 completed (N/A plot generated).")
        return
    
    # Load sensitivity results
    try:
        df = load_sensitivity_results()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load sensitivity results: {e}")
        sys.exit(1)
    
    # Generate the plot
    output_path = Path("results/figures/sensitivity_curve.png")
    generate_sensitivity_curve(df, output_path)
    
    logger.info("T046 completed successfully.")

if __name__ == "__main__":
    main()
