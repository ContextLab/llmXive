"""
Final Report Writer for T046.
Generates docs/reports/final_report.md by reading from results/*.json artifacts.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its content as a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_executive_summary(metrics: Dict[str, Any]) -> str:
    """Generate the Executive Summary section."""
    rf_rmse = metrics.get('baseline_rmse', 'N/A')
    gnn_rmse = metrics.get('gnn_rmse', 'N/A')
    delta = metrics.get('rmse_delta', 'N/A')
    
    if isinstance(rf_rmse, (int, float)) and isinstance(gnn_rmse, (int, float)):
        improvement = "improvement" if delta < 0 else "degradation"
        return (
            f"This study evaluates the solubility of pharmaceutical compounds using "
            f"Graph Neural Networks (GNN) compared to a Random Forest (RF) baseline. "
            f"The GNN model achieved an RMSE of {gnn_rmse:.4f}, compared to the RF baseline "
            f"of {rf_rmse:.4f}, representing a {improvement} of {abs(delta):.4f}.\n"
        )
    return "Performance metrics pending calculation.\n"

def generate_methodology() -> str:
    """Generate the Methodology section."""
    return (
        "## Methodology\n\n"
        "### Data Pipeline\n"
        "The ESOL dataset was downloaded, cleaned (invalid SMILES removed), and "
        "preprocessed into molecular graphs. A Stratified 5-Fold split (10 quantile bins) "
        "was applied to ensure distribution balance.\n\n"
        "### Models\n"
        "1. **Random Forest Baseline**: Trained using Morgan Fingerprints (radius=2, 2048 bits) "
        "with Nested Cross-Validation (5 outer, 5 inner folds) for hyperparameter tuning.\n"
        "2. **GNN (MPNN)**: A Message Passing Neural Network trained on graph tensors with "
        "Nested Cross-Validation and Early Stopping.\n\n"
        "### Statistical Analysis\n"
        "Model comparison utilized Nadeau's Corrected Resampled t-test on the absolute "
        "prediction errors from the outer CV folds. Normality was assessed via Shapiro-Wilk.\n"
    )

def generate_performance_comparison(metrics: Dict[str, Any]) -> str:
    """Generate the Performance Comparison table."""
    rf_rmse = metrics.get('baseline_rmse', 'N/A')
    rf_r2 = metrics.get('baseline_r2', 'N/A')
    gnn_rmse = metrics.get('gnn_rmse', 'N/A')
    gnn_r2 = metrics.get('gnn_r2', 'N/A')
    delta = metrics.get('rmse_delta', 'N/A')

    return (
        f"## Performance Comparison\n\n"
        f"| Model | RMSE | R² |\n"
        f"| :--- | :--- | :--- |\n"
        f"| Random Forest Baseline | {rf_rmse:.4f} | {rf_r2:.4f} |\n"
        f"| GNN (MPNN) | {gnn_rmse:.4f} | {gnn_r2:.4f} |\n"
        f"| **Delta (GNN - RF)** | **{delta:.4f}** | |\n\n"
    )

def generate_statistical_significance(stats: Dict[str, Any]) -> str:
    """Generate the Statistical Significance section."""
    p_val = stats.get('p_value', 'N/A')
    cohens_d = stats.get('effect_size_cohens_d', 'N/A')
    power = stats.get('statistical_power', 'N/A')
    normality = stats.get('normality_test', {}).get('is_normal', 'Unknown')
    
    test_type = "Nadeau's Corrected Resampled t-test"
    if not normality and normality is not True:
        test_type = "Wilcoxon Signed-Rank Test (Non-parametric alternative)"

    power_interpretation = ""
    if isinstance(power, (int, float)):
        if power < 0.8:
            power_interpretation = (
                f"**Note:** The statistical power ({power:.3f}) is below the recommended "
                f"threshold of 0.8, indicating a potential risk of Type II error.\n"
            )
        else:
            power_interpretation = (
                f"The study has adequate statistical power ({power:.3f}).\n"
            )

    return (
        f"## Statistical Significance\n\n"
        f"A {test_type} was performed on the prediction errors.\n\n"
        f"- **P-value:** {p_val}\n"
        f"- **Effect Size (Cohen's d):** {cohens_d}\n"
        f"- **Statistical Power:** {power}\n\n"
        f"{power_interpretation}"
    )

def generate_interpretability(viz_manifest: Dict[str, Any]) -> str:
    """Generate the Interpretability section."""
    files = viz_manifest.get('files', [])
    if not files:
        return "## Interpretability\n\nNo visualization artifacts were found.\n"

    file_list = "\n".join([f"- `{f['path']}`" for f in files])
    return (
        f"## Interpretability\n\n"
        f"Feature importance heatmaps were generated for a representative subset of molecules.\n"
        f"Refer to the following visualizations:\n\n"
        f"{file_list}\n"
    )

def generate_limitations(metrics: Dict[str, Any], stats: Dict[str, Any]) -> str:
    """Generate the Limitations section."""
    lines = ["## Limitations\n\n"]
    
    # Check ceiling effect
    ceiling_flag = metrics.get('ceiling_effect', False)
    if ceiling_flag:
        lines.append("- **Ceiling Effect:** The Random Forest baseline achieved R² > 0.9, "
                     "suggesting the task may be saturated for this dataset size, "
                     "limiting the observable improvement from GNNs.\n")
    
    # Check power
    power = stats.get('statistical_power', 0)
    if isinstance(power, (int, float)) and power < 0.8:
        lines.append(f"- **Statistical Power:** The post-hoc power analysis yielded "
                     f"{power:.3f}, which is below the 0.8 threshold. Conclusions "
                     f"regarding statistical significance should be interpreted with caution.\n")
    
    if not lines or len(lines) == 1:
        lines.append("- No significant limitations detected based on current metrics.\n")
        
    return "".join(lines)

def main():
    """Main entry point to generate the final report."""
    # Define paths
    base_path = Path(__file__).resolve().parent.parent.parent
    results_dir = base_path / 'results'
    docs_reports_dir = base_path / 'docs' / 'reports'
    
    # Ensure output directory exists
    docs_reports_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = docs_reports_dir / 'final_report.md'
    
    logger.info(f"Loading artifacts from {results_dir}...")
    
    try:
        metrics = load_json_file(results_dir / 'metrics.json')
        stats = load_json_file(results_dir / 'statistical_test.json')
        viz_manifest = load_json_file(results_dir / 'viz_manifest.json')
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Cannot generate report: Missing required input artifacts.")
        sys.exit(1)

    logger.info("Generating report content...")
    
    content = [
        "# Final Report: Predicting Solubility of Pharmaceutical Compounds",
        "",
        generate_executive_summary(metrics),
        generate_methodology(),
        generate_performance_comparison(metrics),
        generate_statistical_significance(stats),
        generate_interpretability(viz_manifest),
        generate_limitations(metrics, stats),
        "",
        "---",
        f"*Report generated on: {__import__('datetime').datetime.now().isoformat()}*"
    ]
    
    report_text = "\n".join(content)
    
    logger.info(f"Writing report to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    logger.info("Final report generation complete.")

if __name__ == '__main__':
    main()