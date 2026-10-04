from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from config import get_config
from logging_config import get_logger, log_operation

CONFIG = get_config()
logger = get_logger("main")

def load_json_safe(path: str) -> Any:
    """Load a JSON file, handling missing files."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required JSON file not found: {path}")
    with open(p, "r") as f:
        return json.load(f)

def load_parquet_safe(path: str) -> pd.DataFrame:
    """Load a parquet file, handling missing files."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required parquet file not found: {path}")
    return pd.read_parquet(p)

def generate_final_report() -> None:
    """Generate the final report from aggregated context."""
    context_path = Path(CONFIG.data_processed) / "report_context.json"
    if not context_path.exists():
        raise FileNotFoundError(f"Report context not found: {context_path}")
    
    context = load_json_safe(str(context_path))
    
    # Extract relevant sections
    model_metrics = context.get("model_metrics", {})
    collinearity = context.get("collinearity_diagnostic", {})
    feature_importance = context.get("feature_importance_summary", {})
    methodological_flags = context.get("methodological_flags", {})
    
    # Build report content
    report_lines = [
        "# Final Report: Predicting Poisson's Ratio of Aluminum Alloys",
        "",
        "## Summary",
        "This report presents the results of a machine learning model trained to predict the Poisson's ratio of aluminum alloys based on their elemental composition.",
        "",
        "## Model Performance",
        f"- Cross-Validation MAE: {model_metrics.get('cv_mae', 'N/A'):.4f}",
        f"- CV 95% CI: [{model_metrics.get('cv_ci_lower', 'N/A'):.4f}, {model_metrics.get('cv_ci_upper', 'N/A'):.4f}]",
        f"- Test Set MAE: {model_metrics.get('test_mae', 'N/A'):.4f}",
        "",
        "## Feature Importance",
    ]
    
    if feature_importance:
        report_lines.append(f"- Top Element: {feature_importance.get('top_element', 'N/A')}")
        report_lines.append(f"- Second Element: {feature_importance.get('second_element', 'N/A')}")
        report_lines.append(f"- Importance Ratio: {feature_importance.get('ratio', 'N/A'):.2f}")
    
    report_lines.extend([
        "",
        "## Collinearity Diagnostic",
        f"- ILR VIF Pass Flag: {collinearity.get('pass_flag', 'N/A')}",
        "",
        "## Methodological Limitations",
    ])
    
    if methodological_flags.get("mae_flag"):
        report_lines.append(methodological_flags.get("narrative_limitation", ""))
    
    if not collinearity.get("pass_flag", True):
        report_lines.append("High collinearity detected in ILR features (VIF > 5). The model uses ILR transformation to mitigate this, but interpretability is limited.")
    
    report_lines.extend([
        "",
        "## Disclaimer",
        "The results presented in this report are **associational (not causal)**. The model identifies statistical patterns in the data but does not establish causal relationships between alloy composition and Poisson's ratio.",
        ""
    ])
    
    report_content = "\n".join(report_lines)
    
    # Save report
    report_path = Path(CONFIG.results) / "final_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report_content)
    
    logger.info(f"Final report saved to {report_path}")

def validate_report_framing() -> bool:
    """Validate that the report contains required framing."""
    report_path = Path(CONFIG.results) / "final_report.md"
    if not report_path.exists():
        return False
    
    with open(report_path, "r") as f:
        content = f.read()
    
    # Check for required phrases
    has_limitations = "Methodological Limitations" in content
    has_disclaimer = "associational (not causal)" in content.lower()
    
    return has_limitations and has_disclaimer

def main() -> None:
    """Main entry point for report generation."""
    log_operation("report_generation_start")
    
    # Aggregate context for report (if not already done)
    # This task assumes T030a-aggregate has run, but we can do a quick check
    context_path = Path(CONFIG.data_processed) / "report_context.json"
    if not context_path.exists():
        # If context is missing, we try to aggregate here as a fallback
        # This ensures the pipeline doesn't fail if T030a-aggregate was skipped
        aggregate_report_context()
    
    generate_final_report()
    
    if not validate_report_framing():
        logger.warning("Report validation failed: missing required framing.")
        sys.exit(1)
    
    log_operation("report_generation_end")

def aggregate_report_context() -> None:
    """Aggregate all results into report_context.json."""
    # Load all required artifacts
    model_metrics = load_json_safe(str(Path(CONFIG.results) / "model_metrics.json"))
    collinearity = load_json_safe(str(Path(CONFIG.results) / "collinearity_diagnostic.json"))
    feature_importance = load_json_safe(str(Path(CONFIG.results) / "feature_importance_summary.json"))
    methodological_flags = load_json_safe(str(Path(CONFIG.results) / "methodological_flags.json"))
    residuals = load_json_safe(str(Path(CONFIG.results) / "residuals.json"))
    
    # Load model path (just the string)
    model_path = str(Path(CONFIG.models) / "rf_model.pkl")
    
    context = {
        "model_metrics": model_metrics,
        "collinearity_diagnostic": collinearity,
        "feature_importance_summary": feature_importance,
        "methodological_flags": methodological_flags,
        "residuals": residuals,
        "model_path": model_path
    }
    
    context_path = Path(CONFIG.data_processed) / "report_context.json"
    context_path.parent.mkdir(parents=True, exist_ok=True)
    with open(context_path, "w") as f:
        json.dump(context, f, indent=2)
    
    logger.info(f"Report context aggregated to {context_path}")

if __name__ == "__main__":
    main()
