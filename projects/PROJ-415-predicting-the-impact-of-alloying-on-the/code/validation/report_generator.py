import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config import REPORTS_DIR, MODELS_DIR
from utils.logging import get_logger

logger = get_logger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_validation_report(
    metrics: Dict[str, Any],
    linear_coeffs: Dict[str, Any],
    bootstrap_ci: Dict[str, Any],
    stability_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assemble the final validation report containing all statistical metrics.
    """
    report = {
        "model_performance": {
            "rf": metrics.get("rf", {}),
            "gb": metrics.get("gb", {})
        },
        "linear_regression": {
            "size_mismatch_coefficient": linear_coeffs.get("size_mismatch_coefficient"),
            "p_value": linear_coeffs.get("p_value"),
            "intercept": linear_coeffs.get("intercept")
        },
        "statistical_significance": {
            "p_value_significant": linear_coeffs.get("p_value", 1.0) < 0.05,
            "bootstrap_95_ci": bootstrap_ci.get("ci_95", []),
            "ci_lower": bootstrap_ci.get("ci_95", [0, 0])[0],
            "ci_upper": bootstrap_ci.get("ci_95", [0, 0])[1]
        },
        "stability_analysis": {
            "threshold_range": stability_metrics.get("threshold_range", []),
            "classification_rate_variation": stability_metrics.get("variation", 0.0),
            "mean_classification_rate": stability_metrics.get("mean_rate", 0.0),
            "stability_verified": stability_metrics.get("verified", False),
            "verification_threshold": 0.05
        },
        "summary": {
            "r2_best": max(
                metrics.get("rf", {}).get("r2", -999),
                metrics.get("gb", {}).get("r2", -999)
            ),
            "rmse_best": min(
                metrics.get("rf", {}).get("rmse", 999),
                metrics.get("gb", {}).get("rmse", 999)
            ),
            "linear_significant": linear_coeffs.get("p_value", 1.0) < 0.05,
            "stability_passed": stability_metrics.get("verified", False)
        }
    }
    return report

def save_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Save the validation report to a JSON file."""
    if output_path is None:
        output_path = REPORTS_DIR / "validation_report.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")
    return output_path

def main():
    """
    Main entry point to generate the validation report.
    Consumes outputs from T025 (metrics), T023 (linear coeffs), T029 (bootstrap), T033 (stability).
    """
    logger.info("Starting validation report generation (T034)...")
    
    # Paths to dependency outputs
    metrics_path = MODELS_DIR / "metrics.json"
    linear_coeffs_path = MODELS_DIR / "linear_coef.json"
    bootstrap_path = MODELS_DIR / "bootstrap_results.json" # Assumed output from T029/T030
    stability_path = MODELS_DIR / "stability_results.json" # Assumed output from T033

    try:
        # Load dependencies
        logger.info(f"Loading metrics from {metrics_path}")
        metrics = load_json_file(metrics_path)

        logger.info(f"Loading linear coefficients from {linear_coeffs_path}")
        linear_coeffs = load_json_file(linear_coeffs_path)

        logger.info(f"Loading bootstrap results from {bootstrap_path}")
        bootstrap_ci = load_json_file(bootstrap_path)

        logger.info(f"Loading stability results from {stability_path}")
        stability_metrics = load_json_file(stability_path)

        # Generate report
        report = generate_validation_report(
            metrics=metrics,
            linear_coeffs=linear_coeffs,
            bootstrap_ci=bootstrap_ci,
            stability_metrics=stability_metrics
        )

        # Save report
        report_path = save_report(report)
        
        logger.info("Validation report generation completed successfully.")
        return report_path

    except FileNotFoundError as e:
        logger.error(f"Missing required dependency file: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        raise

if __name__ == "__main__":
    main()