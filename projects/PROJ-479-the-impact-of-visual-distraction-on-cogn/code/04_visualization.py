"""
Visualization Module.
Generates plots and visual summaries for the analysis.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any

from utils import get_logger

logger = get_logger(__name__)

def load_statistics(path: str) -> List[Dict[str, Any]]:
    """Load statistics from JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Statistics file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

def load_analysis_data(path: str) -> pd.DataFrame:
    """Load analysis data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Analysis data not found: {path}")
    return pd.read_csv(path)

def plot_significant_correlations(df: pd.DataFrame, stats: List[Dict[str, Any]], output_dir: str) -> None:
    """Plot scatter plots for significant correlations."""
    os.makedirs(output_dir, exist_ok=True)
    
    significant = [s for s in stats if s.get("p_value", 1.0) < 0.05]
    
    if not significant:
        logger.info("No significant correlations to plot.")
        return

    for stat in significant:
        pred = stat["predictor"]
        out = stat["outcome"]
        r = stat["pearson_r"]
        p = stat["p_value"]
        
        # Filter NaNs
        clean = df[[pred, out]].dropna()
        if len(clean) < 3:
            continue
        
        plt.figure(figsize=(8, 6))
        plt.scatter(clean[pred], clean[out], alpha=0.6, edgecolors='w', linewidth=0.5)
        
        # Add trend line
        m, b = np.polyfit(clean[pred], clean[out], 1)
        plt.plot(clean[pred], m*clean[pred] + b, color='red', linewidth=2)
        
        plt.title(f"{pred} vs {out}\n(r={r:.3f}, p={p:.3f})")
        plt.xlabel(pred)
        plt.ylabel(out)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        filename = f"{pred}_vs_{out}.png"
        path = os.path.join(output_dir, filename)
        plt.savefig(path, dpi=150)
        plt.close()
        logger.info(f"Saved plot: {path}")

def generate_visual_summary_report(stats: List[Dict[str, Any]], output_path: str) -> None:
    """Generate a text summary of the visual analysis."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    significant_count = sum(1 for s in stats if s.get("p_value", 1.0) < 0.05)
    total_count = len(stats)
    
    with open(output_path, "w") as f:
        f.write("# Visual Analysis Summary\n\n")
        f.write(f"Total tests performed: {total_count}\n")
        f.write(f"Significant correlations (p < 0.05): {significant_count}\n\n")
        
        f.write("## Significant Pairs\n")
        for s in stats:
            if s.get("p_value", 1.0) < 0.05:
                f.write(f"- {s['predictor']} vs {s['outcome']}: r={s['pearson_r']:.3f}, p={s['p_value']:.3f}\n")
        
        f.write("\n## Non-Significant Pairs\n")
        for s in stats:
            if s.get("p_value", 1.0) >= 0.05:
                f.write(f"- {s['predictor']} vs {s['outcome']}: r={s['pearson_r']:.3f}, p={s['p_value']:.3f}\n")

def main() -> None:
    """Main visualization execution."""
    stats_path = "results/statistics/statistics.json"
    data_path = "data/processed/final_analysis_data.csv"
    plots_dir = "results/plots"
    report_path = "results/plots/visual_summary.md"
    
    try:
        stats = load_statistics(stats_path)
        df = load_analysis_data(data_path)
        
        plot_significant_correlations(df, stats, plots_dir)
        generate_visual_summary_report(stats, report_path)
        
        logger.info("Visualization complete.")
    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise

if __name__ == "__main__":
    main()