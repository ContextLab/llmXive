"""
Report Generator Module for T047.

Implements the CSV summary generator that reads the audit report JSON
and writes the summary report CSV with required statistical columns.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)


def load_audit_records(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load audit records from the JSON audit report.

    Args:
        input_path: Path to audit_report.json

    Returns:
        List of audit record dictionaries.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Audit report not found at {input_path}")

    logger.info(f"Loading audit records from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and 'records' in data:
        records = data['records']
    else:
        records = [data] if data else []

    logger.info(f"Loaded {len(records)} audit records")
    return records


def load_prevalence_data(prevalence_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load prevalence analysis results from the prevalence JSON file.

    Args:
        prevalence_path: Path to prevalence.json

    Returns:
        Prevalence data dictionary or None if file doesn't exist.
    """
    if not prevalence_path.exists():
        logger.warning(f"Prevalence file not found at {prevalence_path}. "
                     "Wilson CI values will be set to 0.0.")
        return None

    logger.info(f"Loading prevalence data from {prevalence_path}")
    with open(prevalence_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_summary_statistics(
    audit_records: List[Dict[str, Any]],
    prevalence_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate summary statistics from audit records and prevalence data.

    Args:
        audit_records: List of audit record dictionaries.
        prevalence_data: Optional prevalence analysis results.

    Returns:
        Dictionary containing summary statistics.
    """
    total_summaries = len(audit_records)
    inconsistent_count = sum(
        1 for record in audit_records
        if record.get('is_inconsistent', False)
    )

    # Calculate inconsistent rate
    if total_summaries > 0:
        inconsistent_rate = inconsistent_count / total_summaries
    else:
        inconsistent_rate = 0.0

    # Get bias-adjusted rate and Wilson CI from prevalence data
    bias_adjusted_rate = 0.0
    wilson_ci_lower = 0.0
    wilson_ci_upper = 0.0

    if prevalence_data:
        # Extract bias-adjusted rate
        bias_adjusted_rate = prevalence_data.get('bias_adjusted_rate', 0.0)

        # Extract Wilson CI bounds
        wilson_ci_lower = prevalence_data.get('wilson_ci_lower', 0.0)
        wilson_ci_upper = prevalence_data.get('wilson_ci_upper', 0.0)

        # Validate CI bounds
        if not (0.0 <= wilson_ci_lower <= 1.0):
            logger.warning(f"Invalid Wilson CI lower bound: {wilson_ci_lower}")
            wilson_ci_lower = 0.0
        if not (0.0 <= wilson_ci_upper <= 1.0):
            logger.warning(f"Invalid Wilson CI upper bound: {wilson_ci_upper}")
            wilson_ci_upper = 0.0

    logger.info(f"Calculated summary statistics: "
              f"total={total_summaries}, inconsistent={inconsistent_count}, "
              f"rate={inconsistent_rate:.4f}")

    return {
        'total_summaries': total_summaries,
        'inconsistent_count': inconsistent_count,
        'inconsistent_rate': inconsistent_rate,
        'bias_adjusted_rate': bias_adjusted_rate,
        'wilson_ci_lower': wilson_ci_lower,
        'wilson_ci_upper': wilson_ci_upper
    }


def generate_summary_report(
    statistics: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write summary statistics to a CSV file.

    Args:
        statistics: Dictionary containing summary statistics.
        output_path: Path to the output CSV file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Define required columns in exact order
    fieldnames = [
        'total_summaries',
        'inconsistent_count',
        'inconsistent_rate',
        'bias_adjusted_rate',
        'wilson_ci_lower',
        'wilson_ci_upper'
    ]

    logger.info(f"Writing summary report to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(statistics)

    logger.info(f"Successfully wrote summary report with {len(fieldnames)} columns")


def main() -> int:
    """
    Main entry point for the report generator script.

    Reads output/audit_report.json and output/prevalence.json,
    computes summary statistics, and writes output/summary_report.csv.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    try:
        # Define paths relative to project root
        base_path = Path(__file__).resolve().parent.parent.parent.parent
        audit_report_path = base_path / 'output' / 'audit_report.json'
        prevalence_path = base_path / 'output' / 'prevalence.json'
        output_path = base_path / 'output' / 'summary_report.csv'

        logger.info("Starting report generation for T047")

        # Load audit records
        audit_records = load_audit_records(audit_report_path)

        # Load prevalence data (may be optional)
        prevalence_data = load_prevalence_data(prevalence_path)

        # Calculate summary statistics
        statistics = calculate_summary_statistics(audit_records, prevalence_data)

        # Generate CSV report
        generate_summary_report(statistics, output_path)

        logger.info("Report generation completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in input file: {e}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        return 3


if __name__ == '__main__':
    import sys
    sys.exit(main())
