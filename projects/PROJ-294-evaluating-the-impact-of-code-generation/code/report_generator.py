import os
import sys
import json
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from typing import Dict, Any, List
from utils import setup_logging, get_logger, set_task_id, get_task_id

def ensure_figures_dir():
    """Ensure results/figures/ directory exists."""
    path = "results/figures"
    os.makedirs(path, exist_ok=True)
    return path

def load_metrics_data() -> List[Dict[str, Any]]:
    path = "data/analysis/metrics.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metrics file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

def load_statistical_results() -> Dict[str, Any]:
    path = "data/analysis/statistical_results.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def extract_metric_values(metrics: List[Dict[str, Any]], metric_name: str) -> Dict[str, List[float]]:
    """Extract metric values by source type."""
    result = {"human": [], "codegen": []}
    for m in metrics:
        if m["source_type"] in result:
            result[m["source_type"]].append(m.get(metric_name, 0))
    return result

def calculate_summary_stats(values: List[float]) -> Dict[str, float]:
    """Calculate summary statistics."""
    if not values:
        return {"mean": 0, "std": 0, "min": 0, "max": 0}
    return {
        "mean": sum(values) / len(values),
        "std": (sum((x - sum(values)/len(values))**2 for x in values) / len(values))**0.5,
        "min": min(values),
        "max": max(values)
    }

def plot_histogram(values: Dict[str, List[float]], metric_name: str, output_path: str):
    """Plot histogram for a metric."""
    plt.figure(figsize=(10, 6))
    for source, vals in values.items():
        if vals:
            plt.hist(vals, alpha=0.5, label=source, bins=20)
    plt.title(f"Histogram of {metric_name}")
    plt.xlabel(metric_name)
    plt.ylabel("Frequency")
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def plot_boxplot(values: Dict[str, List[float]], metric_name: str, output_path: str):
    """Plot boxplot for a metric."""
    plt.figure(figsize=(10, 6))
    data = [v for v in values.values() if v]
    plt.boxplot(data, labels=list(values.keys()))
    plt.title(f"Boxplot of {metric_name}")
    plt.ylabel(metric_name)
    plt.savefig(output_path)
    plt.close()

def generate_all_plots(metrics: List[Dict[str, Any]]):
    """Generate all plots."""
    figures_dir = ensure_figures_dir()
    metrics_to_plot = ["cyclomatic_complexity", "halstead_volume", "branch_coverage_potential", "pass_rate"]
    
    for metric in metrics_to_plot:
        values = extract_metric_values(metrics, metric)
        plot_histogram(values, metric, os.path.join(figures_dir, f"{metric}_hist.png"))
        plot_boxplot(values, metric, os.path.join(figures_dir, f"{metric}_boxplot.png"))

def format_sensitivity_comparison(results: Dict[str, Any]) -> str:
    """Format sensitivity comparison results."""
    if not results:
        return "No sensitivity data available."
    return json.dumps(results, indent=2)

def generate_markdown_report(metrics: List[Dict[str, Any]], stats: Dict[str, Any]):
    """Generate the final Markdown report."""
    report_path = "results_report.md"
    with open(report_path, "w") as f:
        f.write("# Research Report\n\n")
        f.write("## Metrics Summary\n\n")
        f.write(f"Total samples: {len(metrics)}\n\n")
        
        # Add statistical results
        f.write("## Statistical Analysis\n\n")
        if stats:
            f.write(f"Power: {stats.get('power', 0):.2%}\n")
            f.write(f"Sample size: {stats.get('sample_size', 0)}\n")
        
        f.write("\n## Figures\n\n")
        f.write("See `results/figures/` for generated plots.\n")

def main():
    logger = setup_logging(task_id="T030")
    logger.info("Starting Report Generation (T030)")
    
    try:
        metrics = load_metrics_data()
        stats = load_statistical_results()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    generate_all_plots(metrics)
    generate_markdown_report(metrics, stats)
    
    logger.info("Report generation completed.")

if __name__ == "__main__":
    main()
