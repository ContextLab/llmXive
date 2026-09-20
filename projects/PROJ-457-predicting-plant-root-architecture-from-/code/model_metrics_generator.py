"""
Model Metrics Generator (T029a)

Generates output JSON with adjusted R², RMSE, p-values, and cross-validation mean R²
for both LMM and Random Forest models. Consumes sensitivity analysis results.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from project API surface
from config import get_config, setup_logging
from modeling import evaluate_model, calculate_r2_delta, evaluate_success_criterion

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and return JSON content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Required file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

def save_json_file(file_path: Path, data: Dict[str, Any]) -> None:
    """Save data as JSON to a file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logging.info(f"Saved JSON to {file_path}")

def generate_model_metrics_report(
    model_results_path: Path,
    sensitivity_analysis_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate the raw metrics report for T029a.

    Consumes:
      - model_results_path: Output from modeling.py (T023-T027)
      - sensitivity_analysis_path: Output from T028b/T028c

    Produces:
      - JSON with adjusted R², RMSE, p-values, CV mean R² for LMM and RF.
    """
    logger = logging.getLogger(__name__)

    # Load model results (expected to contain lmm and rf metrics)
    logger.info(f"Loading model results from {model_results_path}")
    model_results = load_json_file(model_results_path)

    # Load sensitivity analysis (T028b/c output)
    logger.info(f"Loading sensitivity analysis from {sensitivity_analysis_path}")
    sensitivity_data = load_json_file(sensitivity_analysis_path)

    # Extract LMM metrics
    lmm_metrics = model_results.get('lmm', {})
    lmm_adjusted_r2 = lmm_metrics.get('adjusted_r_squared')
    lmm_rmse = lmm_metrics.get('rmse')
    lmm_p_values = lmm_metrics.get('p_values', {})
    lmm_cv_r2 = lmm_metrics.get('cv_mean_r_squared')

    # Extract Random Forest metrics
    rf_metrics = model_results.get('random_forest', {})
    rf_r2 = rf_metrics.get('r_squared')
    rf_rmse = rf_metrics.get('rmse')
    rf_cv_r2 = rf_metrics.get('cv_mean_r_squared')

    # Build the report
    report = {
        "task_id": "T029a",
        "description": "Raw model metrics generation",
        "lmm": {
            "adjusted_r_squared": lmm_adjusted_r2,
            "rmse": lmm_rmse,
            "p_values": lmm_p_values,
            "cv_mean_r_squared": lmm_cv_r2
        },
        "random_forest": {
            "r_squared": rf_r2,
            "rmse": rf_rmse,
            "cv_mean_r_squared": rf_cv_r2
        },
        "sensitivity_reference": {
            "literature_overlap": sensitivity_data.get("literature_overlap"),
            "observed_coefficient": sensitivity_data.get("observed_coefficient"),
            "percent_deviation": sensitivity_data.get("percent_deviation")
        }
    }

    # Validate critical fields are not None
    required_fields = [
        ("lmm", "adjusted_r_squared"),
        ("lmm", "rmse"),
        ("lmm", "cv_mean_r_squared"),
        ("random_forest", "r_squared"),
        ("random_forest", "rmse"),
        ("random_forest", "cv_mean_r_squared")
    ]

    for section, field in required_fields:
        if report[section][field] is None:
            raise ValueError(f"Missing required metric: {section}.{field}")

    logger.info(f"Generated metrics report: {report}")
    return report

def main() -> int:
    """Main entry point for T029a."""
    config = get_config()
    setup_logging()
    logger = logging.getLogger(__name__)

    # Define paths
    project_root = Path(config.get('PROJECT_ROOT', '.'))
    model_results_path = project_root / config.get('MODEL_RESULTS_PATH', 'artifacts/model_results.json')
    sensitivity_analysis_path = project_root / config.get('SENSITIVITY_ANALYSIS_PATH', 'artifacts/sensitivity/sensitivity_analysis.json')
    output_path = project_root / config.get('MODEL_METRICS_OUTPUT_PATH', 'artifacts/reports/model_metrics_raw.json')

    logger.info(f"Starting T029a: Model Metrics Generation")
    logger.info(f"Model Results: {model_results_path}")
    logger.info(f"Sensitivity Analysis: {sensitivity_analysis_path}")
    logger.info(f"Output: {output_path}")

    try:
        # Generate the report
        report = generate_model_metrics_report(
            model_results_path,
            sensitivity_analysis_path,
            output_path
        )

        # Save the report
        save_json_file(output_path, report)

        logger.info("T029a completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data or missing metrics: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T029a: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
