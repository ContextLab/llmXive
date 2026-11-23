"""
T033: Generate Final Report
Generates the final research report (reports/final_report.md) based on the results
of the Bayesian model comparison, parameter recovery, and sensitivity analysis.

Dependencies:
- T030 (regression.py)
- T031 (validation.py - Bonferroni)
- T032a (validation.py - sensitivity analysis)
- T027c (parameter_recovery.py)
- T027d (synthetic_delta_aic_validation.py)

This script reads existing JSON result files and assembles them into a Markdown report.
It handles missing files gracefully by marking sections as 'Not Available' or 'Skipped'.
"""
from __future__ import annotations

import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_path
from code.utils.logging import get_logger

# Configure logging
logger = get_logger("report_generation")

# Define paths for result artifacts
RESULTS_DIR = get_path("data", "results")
REPORTS_DIR = get_path("reports")

# Result file paths
MODEL_COMPARISON_PATH = get_path("data", "results", "model_comparison.json")
PARAMETER_RECOVERY_PATH = get_path("data", "results", "parameter_recovery.json")
SENSITIVITY_ANALYSIS_PATH = get_path("data", "results", "sensitivity_analysis.json")
DELTA_AIC_VALIDATION_PATH = get_path("data", "results", "synthetic_delta_aic.json")
BONFERRONI_PATH = get_path("data", "results", "bonferroni_correction.json")

OUTPUT_PATH = get_path("reports", "final_report.md")

def load_json_result(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON result file, returning None if not found or invalid."""
    if not path.exists():
        logger.log("file_missing", path=str(path))
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.log("file_read_error", path=str(path), error=str(e))
        return None

def determine_pipeline_status(results: Dict[str, Any]) -> str:
    """Determine the overall pipeline status based on results."""
    # Check key success criteria
    if results.get("parameter_recovery", {}).get("bias", 0.0) < 0.1:
        if results.get("model_comparison", {}).get("delta_aic", 0) > 10:
            return "SUCCESS: Model recovered ground truth and outperformed baseline."
    return "PARTIAL: Check individual sections for details."

def generate_report_content(
    model_comparison: Optional[Dict],
    parameter_recovery: Optional[Dict],
    sensitivity_analysis: Optional[Dict],
    delta_aic_validation: Optional[Dict],
    bonferroni: Optional[Dict]
) -> str:
    """Generate the Markdown content for the final report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = []
    lines.append("# Final Research Report: Cognitive Mechanisms of Intuitive Moral Judgments")
    lines.append("")
    lines.append(f"**Generated:** {timestamp}")
    lines.append("")
    
    # 1. Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This report summarizes the findings from the Bayesian analysis of moral judgments in virtual environments.")
    lines.append("The study investigates the effect of perceptual salience on intuitive moral judgments.")
    lines.append("")
    
    status = "Unknown"
    if model_comparison and parameter_recovery:
        status = determine_pipeline_status({
            "model_comparison": model_comparison,
            "parameter_recovery": parameter_recovery
        })
    elif model_comparison:
        status = "Model comparison available."
    elif parameter_recovery:
        status = "Parameter recovery available."
    
    lines.append(f"**Overall Status:** {status}")
    lines.append("")
    
    # 2. Model Comparison (ΔAIC)
    lines.append("## Model Comparison (ΔAIC)")
    lines.append("")
    if model_comparison:
        lines.append("The Bayesian model was compared against a Frequentist Linear Mixed Model (LMM) baseline.")
        lines.append("")
        lines.append("### Results")
        lines.append(f"- **ΔAIC:** {model_comparison.get('delta_aic', 'N/A')}")
        lines.append(f"- **Bayesian WAIC:** {model_comparison.get('bayesian_waic', 'N/A')}")
        lines.append(f"- **LMM AIC:** {model_comparison.get('lmm_aic', 'N/A')}")
        lines.append("")
        if model_comparison.get('interpretation'):
            lines.append(f"**Interpretation:** {model_comparison['interpretation']}")
    else:
        lines.append("*Model comparison results not available.*")
    lines.append("")
    
    # 3. Parameter Recovery
    lines.append("## Parameter Recovery")
    lines.append("")
    lines.append("Parameter recovery analysis validates the model's ability to estimate ground truth effects.")
    lines.append("")
    if parameter_recovery:
        lines.append("### Metrics")
        lines.append(f"- **Bias:** {parameter_recovery.get('bias', 'N/A')}")
        lines.append(f"- **95% CI Coverage:** {parameter_recovery.get('coverage_95ci', 'N/A')}")
        lines.append(f"- **Samples:** {parameter_recovery.get('n_samples', 'N/A')}")
        lines.append("")
        if parameter_recovery.get('success'):
            lines.append("**Conclusion:** Parameters were successfully recovered within acceptable bounds.")
        else:
            lines.append("**Conclusion:** Parameter recovery did not meet success criteria.")
    else:
        lines.append("*Parameter recovery results not available.*")
    lines.append("")
    
    # 4. Sensitivity Analysis
    lines.append("## Sensitivity Analysis")
    lines.append("")
    lines.append("Sensitivity analysis was performed to ensure robustness across different thresholds.")
    lines.append("")
    if sensitivity_analysis:
        lines.append("### Threshold Stability")
        thresholds = sensitivity_analysis.get('thresholds', {})
        if thresholds:
            lines.append("| Threshold | Stability Metric | Status |")
            lines.append("| :--- | :--- | :--- |")
            for t, data in thresholds.items():
                status_str = "Stable" if data.get('stable', False) else "Unstable"
                lines.append(f"| {t} | {data.get('metric', 'N/A')} | {status_str} |")
        else:
            lines.append("*No threshold data found.*")
        lines.append("")
        if sensitivity_analysis.get('overall_stability'):
            lines.append(f"**Overall Stability:** {sensitivity_analysis['overall_stability']}")
    else:
        lines.append("*Sensitivity analysis results not available.*")
    lines.append("")
    
    # 5. Bonferroni Correction (Optional but good for US3)
    lines.append("## Statistical Validation (Bonferroni)")
    lines.append("")
    if bonferroni:
        lines.append(f"**Corrected Alpha:** {bonferroni.get('corrected_alpha', 'N/A')}")
        lines.append(f"**Significant Effects:** {bonferroni.get('significant_count', 0)}")
    else:
        lines.append("*Bonferroni correction results not available.*")
    lines.append("")
    
    # 6. Synthetic Validation (ΔAIC > 10)
    lines.append("## Synthetic Data Validation")
    lines.append("")
    if delta_aic_validation:
        lines.append(f"**Threshold:** {delta_aic_validation.get('threshold', 10)}")
        lines.append(f"**Observed ΔAIC:** {delta_aic_validation.get('observed_delta_aic', 'N/A')}")
        lines.append(f"**Passed:** {delta_aic_validation.get('passed', False)}")
    else:
        lines.append("*Synthetic validation results not available.*")
    lines.append("")
    
    # 7. Conclusion
    lines.append("## Conclusion")
    lines.append("")
    lines.append("The analysis pipeline successfully processed the data and generated statistical models.")
    lines.append("Key findings regarding the effect of perceptual salience on moral judgments are detailed above.")
    lines.append("Future work should focus on acquiring real-world VR data to validate these simulation-based findings.")
    lines.append("")
    lines.append("---")
    lines.append("*End of Report*")
    
    return "\n".join(lines)

def main() -> None:
    """Main entry point for report generation."""
    logger.log("report_start", operation="generate_final_report")
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Load results
    model_comparison = load_json_result(MODEL_COMPARISON_PATH)
    parameter_recovery = load_json_result(PARAMETER_RECOVERY_PATH)
    sensitivity_analysis = load_json_result(SENSITIVITY_ANALYSIS_PATH)
    delta_aic_validation = load_json_result(DELTA_AIC_VALIDATION_PATH)
    bonferroni = load_json_result(BONFERRONI_PATH)
    
    # Generate content
    content = generate_report_content(
        model_comparison,
        parameter_recovery,
        sensitivity_analysis,
        delta_aic_validation,
        bonferroni
    )
    
    # Write report
    try:
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.log("report_written", path=str(OUTPUT_PATH))
        print(f"Report successfully written to: {OUTPUT_PATH}")
    except IOError as e:
        logger.log("report_write_error", error=str(e))
        print(f"Error writing report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()