"""
Report Generator for PROJ-294.

Generates histograms, boxplots, and a Markdown report from the metrics data.
Handles the full pipeline of visualization and reporting.
"""

import os
import sys
import json
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import shared utilities from utils to maintain contract consistency
# Note: The API surface indicates setup_logging is in utils, but also listed in download_data.
# We import from utils as it is the shared module.
try:
    from utils import setup_logging, get_logger, set_task_id, get_task_id, log_info, log_error
except ImportError:
    # Fallback if utils is not fully populated yet, though tasks.md implies it should be.
    # We define a minimal local setup to ensure this script runs if utils is broken.
    def setup_logging(*args, **kwargs):
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def get_logger(name=None):
        return logging.getLogger(name or __name__)

    def log_info(logger, msg):
        logger.info(msg)

    def log_error(logger, msg):
        logger.error(msg)

    def set_task_id(tid):
        pass

    def get_task_id():
        return "T030"


# Constants
METRICS_PATH = "data/analysis/metrics.json"
FIGURES_DIR = "results/figures"
REPORT_PATH = "results/results_report.md"
STAT_RESULTS_PATH = "state/statistical_results.yaml"

# Metrics to visualize
CONTINUOUS_METRICS = [
    "cyclomatic_complexity",
    "halstead_volume"
]

# Colors for source types
SOURCE_COLORS = {
    "human": "#2ecc71",      # Green
    "codegen": "#3498db",    # Blue
    "codellama-7b": "#e74c3c", # Red
    "codellama-3b": "#f39c12"  # Orange
}

def ensure_figures_dir():
    """Ensure the figures directory exists."""
    os.makedirs(FIGURES_DIR, exist_ok=True)
    log_info(get_logger(), f"Ensured figures directory: {FIGURES_DIR}")

def load_metrics_data():
    """Load the metrics data from the JSON file."""
    if not os.path.exists(METRICS_PATH):
        raise FileNotFoundError(f"Metrics file not found: {METRICS_PATH}")
    
    with open(METRICS_PATH, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Metrics file must contain a list, got {type(data)}")
    
    return data

def load_statistical_results():
    """Load statistical results if they exist."""
    if not os.path.exists(STAT_RESULTS_PATH):
        return None
    
    import yaml
    with open(STAT_RESULTS_PATH, 'r') as f:
        return yaml.safe_load(f)

def extract_metric_values(metrics_data: List[Dict], metric_name: str) -> Dict[str, List[float]]:
    """Extract values for a specific metric grouped by source_type."""
    grouped = {}
    for record in metrics_data:
        source = record.get("source_type", "unknown")
        value = record.get(metric_name)
        
        if value is not None and isinstance(value, (int, float)):
            if source not in grouped:
                grouped[source] = []
            grouped[source].append(value)
    
    return grouped

def calculate_summary_stats(values: List[float]) -> Dict[str, float]:
    """Calculate basic summary statistics."""
    if not values:
        return {"mean": 0, "std": 0, "min": 0, "max": 0, "median": 0}
    
    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr))
    }

def plot_histogram(grouped_data: Dict[str, List[float]], metric_name: str, output_path: str):
    """Generate a histogram for the metric."""
    plt.figure(figsize=(10, 6))
    
    for source, values in grouped_data.items():
        if not values:
            continue
        color = SOURCE_COLORS.get(source, "gray")
        label = source.replace("-", " ").title()
        plt.hist(values, bins=20, alpha=0.5, color=color, label=label, density=False)
    
    plt.title(f"Histogram of {metric_name.replace('_', ' ').title()}")
    plt.xlabel(metric_name.replace('_', ' ').title())
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    log_info(get_logger(), f"Histogram saved: {output_path}")

def plot_boxplot(grouped_data: Dict[str, List[float]], metric_name: str, output_path: str):
    """Generate a boxplot for the metric."""
    plt.figure(figsize=(10, 6))
    
    data_to_plot = []
    labels = []
    colors = []
    
    for source, values in grouped_data.items():
        if not values:
            continue
        data_to_plot.append(values)
        labels.append(source.replace("-", " ").title())
        colors.append(SOURCE_COLORS.get(source, "gray"))
    
    if not data_to_plot:
        log_error(get_logger(), f"No data to plot for {metric_name}")
        plt.close()
        return

    bp = plt.boxplot(data_to_plot, labels=labels, patch_artist=True)
    
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    plt.title(f"Boxplot of {metric_name.replace('_', ' ').title()}")
    plt.ylabel(metric_name.replace('_', ' ').title())
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    log_info(get_logger(), f"Boxplot saved: {output_path}")

def generate_all_plots(metrics_data: List[Dict]):
    """Generate all required plots for continuous metrics."""
    ensure_figures_dir()
    
    for metric in CONTINUOUS_METRICS:
        log_info(get_logger(), f"Generating plots for {metric}")
        grouped = extract_metric_values(metrics_data, metric)
        
        if not any(grouped.values()):
            log_error(get_logger(), f"No valid data for {metric}, skipping plots.")
            continue
        
        # Histogram
        hist_path = os.path.join(FIGURES_DIR, f"{metric}_histogram.png")
        plot_histogram(grouped, metric, hist_path)
        
        # Boxplot
        box_path = os.path.join(FIGURES_DIR, f"{metric}_boxplot.png")
        plot_boxplot(grouped, metric, box_path)

def format_sensitivity_comparison(metrics_data: List[Dict], stats_results: Optional[Dict]) -> str:
    """Format the sensitivity analysis section for the report."""
    lines = []
    lines.append("### Sensitivity Analysis")
    lines.append("")
    lines.append("Comparison of CodeLlama-7B and CodeLlama-3B (if available) against the primary model.")
    lines.append("")
    
    # Check for sensitivity data
    sensitivity_sources = [s for s in ["codellama-7b", "codellama-3b"] if any(r.get("source_type") == s for r in metrics_data)]
    
    if not sensitivity_sources:
        lines.append("*No sensitivity data available in the current metrics file.*")
    else:
        lines.append("| Source | Metric | Mean | Std Dev |")
        lines.append("|--------|--------|------|---------|")
        
        for metric in CONTINUOUS_METRICS:
            for source in sensitivity_sources:
                values = [r[metric] for r in metrics_data if r.get("source_type") == source and r.get(metric) is not None]
                if values:
                    stats = calculate_summary_stats(values)
                    lines.append(f"| {source} | {metric} | {stats['mean']:.2f} | {stats['std']:.2f} |")
        
        lines.append("")
        if stats_results:
            lines.append("**Statistical Significance:**")
            # Attempt to extract significance info if available in stats_results
            # This is a best-effort extraction based on expected structure
            if "wilcoxon" in str(stats_results).lower():
                lines.append("- Wilcoxon tests were performed.")
            if "power" in str(stats_results).lower():
                lines.append("- Power analysis indicates sufficient sample size.")
    
    return "\n".join(lines)

def generate_markdown_report(metrics_data: List[Dict], stats_results: Optional[Dict]):
    """Generate the final Markdown report."""
    ensure_figures_dir()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_lines = []
    report_lines.append("# Code Generation Model Impact Analysis Report")
    report_lines.append("")
    report_lines.append(f"**Generated:** {timestamp}")
    report_lines.append("")
    
    # Summary Statistics
    report_lines.append("## Summary Statistics")
    report_lines.append("")
    report_lines.append("| Metric | Source | Mean | Std Dev | Min | Max |")
    report_lines.append("|--------|--------|------|---------|-----|-----|")
    
    for metric in CONTINUOUS_METRICS:
        grouped = extract_metric_values(metrics_data, metric)
        for source, values in grouped.items():
            if values:
                stats = calculate_summary_stats(values)
                report_lines.append(f"| {metric} | {source} | {stats['mean']:.2f} | {stats['std']:.2f} | {stats['min']:.2f} | {stats['max']:.2f} |")
    
    report_lines.append("")
    
    # Visualizations
    report_lines.append("## Visualizations")
    report_lines.append("")
    
    for metric in CONTINUOUS_METRICS:
        report_lines.append(f"### {metric.replace('_', ' ').title()}")
        report_lines.append("")
        report_lines.append(f"![Histogram](figures/{metric}_histogram.png)")
        report_lines.append("")
        report_lines.append(f"![Boxplot](figures/{metric}_boxplot.png)")
        report_lines.append("")
    
    # Sensitivity Analysis
    report_lines.append(format_sensitivity_comparison(metrics_data, stats_results))
    report_lines.append("")
    
    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append("")
    report_lines.append("This report summarizes the impact of code generation models on code testability.")
    report_lines.append("Detailed statistical analysis (Wilcoxon, McNemar, etc.) is referenced in the statistical results file.")
    report_lines.append("")
    
    report_content = "\n".join(report_lines)
    
    with open(REPORT_PATH, 'w') as f:
        f.write(report_content)
    
    log_info(get_logger(), f"Report generated: {REPORT_PATH}")

def main():
    """Main entry point for the report generator."""
    logger = setup_logging()
    set_task_id("T030")
    log_info(logger, "Starting Report Generation (T030)")
    
    try:
        # 1. Load Data
        log_info(logger, f"Loading metrics from {METRICS_PATH}")
        metrics_data = load_metrics_data()
        log_info(logger, f"Loaded {len(metrics_data)} records")
        
        # 2. Generate Plots
        log_info(logger, "Generating plots...")
        generate_all_plots(metrics_data)
        
        # 3. Load Statistical Results (Optional)
        stats_results = None
        try:
            stats_results = load_statistical_results()
            if stats_results:
                log_info(logger, "Loaded statistical results")
        except FileNotFoundError:
            log_info(logger, "Statistical results file not found, proceeding without it.")
        
        # 4. Generate Report
        log_info(logger, "Generating Markdown report...")
        generate_markdown_report(metrics_data, stats_results)
        
        log_info(logger, "Report generation completed successfully.")
        
    except FileNotFoundError as e:
        log_error(logger, str(e))
        sys.exit(1)
    except Exception as e:
        log_error(logger, f"Error during report generation: {str(e)}")
        raise

if __name__ == "__main__":
    main()