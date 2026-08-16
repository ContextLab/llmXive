import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import load_paths
from utils.logging import get_logger

logger = get_logger(__name__)

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {file_path}: {e}")
        return None

def format_float(value: Optional[float], decimals: int = 4) -> str:
    """Format a float value, handling None gracefully."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"

def generate_research_md(
    metrics: Dict[str, Any],
    vif_scores: Dict[str, float],
    ale_plots: List[str],
    feature_ranking: List[Dict[str, Any]],
    permutation_results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate the final research.md summary file.

    Includes metrics, VIF results, and references to ALE plot files.
    Does not generate interpretation text not mandated by spec.
    """
    lines = []
    lines.append("# Research Summary: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy")
    lines.append("")
    lines.append("## 1. Model Performance Metrics")
    lines.append("")
    lines.append("| Metric | Random Forest | Gradient Boosting |")
    lines.append("| :--- | :--- | :--- |")

    rf_r2 = metrics.get('rf', {}).get('r2') if isinstance(metrics.get('rf'), dict) else metrics.get('rf_r2')
    gb_r2 = metrics.get('gb', {}).get('r2') if isinstance(metrics.get('gb'), dict) else metrics.get('gb_r2')
    rf_mae = metrics.get('rf', {}).get('mae') if isinstance(metrics.get('rf'), dict) else metrics.get('rf_mae')
    gb_mae = metrics.get('gb', {}).get('mae') if isinstance(metrics.get('gb'), dict) else metrics.get('gb_mae')
    rf_rmse = metrics.get('rf', {}).get('rmse') if isinstance(metrics.get('rf'), dict) else metrics.get('rf_rmse')
    gb_rmse = metrics.get('gb', {}).get('rmse') if isinstance(metrics.get('gb'), dict) else metrics.get('gb_rmse')
    rf_overfit = metrics.get('rf', {}).get('overfitting_ratio') if isinstance(metrics.get('rf'), dict) else metrics.get('rf_overfitting_ratio')
    gb_overfit = metrics.get('gb', {}).get('overfitting_ratio') if isinstance(metrics.get('gb'), dict) else metrics.get('gb_overfitting_ratio')

    lines.append(f"| R² | {format_float(rf_r2)} | {format_float(gb_r2)} |")
    lines.append(f"| MAE | {format_float(rf_mae)} | {format_float(gb_mae)} |")
    lines.append(f"| RMSE | {format_float(rf_rmse)} | {format_float(gb_rmse)} |")
    lines.append(f"| Overfitting Ratio | {format_float(rf_overfit)} | {format_float(gb_overfit)} |")
    lines.append("")

    lines.append("## 2. Feature Importance and Stability")
    lines.append("")
    lines.append("### 2.1 Top Ranked Descriptors")
    lines.append("")
    if feature_ranking:
        lines.append("| Rank | Feature | Importance Score |")
        lines.append("| :--- | :--- | :--- |")
        for i, item in enumerate(feature_ranking, 1):
            feature_name = item.get('feature', 'Unknown')
            score = item.get('importance', 0.0)
            lines.append(f"| {i} | {feature_name} | {format_float(score)} |")
    else:
        lines.append("No feature ranking data available.")
    lines.append("")

    lines.append("### 2.2 Permutation Importance Validation")
    lines.append("")
    if permutation_results:
        corr = permutation_results.get('correlation', permutation_results.get('r'))
        passed = permutation_results.get('importance_correlation_pass')
        lines.append(f"- Pearson Correlation (Tree vs Permutation): {format_float(corr)}")
        lines.append(f"- Validation Threshold (r ≥ 0.8): {'Passed' if passed else 'Failed'}")
    else:
        lines.append("Permutation importance results not available.")
    lines.append("")

    lines.append("### 2.3 Variance Inflation Factor (VIF) Analysis")
    lines.append("")
    if vif_scores:
        lines.append("| Feature | VIF Score | Status (Threshold > 10) |")
        lines.append("| :--- | :--- | :--- |")
        for feature, vif in vif_scores.items():
            status = "High Collinearity" if vif > 10 else "Acceptable"
            lines.append(f"| {feature} | {format_float(vif)} | {status} |")
    else:
        lines.append("VIF scores not available.")
    lines.append("")

    lines.append("## 3. Accumulated Local Effects (ALE) Plots")
    lines.append("")
    lines.append("The following ALE plot files have been generated for the top-ranked features:")
    lines.append("")
    if ale_plots:
        for plot_file in ale_plots:
            lines.append(f"- `data/evaluation/{plot_file}`")
    else:
        lines.append("No ALE plot files found.")
    lines.append("")

    lines.append("## 4. Statistical Tests")
    lines.append("")
    lines.append("Statistical comparison results (e.g., t-test) are available in `data/evaluation/statistical_tests.json`.")
    lines.append("")

    # Write the file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Research summary generated at {output_path}")

def main() -> None:
    """Main entry point for generating the research summary."""
    paths = load_paths()
    data_dir = paths['data']
    evaluation_dir = data_dir / 'evaluation'
    project_root = paths['project_root']

    # Define artifact paths
    metrics_path = evaluation_dir / 'model_metrics.json'
    vif_path = evaluation_dir / 'vif_scores.json'
    ranking_path = evaluation_dir / 'feature_ranking.json'
    perm_path = evaluation_dir / 'permutation_importance.json'
    output_path = project_root / 'research.md'

    # Load artifacts
    metrics = load_json_safe(metrics_path) or {}
    vif_scores = load_json_safe(vif_path) or {}
    feature_ranking = load_json_safe(ranking_path) or []
    perm_results = load_json_safe(perm_path) or {}

    # Identify ALE plots
    ale_plots = []
    if evaluation_dir.exists():
        for f in evaluation_dir.glob('ale_*.png'):
            ale_plots.append(f.name)

    # Generate the report
    generate_research_md(
        metrics=metrics,
        vif_scores=vif_scores,
        ale_plots=ale_plots,
        feature_ranking=feature_ranking,
        permutation_results=perm_results,
        output_path=output_path
    )

if __name__ == '__main__':
    main()
