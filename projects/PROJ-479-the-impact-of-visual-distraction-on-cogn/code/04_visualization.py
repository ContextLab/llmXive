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
from typing import List, Dict, Any, Tuple

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
    """Plot scatter plots for significant correlations with trend lines."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter for significant correlations (p < 0.05)
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
            logger.warning(f"Insufficient data points for {pred} vs {out}. Skipping plot.")
            continue
        
        plt.figure(figsize=(8, 6))
        plt.scatter(clean[pred], clean[out], alpha=0.6, edgecolors='w', linewidth=0.5, label='Data Points')
        
        # Add trend line (linear regression fit)
        m, b = np.polyfit(clean[pred], clean[out], 1)
        x_line = np.linspace(clean[pred].min(), clean[pred].max(), 100)
        y_line = m * x_line + b
        plt.plot(x_line, y_line, color='red', linewidth=2, label=f'Trend Line (r={r:.3f})')
        
        plt.title(f"{pred} vs {out}\n(r={r:.3f}, p={p:.3f})")
        plt.xlabel(pred)
        plt.ylabel(out)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        filename = f"{pred}_vs_{out}.png"
        path = os.path.join(output_dir, filename)
        plt.savefig(path, dpi=150)
        plt.close()
        logger.info(f"Saved plot: {path}")

def plot_bootstrap_overlay(df: pd.DataFrame, stats: List[Dict[str, Any]], output_dir: str) -> None:
    """
    Generate a summary visualization overlaying bootstrap confidence intervals
    on the primary scatter plots.
    
    Chart Type: Scatter plot with error bars (95% CI) representing the bootstrap
    distribution of the correlation coefficient.
    
    Output: results/plots/bootstrap_overlay.png
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter for significant correlations (p < 0.05) to display
    significant = [s for s in stats if s.get("p_value", 1.0) < 0.05]
    
    if not significant:
        logger.warning("No significant correlations found to generate bootstrap overlay.")
        # Create a placeholder or empty plot if no data, but task implies plotting existing stats
        # If no stats, we can't plot. Return early.
        return

    # Prepare data for the summary plot
    # We will create a scatter plot where X-axis is the predictor metric, Y-axis is the outcome.
    # However, to overlay CIs, we usually plot the correlation strength or the regression line
    # with a confidence band.
    # Per task: "Scatter plot with error bars (95% CI)".
    # Interpretation: Plot the data points, and overlay the regression line with a confidence interval band,
    # or plot the bootstrap distribution of the correlation coefficient if multiple pairs are shown.
    # Given "summary visualization", we will plot the combined data or a representative pair.
    # Let's plot the first significant pair as a representative example, or aggregate if possible.
    # To satisfy "summary", we will plot the first significant pair found in the stats.
    
    stat = significant[0]
    pred = stat["predictor"]
    out = stat["outcome"]
    r = stat["pearson_r"]
    p = stat["p_value"]
    
    # Check for bootstrap CI in stats (from T041/T044)
    ci_low = stat.get("ci_low")
    ci_high = stat.get("ci_high")
    
    if ci_low is None or ci_high is None:
        logger.warning(f"Bootstrap CI not found for {pred} vs {out}. Generating plot without error bars.")
        # Fallback to standard plot if CI missing
        clean = df[[pred, out]].dropna()
        if len(clean) < 3:
            logger.warning(f"Insufficient data points for {pred} vs {out}.")
            return
        
        plt.figure(figsize=(10, 8))
        plt.scatter(clean[pred], clean[out], alpha=0.6, edgecolors='w', linewidth=0.5, label='Data Points')
        m, b = np.polyfit(clean[pred], clean[out], 1)
        x_line = np.linspace(clean[pred].min(), clean[pred].max(), 100)
        y_line = m * x_line + b
        plt.plot(x_line, y_line, color='red', linewidth=2, label=f'Trend Line (r={r:.3f})')
        plt.title(f"Bootstrap Overlay: {pred} vs {out}\n(r={r:.3f}, p={p:.3f}) - No CI Data")
        plt.xlabel(pred)
        plt.ylabel(out)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        path = os.path.join(output_dir, "bootstrap_overlay.png")
        plt.savefig(path, dpi=150)
        plt.close()
        logger.info(f"Saved bootstrap overlay (no CI): {path}")
        return

    # Extract clean data
    clean = df[[pred, out]].dropna()
    if len(clean) < 3:
        logger.warning(f"Insufficient data points for {pred} vs {out}.")
        return

    plt.figure(figsize=(10, 8))
    
    # Scatter plot of actual data
    plt.scatter(clean[pred], clean[out], alpha=0.5, edgecolors='black', linewidth=0.5, label='Observed Data')
    
    # Regression line
    m, b = np.polyfit(clean[pred], clean[out], 1)
    x_line = np.linspace(clean[pred].min(), clean[pred].max(), 100)
    y_line = m * x_line + b
    plt.plot(x_line, y_line, color='blue', linewidth=2, label=f'Fit (r={r:.3f})')
    
    # Bootstrap Confidence Interval Band (95%)
    # We assume the bootstrap was done on the correlation, but to plot a band on the scatter:
    # We simulate the uncertainty by drawing lines based on the slope uncertainty if available,
    # or simply annotate the plot with the CI of the correlation coefficient as a text box/legend.
    # However, "Scatter plot with error bars" usually implies error bars on the points or the line.
    # Given we have CI for the *correlation* (r), not the prediction interval, we will:
    # 1. Plot the main fit.
    # 2. Add a text annotation or a secondary plot element showing the CI.
    # To make it a "Scatter plot with error bars", we can plot the correlation coefficient itself
    # if we had multiple samples, but we have one dataset.
    # Alternative interpretation: Plot the regression line with a shaded confidence interval band
    # derived from the bootstrap distribution of the slope/intercept?
    # The task says "overlay bootstrap confidence intervals".
    # Let's create a plot that shows the data, the fit, and annotates the CI clearly.
    # If we interpret "error bars" as the CI of the correlation coefficient displayed on the plot:
    
    # We will create a secondary axis or a text box to display the CI.
    # But to strictly follow "Scatter plot with error bars", we can plot the correlation
    # value as a point with error bars if we had multiple estimates.
    # Since we have one estimate with a CI, we can plot the regression line and add a shaded region
    # representing the uncertainty in the prediction if we assume the CI applies to the slope.
    # However, the most accurate representation of "Bootstrap CI on Scatter" is to show the
    # distribution of regression lines if we had them, or simply annotate.
    
    # Let's try to plot the CI as a shaded region around the regression line, assuming
    # the CI in stats refers to the correlation, but we can approximate the slope uncertainty.
    # Actually, a better approach for "summary visualization" of bootstrap results:
    # Plot the correlation coefficient (r) on a separate axis or as a text box with error bars.
    # But the task says "on the primary scatter plots".
    
    # Let's plot the scatter, the fit, and add a text box with the CI.
    # To make it look like "error bars", we can plot the correlation coefficient on a dummy axis
    # or just use the standard error bar function on a single point if we force it.
    # Let's do this: Plot the data, the fit, and add a legend entry with the CI range.
    
    # To satisfy "error bars", we can plot the correlation coefficient as a point with error bars
    # on a secondary plot, but the task says "on the primary scatter plots".
    # Let's assume the user wants to see the uncertainty in the relationship.
    # We will plot the regression line and a confidence band (95%) calculated from the bootstrap
    # if we had the raw bootstrap samples. Since we only have the summary (ci_low, ci_high),
    # we will annotate the plot.
    
    # Re-reading: "Scatter plot with error bars (95% CI)".
    # Maybe it means plotting the mean values with error bars if binned? No, it says "on scatter plots".
    # Let's interpret this as: Plot the data, and overlay the regression line, and visualize the CI.
    # Since we only have the CI for 'r', not the prediction interval, we will add a text annotation
    # that is styled to look like an error bar caption.
    
    # Actually, we can plot the correlation coefficient itself as a point with error bars on a separate
    # subplot or inset. But "on the primary scatter plots" suggests the main plot.
    # Let's create a plot with the scatter and a text box with the CI, and add a visual element.
    
    # Let's try a different interpretation: The bootstrap was run on the correlation.
    # We can plot the correlation coefficient (r) on a separate axis (e.g. a dot plot) with error bars.
    # But the task says "on the primary scatter plots".
    # Okay, let's plot the scatter, the fit, and add a legend that includes the CI.
    # And we will add a text box with the CI range.
    
    # To strictly follow "error bars", we can plot the correlation coefficient as a point
    # with error bars on a secondary axis (e.g. right y-axis) or as an inset.
    # Let's do an inset plot for the correlation coefficient with error bars.
    
    ax = plt.gca()
    inset_ax = fig = plt.gcf()
    # Create an inset axis
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    try:
        ax_inset = inset_axes(ax, width="30%", height="30%", loc='upper right')
    except:
        # Fallback if inset_axes not available (older matplotlib)
        ax_inset = fig.add_axes([0.6, 0.6, 0.3, 0.3])
    
    ax_inset.set_xlim(-0.1, 1.1)
    ax_inset.set_ylim(-1.1, 1.1)
    ax_inset.axis('off')
    ax_inset.text(0.5, 0.5, f'r = {r:.3f}\n95% CI: [{ci_low:.3f}, {ci_high:.3f}]', 
                 ha='center', va='center', fontsize=10, 
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    # Draw error bar manually on the inset?
    # We can plot a horizontal line for the CI and a vertical line for the point.
    ax_inset.plot([ci_low, ci_high], [0.5, 0.5], color='black', linewidth=2)
    ax_inset.plot([r, r], [0.4, 0.6], color='black', linewidth=2)
    
    plt.title(f"Bootstrap Overlay: {pred} vs {out}\n(r={r:.3f}, p={p:.3f})")
    plt.xlabel(pred)
    plt.ylabel(out)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    filename = "bootstrap_overlay.png"
    path = os.path.join(output_dir, filename)
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved bootstrap overlay with CI: {path}")

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
        plot_bootstrap_overlay(df, stats, plots_dir)
        generate_visual_summary_report(stats, report_path)
        
        logger.info("Visualization complete.")
    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise

if __name__ == "__main__":
    main()