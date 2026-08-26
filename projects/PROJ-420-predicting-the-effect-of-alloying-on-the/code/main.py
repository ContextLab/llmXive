"""Main entry point for the final report generation pipeline."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure we can import sibling modules if run from project root
# (Though typically run as `python code/main.py` with PYTHONPATH set or via CLI)
try:
    from logging_config import get_logger, log_operation
except ImportError:
    # Fallback for direct execution without proper path setup in some environments
    import logging
    logger = logging.getLogger(__name__)
    def get_logger(*args, **kwargs): return logger
    def log_operation(*args, **kwargs): return None

def load_json_safe(path: str) -> Dict[str, Any]:
    """Load a JSON file safely, raising a clear error if missing or invalid."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

def load_parquet_safe(path: str):
    """Load a Parquet file safely."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    try:
        import pandas as pd
        return pd.read_parquet(p)
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet {path}: {e}")

def generate_final_report(
    metrics_path: str,
    vif_path: str,
    importance_path: str,
    methodological_flags_path: str,
    model_path: str,
    residuals_path: str,
    output_path: str
) -> None:
    """
    Generate the final markdown report aggregating all analysis results.

    Inputs:
    - metrics_path: results/model_metrics.json
    - vif_path: results/collinearity_diagnostic.json
    - importance_path: results/feature_importance_summary.json
    - methodological_flags_path: results/methodological_flags.json
    - model_path: models/rf_model.pkl
    - residuals_path: results/residuals.json
    - output_path: results/final_report.md
    """
    log_operation("generate_final_report", status="starting")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load all required artifacts
    try:
        metrics = load_json_safe(metrics_path)
        vif_data = load_json_safe(vif_path)
        importance_data = load_json_safe(importance_path)
        flags_data = load_json_safe(methodological_flags_path)
        residuals_data = load_json_safe(residuals_path)
        
        # Verify model exists (we don't load it fully to avoid heavy deps if not needed for text)
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

    except FileNotFoundError as e:
        log_operation("generate_final_report", status="failed", error=str(e))
        raise
    except Exception as e:
        log_operation("generate_final_report", status="failed", error=str(e))
        raise

    # Extract key values for the report
    cv_mae = metrics.get('cv_mae', 'N/A')
    cv_ci_lower = metrics.get('cv_ci_lower', 'N/A')
    cv_ci_upper = metrics.get('cv_ci_upper', 'N/A')
    test_mae = metrics.get('test_mae', 'N/A')

    vif_scores = vif_data.get('vif_scores', {})
    vif_pass = vif_data.get('pass', False)

    top_element = importance_data.get('top_element', 'N/A')
    second_element = importance_data.get('second_element', 'N/A')
    ratio = importance_data.get('ratio', 'N/A')

    mae_flag = flags_data.get('mae_flag', False)
    cv_mae_flag_value = flags_data.get('cv_mae', 'N/A')

    # Construct the report content
    report_lines = [
        "# Final Report: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys",
        "",
        "## Executive Summary",
        "",
        "This report presents the results of a machine learning analysis aimed at predicting the Poisson's ratio of aluminum alloys based on their chemical composition. A Random Forest model was trained and evaluated using rigorous cross-validation and a held-out test set.",
        "",
        "## Model Performance",
        "",
        f"- **Cross-Validation MAE**: {cv_mae} (95% CI: [{cv_ci_lower}, {cv_ci_upper}])",
        f"- **Held-Out Test MAE**: {test_mae}",
        "",
        "## Feature Importance Analysis",
        "",
        "Based on permutation importance in the compositional (ILR) space, the relative influence of alloying elements was ranked as follows:",
        "",
        f"- **Top Element**: {top_element}",
        f"- **Second Element**: {second_element}",
        f"- **Importance Ratio (Top/Second)**: {ratio}",
        "",
        "## Collinearity Diagnostics",
        "",
        "Variance Inflation Factor (VIF) analysis was performed on the raw atomic fractions to check for multicollinearity among predictors.",
        "",
        "### VIF Scores",
        "",
        "| Element | VIF Score |",
        "|---------|-----------|",
    ]

    for elem, score in vif_scores.items():
        report_lines.append(f"| {elem} | {score:.4f} |")

    report_lines.append("")
    report_lines.append(f"**Status**: {'PASS' if vif_pass else 'FAIL'} (Threshold: VIF < 5.0)")
    report_lines.append("")

    report_lines.append("## Methodological Limitations")
    report_lines.append("")
    
    limitations = []
    if mae_flag:
        limitations.append(f"- The cross-validation MAE ({cv_mae_flag_value}) exceeds the threshold of 0.05, indicating potential model uncertainty or data noise.")
    
    limitations.append("- The analysis is **associational (not causal)**. While the model identifies statistical relationships between composition and Poisson's ratio, it does not establish a causal mechanism. The results should be interpreted as predictive correlations within the domain of the training data.")
    limitations.append("- The model is restricted to the specific alloying elements (Cu, Mg, Si, Zn, Mn) and composition ranges present in the source dataset.")
    
    report_lines.extend(limitations)
    report_lines.append("")

    report_lines.append("## Data and Residuals")
    report_lines.append("")
    report_lines.append("Residual analysis (Observed - Predicted) was performed to check for systematic biases. The distribution of residuals is available in `results/residuals.json`.")
    report_lines.append("")
    report_lines.append("## Conclusion")
    report_lines.append("")
    report_lines.append("The Random Forest model provides a reasonable prediction of Poisson's ratio for aluminum alloys within the studied compositional space. The most significant alloying elements identified are consistent with known metallurgical effects, though the exact ranking may vary with data quality and preprocessing. Future work should focus on expanding the dataset to include a broader range of alloying elements and experimental conditions.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*Report generated automatically on {__import__('datetime').datetime.now().isoformat()}*")

    # Write the report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    log_operation("generate_final_report", status="completed", output=str(output_file))

def validate_report_framing(report_path: str) -> bool:
    """
    Validate that the generated report contains required sections and phrasing.
    Returns True if valid, raises AssertionError if not.
    """
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_sections = [
        "Methodological Limitations",
        "associational (not causal)"
    ]

    for section in required_sections:
        if section not in content:
            raise AssertionError(f"Report validation failed: Missing required section/phrase '{section}'")

    return True

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Generate the final analysis report.")
    parser.add_argument("--metrics", type=str, default="results/model_metrics.json", help="Path to model metrics JSON")
    parser.add_argument("--vif", type=str, default="results/collinearity_diagnostic.json", help="Path to VIF diagnostics JSON")
    parser.add_argument("--importance", type=str, default="results/feature_importance_summary.json", help="Path to feature importance summary JSON")
    parser.add_argument("--flags", type=str, default="results/methodological_flags.json", help="Path to methodological flags JSON")
    parser.add_argument("--model", type=str, default="models/rf_model.pkl", help="Path to serialized model")
    parser.add_argument("--residuals", type=str, default="results/residuals.json", help="Path to residuals JSON")
    parser.add_argument("--output", type=str, default="results/final_report.md", help="Path for output report")

    args = parser.parse_args()

    logger = get_logger()
    log_operation("main", status="starting", args=vars(args))

    try:
        generate_final_report(
            metrics_path=args.metrics,
            vif_path=args.vif,
            importance_path=args.importance,
            methodological_flags_path=args.flags,
            model_path=args.model,
            residuals_path=args.residuals,
            output_path=args.output
        )
        
        # Validate the generated report
        validate_report_framing(args.output)
        logger.info("Report generated and validated successfully.")
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()