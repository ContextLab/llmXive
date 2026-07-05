import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.utils.logging import get_logger

logger = get_logger(__name__)

# FR-007 Compliance Constant
ASSOCIATIVE_DISCLAIMER = (
  "DISCLAIMER: The relationships identified in this analysis are associative, not causal. "
  "While functional traits may correlate with species distribution model performance, "
  "these correlations do not imply that the traits directly cause the observed distribution patterns. "
  "Confounding variables, environmental covariates, and phylogenetic constraints may influence "
  "both trait values and distribution outcomes. Results should be interpreted as predictive "
  "associations rather than mechanistic drivers."
)

def generate_final_report(
    results_path: str,
    stats_results: Dict[str, Any],
    model_results: Dict[str, Any],
    sensitivity_results: Optional[Dict[str, Any]] = None,
    include_disclaimer: bool = True
) -> Path:
    """
    Generate the final JSON report with explicit associative disclaimer (FR-007).

    Args:
        results_path: Directory where the report will be saved.
        stats_results: Dictionary containing statistical test results (t-test, LMM, etc.).
        model_results: Dictionary containing model performance metrics (AUC, TSS).
        sensitivity_results: Optional dictionary containing sensitivity analysis results.
        include_disclaimer: If True, adds the FR-007 compliance disclaimer to the report.

    Returns:
        Path to the generated report file.
    """
    logger.info(f"Generating final report at {results_path}")

    report_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "project_id": "PROJ-478-assessing-the-predictive-power-of-plant-traits",
            "version": "1.0.0"
        },
        "results": {
            "model_performance": model_results,
            "statistical_analysis": stats_results
        }
    }

    if sensitivity_results:
        report_data["results"]["sensitivity_analysis"] = sensitivity_results

    # FR-007: Explicit disclaimer logic
    if include_disclaimer:
        report_data["compliance"] = {
            "fr_007_associative_disclaimer": ASSOCIATIVE_DISCLAIMER,
            "causality_warning": (
                "This study does not claim causal inference. "
                "All reported improvements in predictive power are correlational."
            )
        }
    else:
        logger.warning("FR-007 disclaimer was explicitly excluded from the report.")

    # Ensure directory exists
    output_file = Path(results_path) / "final_report.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=str)

    logger.info(f"Final report saved to {output_file}")
    return output_file

def generate_stats_report(
    stats_results: Dict[str, Any],
    output_path: str
) -> Path:
    """
    Generate a specific JSON report for statistical analysis results.

    Args:
        stats_results: Dictionary containing t-test, LMM, and effect size results.
        output_path: Directory where the report will be saved.

    Returns:
        Path to the generated report file.
    """
    logger.info(f"Generating stats report at {output_path}")

    report_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "analysis_type": "comparative_statistical_analysis"
        },
        "disclaimer": ASSOCIATIVE_DISCLAIMER,
        "results": stats_results
    }

    output_file = Path(output_path) / "stats_report.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=str)

    logger.info(f"Stats report saved to {output_file}")
    return output_file

def generate_model_report(
    model_results: Dict[str, Any],
    output_path: str
) -> Path:
    """
    Generate a specific JSON report for model performance results.

    Args:
        model_results: Dictionary containing AUC, TSS, and cross-validation metrics.
        output_path: Directory where the report will be saved.

    Returns:
        Path to the generated report file.
    """
    logger.info(f"Generating model report at {output_path}")

    report_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "analysis_type": "model_performance_evaluation"
        },
        "disclaimer": ASSOCIATIVE_DISCLAIMER,
        "results": model_results
    }

    output_file = Path(output_path) / "model_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=str)

    logger.info(f"Model report saved to {output_file}")
    return output_file
