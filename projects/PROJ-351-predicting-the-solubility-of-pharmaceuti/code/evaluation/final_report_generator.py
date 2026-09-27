"""
Final Report Generation for T046.
Generates docs/reports/final_report.md by reading from:
- results/metrics.json
- results/statistical_test.json
- results/viz_manifest.json
- results/model_comparison.json (optional, for delta)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure imports align with project API surface
# We will read directly from JSON files as specified in T046 requirements.
# No external imports from sibling modules are strictly required for this
# report generation task, as it is a read-and-compile operation.

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def generate_report_content(
    metrics: Dict[str, Any],
    stats: Dict[str, Any],
    viz_manifest: Dict[str, Any],
    comparison: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate the Markdown content for the final report.
    Fulfills the mandatory sections defined in T046.
    """
    lines = []

    # 1. Executive Summary
    lines.append("# Final Report: Predicting Solubility of Pharmaceutical Compounds")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("This report presents the results of a study comparing a Random Forest baseline "
                 "against a Message Passing Neural Network (MPNN) for predicting the aqueous solubility "
                 "(logS) of pharmaceutical compounds using the ESOL dataset.")
    lines.append("")
    
    rf_rmse = metrics.get("baseline", {}).get("rmse", "N/A")
    gnn_rmse = metrics.get("gnn", {}).get("rmse", "N/A")
    rf_r2 = metrics.get("baseline", {}).get("r2", "N/A")
    gnn_r2 = metrics.get("gnn", {}).get("r2", "N/A")
    
    lines.append(f"The Random Forest baseline achieved an RMSE of **{rf_rmse}** (R²: {rf_r2}), "
                 f"while the GNN model achieved an RMSE of **{gnn_rmse}** (R²: {gnn_r2}).")
    lines.append("")
    if comparison and comparison.get("delta_rmse"):
        delta = comparison["delta_rmse"]
        improvement = "improvement" if delta < 0 else "degradation"
        lines.append(f"This represents a {improvement} of **{abs(delta):.4f}** in RMSE.")
    lines.append("")

    # 2. Methodology
    lines.append("## 2. Methodology")
    lines.append("")
    lines.append("### Data Preprocessing")
    lines.append("- **Dataset**: ESOL (Delaney) dataset from MoleculeNet.")
    lines.append("- **Cleaning**: Invalid SMILES and NaN logS values were excluded.")
    lines.append("- **Splitting**: Stratified 5-Fold Cross-Validation using 10 quantile bins for logS.")
    lines.append("")
    lines.append("### Models")
    lines.append("- **Baseline**: Random Forest trained on Morgan Fingerprints (radius=2, 2048 bits).")
    lines.append("- **Experimental**: Message Passing Neural Network (MPNN) using PyTorch Geometric.")
    lines.append("")
    lines.append("### Validation Strategy")
    lines.append("- **Nested Cross-Validation**: Outer loop (5 folds) for evaluation, Inner loop (5 folds) for hyperparameter tuning.")
    lines.append("- **Statistical Testing**: Nadeau's Corrected Resampled t-test with Shapiro-Wilk normality check.")
    lines.append("")

    # 3. Performance Comparison
    lines.append("## 3. Performance Comparison")
    lines.append("")
    lines.append("| Model | RMSE | R² |")
    lines.append("| :--- | :--- | :--- |")
    lines.append(f"| Random Forest | {rf_rmse} | {rf_r2} |")
    lines.append(f"| GNN (MPNN) | {gnn_rmse} | {gnn_r2} |")
    lines.append("")
    if comparison:
        delta_rmse = comparison.get("delta_rmse", "N/A")
        lines.append(f"**RMSE Delta (GNN - RF):** {delta_rmse}")
    lines.append("")

    # 4. Statistical Significance
    lines.append("## 4. Statistical Significance")
    lines.append("")
    p_value = stats.get("p_value", "N/A")
    cohens_d = stats.get("effect_size_cohens_d", "N/A")
    power = stats.get("statistical_power", "N/A")
    normality = stats.get("normality_test", {}).get("is_normal", "N/A")
    
    lines.append(f"- **Normality Test (Shapiro-Wilk):** {'Normal distribution assumed' if normality else 'Non-normal distribution detected'}")
    lines.append(f"- **P-value:** {p_value}")
    lines.append(f"- **Effect Size (Cohen's d):** {cohens_d}")
    lines.append(f"- **Statistical Power:** {power}")
    lines.append("")
    
    if power < 0.8 and power != "N/A":
        lines.append(f"> **Limitation:** Statistical power ({power}) is below the recommended threshold of 0.8. "
                     f"Interpretation of non-significant results should be cautious.")
    lines.append("")

    # 5. Interpretability
    lines.append("## 5. Interpretability")
    lines.append("")
    lines.append("Feature importance and attention heatmaps were generated for a representative subset of molecules.")
    lines.append("")
    
    viz_files = viz_manifest.get("files", [])
    lines.append(f"**Generated Visualizations ({len(viz_files)} files):**")
    lines.append("")
    for item in viz_files:
        path = item.get("path", "unknown")
        mol_id = item.get("molecule_id", "unknown")
        lines.append(f"- `{path}` (Molecule ID: {mol_id})")
    lines.append("")

    # 6. Limitations
    lines.append("## 6. Limitations")
    lines.append("")
    ceiling_flag = metrics.get("ceiling_effect", False)
    if ceiling_flag:
        lines.append("- **Ceiling Effect:** The baseline model achieved an R² > 0.9, suggesting the task may be saturated "
                     "by simpler models, limiting the observable gain from complex GNN architectures.")
    else:
        lines.append("- **Baseline Performance:** The Random Forest baseline did not exhibit a ceiling effect (R² ≤ 0.9).")
    lines.append("")
    
    if power < 0.8 and power != "N/A":
        lines.append(f"- **Statistical Power:** The study had a power of {power}, which is below the standard 0.8 threshold. "
                     f"This increases the risk of Type II errors (false negatives).")
    lines.append("")
    lines.append("- **Dataset Size:** The ESOL dataset is relatively small (~1,100 compounds), which limits the generalizability "
                 "of the findings to larger, more diverse chemical spaces.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated automatically by the llmXive pipeline.*")

    return "\n".join(lines)

def main():
    """
    Main entry point for T046.
    Reads required JSON artifacts and writes the final report.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Define paths relative to project root
    # Assuming execution from project root or code/ directory
    base_path = Path(__file__).resolve().parent.parent.parent
    results_dir = base_path / "results"
    docs_reports_dir = base_path / "docs" / "reports"
    
    # Ensure output directory exists
    docs_reports_dir.mkdir(parents=True, exist_ok=True)

    # Define input file paths
    metrics_path = results_dir / "metrics.json"
    stats_path = results_dir / "statistical_test.json"
    viz_path = results_dir / "viz_manifest.json"
    comparison_path = results_dir / "model_comparison.json"

    logger.info("Starting Final Report Generation (T046)...")

    try:
        # Load required data
        logger.info(f"Loading metrics from {metrics_path}")
        metrics = load_json_file(metrics_path)

        logger.info(f"Loading statistical results from {stats_path}")
        stats = load_json_file(stats_path)

        logger.info(f"Loading visualization manifest from {viz_path}")
        viz_manifest = load_json_file(viz_path)

        comparison = None
        if comparison_path.exists():
            logger.info(f"Loading model comparison from {comparison_path}")
            comparison = load_json_file(comparison_path)
        else:
            logger.warning(f"Comparison file not found at {comparison_path}, skipping delta calculation.")

        # Generate content
        report_content = generate_report_content(metrics, stats, viz_manifest, comparison)

        # Write report
        output_path = docs_reports_dir / "final_report.md"
        logger.info(f"Writing report to {output_path}")
        with open(output_path, 'w') as f:
            f.write(report_content)

        logger.info("Final Report Generation completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required artifact: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in artifact: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())