import os
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Add code directory to path
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from config import METRICS_CSV_PATH, REPORTS_FIGURES_DIR
from logging_setup import setup_logging

def plot_correlation_scatter(df: pd.DataFrame, metric_x: str, metric_y: str, output_path: str):
    """
    Generate a scatter plot with regression line and annotations.
    """
    plt.figure(figsize=(10, 8))
    sns.set(style="whitegrid")
    
    # Plot
    sns.regplot(x=metric_x, y=metric_y, data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'red'})
    
    # Calculate stats for annotation
    r, p = stats.pearsonr(df[metric_x], df[metric_y])
    n = len(df)
    
    # Annotate
    annotation = f"r = {r:.3f}\np = {p:.3e}\nn = {n}"
    plt.annotate(annotation, xy=(0.05, 0.95), xycoords='axes fraction', 
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.title(f"{metric_x.replace('_', ' ').title()} vs {metric_y.replace('_', ' ').title()}")
    plt.xlabel(metric_x.replace('_', ' ').title())
    plt.ylabel(metric_y.replace('_', ' ').title())
    
    plt.savefig(output_path, dpi=300)
    plt.close()

def main():
    """
    Main entry point for visualization.
    """
    logger = setup_logging()
    logger.info("Starting visualization...")
    
    if not os.path.exists(METRICS_CSV_PATH):
        logger.error(f"Metrics file not found: {METRICS_CSV_PATH}")
        return False
    
    df = pd.read_csv(METRICS_CSV_PATH)
    
    pairs = [
        ("entropy", "sa_score"),
        ("entropy", "qed"),
        ("lz_complexity", "sa_score"),
        ("lz_complexity", "qed")
    ]
    
    for x, y in pairs:
        if x not in df.columns or y not in df.columns:
            continue
        
        safe_x = x.replace(" ", "_").replace("-", "_")
        safe_y = y.replace(" ", "_").replace("-", "_")
        filename = f"scatter_{safe_x}_vs_{safe_y}.png"
        output_path = str(REPORTS_FIGURES_DIR / filename)
        
        logger.info(f"Generating plot: {filename}")
        plot_correlation_scatter(df, x, y, output_path)
    
    logger.info(f"Visualization complete. Figures saved to {REPORTS_FIGURES_DIR}")
    return True

if __name__ == "__main__":
    main()