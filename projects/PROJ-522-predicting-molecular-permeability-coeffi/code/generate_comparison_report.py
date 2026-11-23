"""
Generate comparison report summarizing mean/std metrics and statistical significance.

This script loads the aggregated fold metrics from `data/processed/predictions.csv`
(produced by T022) and the statistical test results from `data/processed/statistical_results.json`
(produced by T024), then generates a human-readable Markdown report at `paper/report.md`.

It summarizes:
1. Mean and standard deviation of R², MAE, and RMSE for GCN, Random Forest, and Linear Regression.
2. Paired t-test results comparing GCN vs. RF and GCN vs. LR.
3. A conclusion section highlighting the best performing model.
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_predictions(filepath: Path) -> pd.DataFrame:
    """Load the predictions and metrics CSV file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Predictions file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df

def load_statistical_results(filepath: Path) -> Dict[str, Any]:
    """Load the statistical test results JSON file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Statistical results file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_summary_metrics(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calculate mean and std for R², MAE, RMSE grouped by model.

    Returns:
        Dict: {model_name: {'r2_mean': ..., 'r2_std': ..., 'mae_mean': ..., ...}}
    """
    summary = {}
    models = df['model'].unique()

    for model in models:
        subset = df[df['model'] == model]
        summary[model] = {
            'r2_mean': subset['r2'].mean(),
            'r2_std': subset['r2'].std(),
            'mae_mean': subset['mae'].mean(),
            'mae_std': subset['mae'].std(),
            'rmse_mean': subset['rmse'].mean(),
            'rmse_std': subset['rmse'].std()
        }
    return summary

def format_metric(value: float, std: float, decimals: int = 4) -> str:
    """Format a metric with its standard deviation."""
    return f"{value:.{decimals}f} ± {std:.{decimals}f}"

def generate_markdown_report(
    summary_metrics: Dict[str, Dict[str, float]],
    statistical_results: Dict[str, Any],
    output_path: Path
) -> None:
    """Generate the Markdown comparison report."""
    lines = []
    lines.append("# Molecular Permeability Prediction: Model Comparison Report")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("This report compares the performance of three models—Graph Convolutional Network (GCN),")
    lines.append("Random Forest (RF), and Linear Regression (LR)—on the task of predicting molecular permeability coefficients.")
    lines.append("Performance is evaluated using 5-fold scaffold-split cross-validation, with metrics including")
    lines.append("R², Mean Absolute Error (MAE), and Root Mean Squared Error (RMSE).")
    lines.append("")

    # Determine best model based on R²
    best_model = max(summary_metrics.keys(), key=lambda m: summary_metrics[m]['r2_mean'])
    lines.append(f"**Best Performing Model:** {best_model} (Mean R² = {summary_metrics[best_model]['r2_mean']:.4f})")
    lines.append("")

    lines.append("## 2. Performance Metrics Summary")
    lines.append("")
    lines.append("The table below shows the mean and standard deviation of performance metrics across 5 folds.")
    lines.append("")
    lines.append("| Model | R² (Mean ± Std) | MAE (Mean ± Std) | RMSE (Mean ± Std) |")
    lines.append("| :--- | :--- | :--- | :--- |")

    for model in sorted(summary_metrics.keys()):
        m = summary_metrics[model]
        r2_str = format_metric(m['r2_mean'], m['r2_std'])
        mae_str = format_metric(m['mae_mean'], m['mae_std'])
        rmse_str = format_metric(m['rmse_mean'], m['rmse_std'])
        lines.append(f"| {model} | {r2_str} | {mae_str} | {rmse_str} |")

    lines.append("")

    lines.append("## 3. Statistical Significance Analysis")
    lines.append("")
    lines.append("Paired t-tests were performed to determine if the differences in performance between models are statistically significant.")
    lines.append("The null hypothesis (H₀) is that there is no difference in mean performance between the two models.")
    lines.append("A significance level (α) of 0.05 was used.")
    lines.append("")

    comparisons = statistical_results.get('comparisons', [])
    lines.append("| Comparison | T-statistic | P-value | Significant (α=0.05)? |")
    lines.append("| :--- | :--- | :--- | :--- |")

    for comp in comparisons:
        is_sig = "Yes" if comp['significant'] else "No"
        lines.append(f"| {comp['model_1']} vs {comp['model_2']} | {comp['t_stat']:.4f} | {comp['p_value']:.4f} | {is_sig} |")

    lines.append("")

    # Interpretation
    lines.append("### Interpretation")
    lines.append("")
    for comp in comparisons:
        if comp['significant']:
            winner = comp['model_1'] if comp['model_1'] == best_model else comp['model_2']
            lines.append(f"- The difference between **{comp['model_1']}** and **{comp['model_2']}** is statistically significant (p < 0.05).")
            lines.append(f"  - **{winner}** demonstrates superior performance based on R².")
        else:
            lines.append(f"- The difference between **{comp['model_1']}** and **{comp['model_2']}** is **not** statistically significant (p ≥ 0.05).")
            lines.append(f"  - We cannot conclude that one model outperforms the other based on this dataset and split strategy.")
        lines.append("")

    lines.append("## 4. Conclusion")
    lines.append("")
    lines.append(f"Based on the 5-fold scaffold-split cross-validation, the **{best_model}** model achieved the highest mean R² score.")
    lines.append(f"Statistical testing confirms whether this improvement is significant over the baseline models.")
    lines.append("")
    lines.append("Note: All reported structure-permeability relationships are associational, not causal, due to the observational nature of the training data.")
    lines.append("")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    logger.info(f"Report generated successfully at {output_path}")

def main():
    """Main entry point for the report generation."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    predictions_path = project_root / "data" / "processed" / "predictions.csv"
    stats_path = project_root / "data" / "processed" / "statistical_results.json"
    report_path = project_root / "paper" / "report.md"

    logger.info(f"Loading predictions from {predictions_path}...")
    df = load_predictions(predictions_path)

    logger.info(f"Loading statistical results from {stats_path}...")
    stats_results = load_statistical_results(stats_path)

    logger.info("Calculating summary metrics...")
    summary = calculate_summary_metrics(df)

    logger.info("Generating Markdown report...")
    generate_markdown_report(summary, stats_results, report_path)

    print(f"Report successfully generated at: {report_path}")

if __name__ == "__main__":
    main()