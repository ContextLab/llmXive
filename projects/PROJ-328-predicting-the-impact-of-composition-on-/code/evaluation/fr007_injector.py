"""
Integration point for FR-007 warnings in the evaluation pipeline.

This module ensures that after model training, SHAP analysis, and comparison,
the mandatory associational warnings are injected into the generated artifacts.
"""
import logging
from pathlib import Path
from typing import List, Optional

from utils.fr007_warnings import (
    inject_warning_into_json_output,
    inject_warning_into_yaml_output,
    ASSOCIATIONAL_WARNING_TEXT
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

def inject_warnings_into_evaluation_outputs(
    model_results_paths: List[Path],
    comparison_report_path: Optional[Path] = None,
    sensitivity_path: Optional[Path] = None,
    shap_path: Optional[Path] = None
) -> None:
    """
    Centralized function to inject FR-007 warnings into all evaluation outputs.
    
    Args:
        model_results_paths: List of paths to JSON model result files.
        comparison_report_path: Path to the JSON comparison report.
        sensitivity_path: Path to the YAML sensitivity analysis file.
        shap_path: Path to the JSON SHAP analysis file.
    """
    warning_text = ASSOCIATIONAL_WARNING_TEXT

    # Inject into model results
    for path in model_results_paths:
        if path.exists():
            inject_warning_into_json_output(path, warning_text)
        else:
            logger.warning(f"Model results file not found: {path}")

    # Inject into comparison report
    if comparison_report_path and comparison_report_path.exists():
        inject_warning_into_json_output(comparison_report_path, warning_text)
    
    # Inject into sensitivity analysis
    if sensitivity_path and sensitivity_path.exists():
        inject_warning_into_yaml_output(sensitivity_path, warning_text)
    
    # Inject into SHAP analysis
    if shap_path and shap_path.exists():
        inject_warning_into_json_output(shap_path, warning_text)

def main():
    """
    Entry point for the evaluation pipeline to trigger FR-007 injection.
    """
    # Determine base paths relative to this file's location
    base_dir = Path(__file__).parent.parent.parent
    models_dir = base_dir / "models"
    data_processed_dir = base_dir / "data" / "processed"

    # Define the artifacts that should have warnings injected
    # These names match the outputs of T023, T024, T027, T028, T029
    artifacts = {
        "model_results": [
            models_dir / "xgboost_results.json",
            models_dir / "linear_regression_results.json"
        ],
        "comparison_report": models_dir / "comparison_report.json",
        "sensitivity_analysis": data_processed_dir / "sensitivity_analysis.yaml",
        "shap_analysis": models_dir / "shap_summary.json"
    }

    inject_warnings_into_evaluation_outputs(
        model_results_paths=artifacts["model_results"],
        comparison_report_path=artifacts["comparison_report"],
        sensitivity_path=artifacts["sensitivity_analysis"],
        shap_path=artifacts["shap_analysis"]
    )

    logger.info("FR-007 Associational Framing Warnings successfully injected into all evaluation outputs.")

if __name__ == "__main__":
    main()
