import os
import json
import logging
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import numpy as np
from jinja2 import Template

from utils import get_logger, set_task_id, get_task_id, get_timestamp

# Constants for paths
DATA_ANALYSIS_DIR = "data/analysis"
RESULTS_FIGURES_DIR = "results/figures"
RESULTS_REPORT_FILE = "results_report.md"
METRICS_FILE = "metrics.json"
STAT_RESULTS_FILE = "statistical_results.json"

def ensure_figures_dir():
    """Ensure the figures directory exists."""
    os.makedirs(RESULTS_FIGURES_DIR, exist_ok=True)
    logging.info(f"Ensured figures directory exists: {RESULTS_FIGURES_DIR}")

def load_metrics_data():
    """Load the main metrics JSON file."""
    metrics_path = os.path.join(DATA_ANALYSIS_DIR, METRICS_FILE)
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_statistical_results():
    """Load the statistical analysis results JSON file."""
    stat_path = os.path.join(DATA_ANALYSIS_DIR, STAT_RESULTS_FILE)
    if not os.path.exists(stat_path):
        logging.warning(f"Statistical results file not found: {stat_path}. Skipping statistical tables in report.")
        return None
    with open(stat_path, 'r') as f:
        return json.load(f)

def extract_metric_values(metrics_data: Dict, metric_name: str) -> List[float]:
    """Extract a list of values for a specific metric from the metrics data."""
    values = []
    for item in metrics_data:
        if metric_name in item and item[metric_name] is not None and item[metric_name] != '[deferred]':
            try:
                values.append(float(item[metric_name]))
            except (ValueError, TypeError):
                pass
    return values

def calculate_summary_stats(values: List[float]) -> Dict[str, float]:
    """Calculate basic summary statistics for a list of values."""
    if not values:
        return {"mean": 0, "std": 0, "min": 0, "max": 0, "median": 0, "count": 0}
    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
        "count": len(values)
    }

def plot_histogram(values: List[float], title: str, filename: str, xlabel: str = "Value"):
    """Generate a histogram plot."""
    plt.figure(figsize=(10, 6))
    plt.hist(values, bins=20, edgecolor='black', alpha=0.7)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_FIGURES_DIR, filename))
    plt.close()
    logging.info(f"Saved histogram: {filename}")

def plot_boxplot(values: List[float], title: str, filename: str, xlabel: str = "Metric"):
    """Generate a boxplot."""
    plt.figure(figsize=(8, 6))
    plt.boxplot(values, vert=True, patch_artist=True)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Value")
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_FIGURES_DIR, filename))
    plt.close()
    logging.info(f"Saved boxplot: {filename}")

def generate_all_plots(metrics_data: Dict):
    """Generate all required plots for the report."""
    ensure_figures_dir()
    metrics_to_plot = [
        ("cyclomatic_complexity", "Cyclomatic Complexity Distribution", "hist_complexity.png", "Boxplot Complex"),
        ("halstead_volume", "Halstead Volume Distribution", "hist_halstead.png", "Boxplot Halstead"),
        # Branch coverage is percentage, so 0-100
        ("branch_coverage_pct", "Branch Coverage Distribution", "hist_coverage.png", "Boxplot Coverage")
    ]

    for metric_key, hist_title, hist_file, box_title in metrics_to_plot:
        values = extract_metric_values(metrics_data, metric_key)
        if not values:
            logging.warning(f"No data found for {metric_key}, skipping plots.")
            continue

        plot_histogram(values, hist_title, hist_file)
        # Re-use boxplot function but with specific title
        plot_boxplot(values, box_title, f"box_{hist_file.replace('.png', '.png').replace('hist_', '')}", metric_key)

def format_sensitivity_comparison(sensitivity_data: List[Dict]) -> str:
    """
    Format sensitivity analysis data into a Markdown table and summary.
    Expects a list of dicts where each dict has 'model_type', 'metric_name', 'mean', 'std', 'count'.
    """
    if not sensitivity_data:
        return "No sensitivity analysis data available."

    # Group by model type for easier display
    models = {}
    for item in sensitivity_data:
        model = item['model_type']
        if model not in models:
            models[model] = {}
        models[model][item['metric_name']] = {
            'mean': item['mean'],
            'std': item['std'],
            'count': item['count']
        }

    md_lines = ["### Sensitivity Analysis: Model Comparison (CodeLlama 7B/3B vs 350M)", ""]
    md_lines.append("Comparison of generated code metrics across different CodeLlama model sizes to assess sensitivity to model scale.")
    md_lines.append("")

    # Create a table for each metric
    all_metrics = set()
    for model_data in models.values():
        all_metrics.update(model_data.keys())

    for metric in sorted(all_metrics):
        md_lines.append(f"**{metric.replace('_', ' ').title()}**")
        md_lines.append("")
        md_lines.append(f"| Model Size | Mean | Std Dev | Count |")
        md_lines.append(f"| :--- | :--- | :--- | :--- |")
        
        for model_name in sorted(models.keys()):
            data = models[model_name].get(metric, {})
            mean_val = f"{data['mean']:.2f}" if 'mean' in data else "N/A"
            std_val = f"{data['std']:.2f}" if 'std' in data else "N/A"
            count_val = str(data.get('count', 0))
            md_lines.append(f"| {model_name} | {mean_val} | {std_val} | {count_val} |")
        md_lines.append("")

    # Add a brief textual summary
    md_lines.append("**Summary:**")
    md_lines.append("The table above compares the structural complexity and functional coverage of code generated by different CodeLlama variants.")
    md_lines.append("Higher model sizes (7B, 3B) are expected to show different distributions compared to the smaller 350M model, particularly in Halstead Volume and Branch Coverage.")
    md_lines.append("")

    return "\n".join(md_lines)

def generate_markdown_report(metrics_data: Dict, stat_results: Optional[Dict], sensitivity_data: Optional[List[Dict]]):
    """Generate the final Markdown report."""
    timestamp = get_timestamp()
    
    # Prepare data for template
    context = {
        "timestamp": timestamp,
        "metrics": metrics_data,
        "statistics": stat_results,
        "figures": [
            {"name": "hist_complexity.png", "caption": "Distribution of Cyclomatic Complexity"},
            {"name": "hist_halstead.png", "caption": "Distribution of Halstead Volume"},
            {"name": "hist_coverage.png", "caption": "Distribution of Branch Coverage"},
            {"name": "box_cyclomatic_complexity.png", "caption": "Boxplot of Cyclomatic Complexity"},
            {"name": "box_halstead_volume.png", "caption": "Boxplot of Halstead Volume"},
            {"name": "box_branch_coverage_pct.png", "caption": "Boxplot of Branch Coverage"}
        ],
        "sensitivity_content": format_sensitivity_comparison(sensitivity_data) if sensitivity_data else "No sensitivity data available.",
        "summary_stats": {}
    }

    # Calculate summary stats for the main metrics
    for metric in ["cyclomatic_complexity", "halstead_volume", "branch_coverage_pct"]:
        values = extract_metric_values(metrics_data, metric)
        context["summary_stats"][metric] = calculate_summary_stats(values)

    # Template for the report
    template_str = """
    # Research Report: Evaluating the Impact of Code Generation Models on Code Testability

    **Generated:** {{ timestamp }}

    ## 1. Executive Summary

    This report presents the results of the automated pipeline analyzing code generated by LLMs.
    It includes structural complexity metrics (Cyclomatic Complexity, Halstead Volume), functional test coverage,
    statistical hypothesis testing results, and a sensitivity analysis comparing different model scales.

    ## 2. Data Overview

    Total samples analyzed: {{ metrics | length }}

    ### Summary Statistics

    {% for metric, stats in summary_stats.items() %}
    #### {{ metric.replace('_', ' ').title() }}
    - Mean: {{ "%.2f"|format(stats.mean) }}
    - Std Dev: {{ "%.2f"|format(stats.std) }}
    - Min: {{ "%.2f"|format(stats.min) }}
    - Max: {{ "%.2f"|format(stats.max) }}
    - Median: {{ "%.2f"|format(stats.median) }}
    {% endfor %}

    ## 3. Visualizations

    {% for fig in figures %}
    ### {{ fig.caption }}
    ![](figures/{{ fig.name }})
    {% endfor %}

    ## 4. Statistical Analysis

    {% if statistics %}
    ### Hypothesis Testing Results

    {% for test_name, result in statistics.items() %}
    #### {{ test_name.replace('_', ' ').title() }}
    - Statistic: {{ result.get('statistic', 'N/A') }}
    - P-value: {{ result.get('pvalue', 'N/A') }}
    - Conclusion: {{ result.get('conclusion', 'N/A') }}
    {% endfor %}

    {% if statistics.get('power_analysis') %}
    ### Power Analysis
    - Required Sample Size (n >= 38): {{ statistics.power_analysis.get('required_n', 'N/A') }}
    - Achieved Power: {{ statistics.power_analysis.get('achieved_power', 'N/A') }}
    {% endif %}
    {% else %}
    Statistical results not available.
    {% endif %}

    ## 5. Sensitivity Analysis: Model Comparison (CodeLlama 7B/3B vs 350M)

    {{ sensitivity_content }}

    ## 6. Conclusion

    The pipeline successfully generated metrics for {{ metrics | length }} samples.
    Statistical tests were performed to compare structural complexity against functional success.
    Sensitivity analysis provides insights into how model scale affects code testability.

    ---
    *Report generated by llmXive automated science pipeline.*
    """

    template = Template(template_str)
    report_content = template.render(context)

    with open(RESULTS_REPORT_FILE, 'w') as f:
        f.write(report_content)
    
    logging.info(f"Report generated successfully: {RESULTS_REPORT_FILE}")

def main():
    """Main entry point for report generation."""
    set_task_id("T032")
    logger = get_logger()
    logger.info("Starting report generation (T032)...")

    try:
        # Load data
        metrics_data = load_metrics_data()
        logger.info(f"Loaded {len(metrics_data)} metrics records.")

        stat_results = load_statistical_results()
        
        # Load sensitivity data if it exists (merged into metrics or separate file)
        # We assume sensitivity data is merged into metrics.json with a 'model_type' field or similar.
        # For this task, we look for a specific file or derive from metrics if structured.
        # Based on T041, sensitivity data is merged. We need to extract it.
        # If the merged file doesn't have a separate sensitivity file, we parse metrics for 'model_type'.
        sensitivity_data = None
        # Check if metrics have model_type to separate
        if metrics_data and isinstance(metrics_data, list):
            # Check if any item has 'model_type'
            if any('model_type' in item for item in metrics_data):
                # Re-calculate stats per model type for the report
                models = {}
                for item in metrics_data:
                    model = item.get('model_type', 'default')
                    if model not in models:
                        models[model] = []
                    models[model].append(item)
                
                sensitivity_list = []
                for model_name, items in models.items():
                    for metric in ['cyclomatic_complexity', 'halstead_volume', 'branch_coverage_pct']:
                        vals = [x[metric] for x in items if metric in x and x[metric] is not None and x[metric] != '[deferred]']
                        if vals:
                            sensitivity_list.append({
                                'model_type': model_name,
                                'metric_name': metric,
                                'mean': float(np.mean(vals)),
                                'std': float(np.std(vals)),
                                'count': len(vals)
                            })
                sensitivity_data = sensitivity_list

        # Generate plots
        generate_all_plots(metrics_data)

        # Generate report
        generate_markdown_report(metrics_data, stat_results, sensitivity_data)

        logger.info("Report generation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during report generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())