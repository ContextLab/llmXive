"""
T014b: Aggregate Final Report

Aggregates the power limitation status from ingestion validation (T014)
and the model results from the evaluation report (T031c) into a single
final artifact for the paper draft.

Inputs:
  - data/processed/.ingestion_status.json (from T014)
  - data/processed/report.yaml (from T031c)

Output:
  - data/processed/final_aggregated_report.yaml
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_ingestion_status(path: Path) -> Optional[Dict[str, Any]]:
    """Load ingestion status JSON."""
    if not path.exists():
        logger.error(f"Ingestion status file not found: {path}")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ingestion status JSON: {e}")
        return None

def load_report_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Load evaluation report YAML."""
    if not path.exists():
        logger.error(f"Evaluation report file not found: {path}")
        return None
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse evaluation report YAML: {e}")
        return None

def aggregate_reports(
    ingestion_status: Dict[str, Any],
    evaluation_report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge ingestion status and evaluation report into a final aggregated report.
    """
    final_report = {
        "metadata": {
            "generated_by": "code/ingestion/aggregate_final_report.py (T014b)",
            "description": "Aggregated report combining data ingestion validation and model evaluation results."
        },
        "data_validation": {
            "threshold_status": ingestion_status.get("threshold_status", "UNKNOWN"),
            "exact_N": ingestion_status.get("exact_N", 0),
            "excluded_count": ingestion_status.get("excluded_count", 0),
            "power_limitation_warning": ingestion_status.get("power_limitation_warning", None)
        },
        "model_evaluation": {
            "model_comparison": evaluation_report.get("model_comparison", {}),
            "best_model": evaluation_report.get("best_model", "UNKNOWN"),
            "metrics": evaluation_report.get("metrics", {}),
            "warnings": evaluation_report.get("warnings", [])
        }
    }

    # Add cross-references if available
    if ingestion_status.get("power_limitation_warning"):
        final_report["metadata"]["data_quality_note"] = (
            "Model evaluation results should be interpreted with caution due to limited sample size."
        )

    return final_report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the final report to YAML."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Final aggregated report saved to: {output_path}")

def main():
    """Main entry point for T014b."""
    # Define paths relative to project root
    processed_dir = project_root / "data" / "processed"
    ingestion_status_path = processed_dir / ".ingestion_status.json"
    evaluation_report_path = processed_dir / "report.yaml"
    output_path = processed_dir / "final_aggregated_report.yaml"

    logger.info("Starting T014b: Aggregate Final Report")

    # Load inputs
    ingestion_status = load_ingestion_status(ingestion_status_path)
    if not ingestion_status:
        logger.error("FATAL: Could not load ingestion status. Cannot proceed.")
        sys.exit(1)

    evaluation_report = load_report_yaml(evaluation_report_path)
    if not evaluation_report:
        logger.error("FATAL: Could not load evaluation report. Cannot proceed.")
        sys.exit(1)

    # Aggregate
    final_report = aggregate_reports(ingestion_status, evaluation_report)

    # Save output
    save_report(final_report, output_path)

    logger.info("T014b completed successfully.")

if __name__ == "__main__":
    main()