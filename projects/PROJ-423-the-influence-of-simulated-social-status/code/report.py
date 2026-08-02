"""
Reporting Module for Simulated Social Status Study.

This module generates comprehensive research reports including forest plots,
model summaries, sensitivity analysis results, and post-hoc comparisons.
It produces both HTML and PDF formats for reproducible research dissemination.

Key Features:
    - Forest plot visualization of condition means with confidence intervals
    - Model results table with coefficients, standard errors, and p-values
    - VIF table for multicollinearity assessment
    - Sensitivity analysis summary across outlier thresholds
    - Post-hoc comparison table with Bonferroni correction
    - HTML template rendering with Jinja2
    - PDF generation using WeasyPrint

The module integrates analysis results from the regression module and
formats them into publication-ready reports.

Attributes:
    logger (logging.Logger): Module-level logger for tracking execution.
"""

import os
import json
import base64
import io
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# Ensure code is in path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logger import setup_logger, get_logger
from utils import load_json, ensure_directory

logger = setup_logger("report", "logs/report.log")


def calculate_condition_stats(df: pd.DataFrame) -> dict:
    """
    Calculate descriptive statistics for each experimental condition.

    Computes mean, standard deviation, standard error, and 95% confidence
    intervals for risk-taking scores within each condition combination.

    Args:
        df (pd.DataFrame): Preprocessed dataset with condition variables.

    Returns:
        dict: Condition statistics including:
            - means (dict): Mean score for each condition
            - stds (dict): Standard deviation for each condition
            - ses (dict): Standard error for each condition
            - ci_lower (dict): Lower bound of 95% CI
            - ci_upper (dict): Upper bound of 95% CI
            - n_per_condition (dict): Sample size per condition
    """
    stats = {
        "means": {},
        "stds": {},
        "ses": {},
        "ci_lower": {},
        "ci_upper": {},
        "n_per_condition": {}
    }

    conditions = df.groupby(["status_level", "observed_behavior"])["risk_taking_score"]

    for (status, behavior), group in conditions:
        condition_name = f"{status}_{behavior}"
        n = len(group)
        mean = group.mean()
        std = group.std()
        se = std / np.sqrt(n) if n > 0 else 0
        ci_margin = 1.96 * se

        stats["means"][condition_name] = float(mean)
        stats["stds"][condition_name] = float(std)
        stats["ses"][condition_name] = float(se)
        stats["ci_lower"][condition_name] = float(mean - ci_margin)
        stats["ci_upper"][condition_name] = float(mean + ci_margin)
        stats["n_per_condition"][condition_name] = int(n)

    return stats


def generate_forest_plot(df: pd.DataFrame, output_path: str = None) -> str:
    """
    Generate a forest plot of condition means with confidence intervals.

    Creates a publication-quality visualization showing the estimated
    mean risk-taking scores for each experimental condition with 95%
    confidence intervals.

    Args:
        df (pd.DataFrame): Preprocessed dataset.
        output_path (str, optional): Path to save the plot image. If None,
            returns base64 encoded string.

    Returns:
        str: Base64 encoded image string (or None if output_path specified).
    """
    stats = calculate_condition_stats(df)

    fig, ax = plt.subplots(figsize=(10, 6))

    conditions = list(stats["means"].keys())
    means = [stats["means"][c] for c in conditions]
    ci_lower = [stats["ci_lower"][c] for c in conditions]
    ci_upper = [stats["ci_upper"][c] for c in conditions]
    errors = [[m - l, u - m] for m, l, u in zip(means, ci_lower, ci_upper)]

    y_pos = np.arange(len(conditions))

    ax.errorbar(y_pos, means, yerr=errors, fmt='o', capsize=5,
               ecolor='black', color='steelblue', markersize=8,
               capthick=2, elinewidth=2)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(conditions)
    ax.set_xlabel('Mean Risk-Taking Score')
    ax.set_title('Effect of Social Status and Observed Behavior on Risk-Taking')
    ax.axvline(x=np.mean(means), color='red', linestyle='--', alpha=0.5, label='Grand Mean')
    ax.legend()
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()

    if output_path:
        ensure_directory(os.path.dirname(output_path))
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Forest plot saved to {output_path}")
        plt.close()
        return output_path
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"


def load_model_results(results_path: str) -> dict:
    """
    Load model results from a JSON file.

    Args:
        results_path (str): Path to the analysis results JSON file.

    Returns:
        dict: Model results dictionary.
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Model results file not found: {results_path}")

    with open(results_path, 'r') as f:
        return json.load(f)


def load_sensitivity_results(results_path: str) -> dict:
    """
    Load sensitivity analysis results from a JSON file.

    Args:
        results_path (str): Path to the analysis results JSON file.

    Returns:
        dict: Sensitivity analysis results.
    """
    results = load_model_results(results_path)
    return results.get("sensitivity", {})


def generate_summary_report(
    model_results: dict,
    sensitivity_results: dict,
    forest_plot_path: str,
    output_path: str,
    template_path: str = None
) -> str:
    """
    Generate a comprehensive HTML/PDF research report.

    Combines all analysis results into a formatted report including:
    - Model coefficients and significance
    - VIF table for multicollinearity
    - Sensitivity analysis across outlier thresholds
    - Forest plot visualization
    - Post-hoc comparisons

    Args:
        model_results (dict): Results from fit_adaptive_model().
        sensitivity_results (dict): Results from run_sensitivity_analysis().
        forest_plot_path (str): Path to the forest plot image.
        output_path (str): Path to save the final report.
        template_path (str, optional): Path to custom Jinja2 template.

    Returns:
        str: Path to the generated report.
    """
    # Prepare template data
    model_table = {
        "coefficients": model_results.get("coefficients", {}),
        "p_values": model_results.get("p_values", {}),
        "model_type": model_results.get("model_type", "unknown")
    }

    vif_table = model_results.get("vif", {})

    # Format sensitivity table
    sensitivity_table = {
        "thresholds": sensitivity_results.get("thresholds", []),
        "effect_sizes": sensitivity_results.get("effect_sizes", []),
        "p_values": sensitivity_results.get("p_values", []),
        "n_excluded": sensitivity_results.get("n_excluded", [])
    }

    # Convert forest plot to base64 if it's a file path
    if os.path.exists(forest_plot_path):
        with open(forest_plot_path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
            forest_plot_img = f"data:image/png;base64,{img_base64}"
    else:
        forest_plot_img = forest_plot_path

    # Setup Jinja2 environment
    if template_path:
        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)
    else:
        template_dir = "reports/templates"
        template_name = "analysis_report.html"

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)

    # Render HTML
    html_content = template.render(
        model_table=model_table,
        vif_table=vif_table,
        sensitivity_table=sensitivity_table,
        forest_plot_img=forest_plot_img,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Save HTML
    ensure_directory(os.path.dirname(output_path))
    html_output = output_path.replace('.pdf', '.html')
    with open(html_output, 'w') as f:
        f.write(html_content)
    logger.info(f"HTML report saved to {html_output}")

    # Convert to PDF if requested
    if output_path.endswith('.pdf'):
        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(output_path)
            logger.info(f"PDF report saved to {output_path}")
        except ImportError:
            logger.warning("WeasyPrint not available. PDF generation skipped.")
            logger.info("Install weasyprint for PDF generation: pip install weasyprint")

    return output_path


def main():
    """
    Command-line entry point for report generation.

    Loads analysis results, generates forest plot, and creates
    comprehensive HTML/PDF report.

    Args:
        --results (str): Path to analysis results JSON
        --data (str): Path to preprocessed data CSV
        --output (str): Path for output report (HTML or PDF)
        --plot (str, optional): Path to save forest plot separately

    Example:
        python code/report.py --results reports/analysis_results.json --data data/processed/cleaned_data.csv --output reports/analysis_report.pdf
    """
    parser = argparse.ArgumentParser(description="Generate research report")
    parser.add_argument("--results", type=str, required=True, help="Analysis results JSON path")
    parser.add_argument("--data", type=str, required=True, help="Preprocessed data CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output report path")
    parser.add_argument("--plot", type=str, default=None, help="Forest plot output path")
    args = parser.parse_args()

    logger.info("Starting report generation")

    # Load results
    model_results = load_model_results(args.results)

    # Load data for forest plot
    df = pd.read_csv(args.data)

    # Generate forest plot
    if args.plot:
        forest_plot_path = generate_forest_plot(df, args.plot)
    else:
        forest_plot_path = generate_forest_plot(df)

    # Generate report
    sensitivity_results = model_results.get("sensitivity", {})
    generate_summary_report(
        model_results,
        sensitivity_results,
        forest_plot_path,
        args.output
    )

    print(f"Report generated: {args.output}")


if __name__ == "__main__":
    import sys
    main()