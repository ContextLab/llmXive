"""
Visualization Module.
Generates scatter plots and visual summaries.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from utils import get_logger

logger = get_logger(__name__)

def load_statistics(path: str) -> List[Dict]:
    with open(path, "r") as f:
        return json.load(f)

def load_analysis_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def plot_significant_correlations(
    df: pd.DataFrame, 
    stats: List[Dict], 
    output_dir: str
) -> None:
    """Plot scatter plots for significant correlations."""
    os.makedirs(output_dir, exist_ok=True)
    
    for stat in stats:
        if stat.get("p_value", 1.0) < 0.05:
            pred = stat["predictor"]
            out = stat["outcome"]
            if pred in df.columns and out in df.columns:
                clean = df[[pred, out]].dropna()
                plt.figure()
                plt.scatter(clean[pred], clean[out])
                plt.title(f"{pred} vs {out} (p={stat['p_value']:.3f})")
                plt.xlabel(pred)
                plt.ylabel(out)
                path = os.path.join(output_dir, f"{pred}_vs_{out}.png")
                plt.savefig(path)
                plt.close()
                logger.info(f"Saved plot: {path}")

def generate_visual_summary_report(
    stats_path: str, 
    output_path: str
) -> None:
    """Generate a text report summarizing findings."""
    stats = load_statistics(stats_path)
    with open(output_path, "w") as f:
        f.write("# Visual Summary Report\n\n")
        f.write("## Significant Correlations\n\n")
        for s in stats:
            if s.get("p_value", 1.0) < 0.05:
                f.write(f"- {s['metric_pair']}: r={s['pearson_r']:.3f}, p={s['p_value']:.3f}\n")
        f.write("\n## Methodology Notes\n")
        f.write("- All findings are associational.\n")
        f.write("- Alpha threshold of 0.05 used as community standard.\n")

def main() -> None:
    """Main visualization execution."""
    stats = load_statistics("results/statistics/statistics.json")
    df = load_analysis_data("data/processed/final_analysis_data.csv")
    
    plot_significant_correlations(df, stats, "results/plots")
    generate_visual_summary_report("results/statistics/statistics.json", "results/report.md")

if __name__ == "__main__":
    main()
