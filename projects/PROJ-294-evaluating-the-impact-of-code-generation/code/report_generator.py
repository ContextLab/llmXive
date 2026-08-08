"""
Report Generator Module (T030, T031)

Generates visualizations and Markdown report.
"""
import os
import sys
import json
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import setup_logging, get_logger, set_task_id, get_task_id, log_info, log_error

TASK_ID = "T030"

def ensure_figures_dir():
    os.makedirs("results/figures", exist_ok=True)

def load_metrics_data(file_path: str = "data/analysis/metrics.json") -> List[Dict[str, Any]]:
    """Load metrics data."""
    with open(file_path, 'r') as f:
        return json.load(f)

def load_statistical_results(file_path: str = "state/statistical_results.json") -> Dict[str, Any]:
    """Load statistical results."""
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_metric_values(metrics: List[Dict[str, Any]], metric_name: str) -> Dict[str, List[float]]:
    """Extract metric values grouped by source type."""
    groups = {}
    for m in metrics:
        source = m['source_type']
        val = m.get(metric_name)
        if val is not None:
            if source not in groups:
                groups[source] = []
            groups[source].append(val)
    return groups

def calculate_summary_stats(values: List[float]) -> Dict[str, float]:
    """Calculate summary statistics."""
    if not values:
        return {}
    return {
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values)
    }

def plot_histogram(values: List[float], title: str, output_path: str):
    """Plot histogram."""
    plt.figure(figsize=(10, 6))
    plt.hist(values, bins=20, alpha=0.7, edgecolor='black')
    plt.title(title)
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.savefig(output_path)
    plt.close()

def plot_boxplot(groups: Dict[str, List[float]], title: str, output_path: str):
    """Plot boxplot."""
    plt.figure(figsize=(10, 6))
    data = [groups[k] for k in sorted(groups.keys())]
    labels = sorted(groups.keys())
    plt.boxplot(data, labels=labels)
    plt.title(title)
    plt.ylabel("Value")
    plt.savefig(output_path)
    plt.close()

def generate_all_plots(metrics: List[Dict[str, Any]]):
    """Generate all required plots."""
    ensure_figures_dir()
    
    for metric in ['cyclomatic_complexity', 'halstead_volume']:
        groups = extract_metric_values(metrics, metric)
        for source, vals in groups.items():
            plot_histogram(vals, f"{metric} - {source}", f"results/figures/{metric}_{source}.png")
        
        if len(groups) > 1:
            plot_boxplot(groups, f"{metric} Comparison", f"results/figures/{metric}_comparison.png")

def format_sensitivity_comparison(results: Dict[str, Any]) -> str:
    """Format sensitivity comparison for report."""
    return json.dumps(results, indent=2)

def generate_markdown_report(metrics: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
    """Generate Markdown report."""
    report = "# Research Report\n\n"
    report += "## Summary\n\n"
    report += f"Total samples: {len(metrics)}\n\n"
    
    report += "## Statistical Results\n\n"
    report += "```json\n"
    report += json.dumps(stats, indent=2)
    report += "\n```\n"
    
    report += "## Figures\n\n"
    report += "See `results/figures/` directory.\n"
    
    return report

def main():
    """Main entry point for T030-T031."""
    logger = setup_logging(task_id=TASK_ID)
    
    metrics = load_metrics_data()
    stats = load_statistical_results()
    
    generate_all_plots(metrics)
    report = generate_markdown_report(metrics, stats)
    
    with open("results_report.md", 'w') as f:
        f.write(report)
    
    log_info(TASK_ID, "Report generated.")

if __name__ == "__main__":
    main()
