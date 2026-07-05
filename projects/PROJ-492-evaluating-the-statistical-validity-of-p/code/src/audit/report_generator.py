"""
CSV summary generator for the A/B test audit pipeline.

Reads the audit report JSON produced by the validator and generates a
summary CSV report containing aggregate statistics required for the
final deliverable.

Outputs:
    output/summary_report.csv: Contains columns:
        - total_summaries
        - inconsistent_count
        - inconsistent_rate
        - bias_adjusted_rate
        - wilson_ci_lower
        - wilson_ci_upper
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)


def load_audit_records(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load audit records from the JSON report file.

    Args:
        json_path: Path to the audit_report.json file.

    Returns:
        List of audit record dictionaries.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the JSON is malformed.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Audit report not found at {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'records' in data:
        return data['records']
    else:
        # Fallback: treat the whole dict as a single record or empty list
        logger.warning(f"Unexpected JSON structure in {json_path}, attempting to process as list")
        return [data] if isinstance(data, dict) else []


def load_prevalence_data(json_path: Path) -> Dict[str, float]:
    """
    Load prevalence and bias-adjusted data from the prevalence JSON file.

    Expected keys in the JSON:
        - 'bias_adjusted_rate': float
        - 'wilson_ci_lower': float
        - 'wilson_ci_upper': float

    Args:
        json_path: Path to the prevalence.json file.

    Returns:
        Dictionary containing the required fields.

    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If required fields are missing.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Prevalence data not found at {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    required_fields = ['bias_adjusted_rate', 'wilson_ci_lower', 'wilson_ci_upper']
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise KeyError(f"Missing required fields in prevalence data: {missing}")

    return {
        'bias_adjusted_rate': float(data['bias_adjusted_rate']),
        'wilson_ci_lower': float(data['wilson_ci_lower']),
        'wilson_ci_upper': float(data['wilson_ci_upper'])
    }


def calculate_summary_statistics(audit_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics from audit records.

    Args:
        audit_records: List of audit record dictionaries.

    Returns:
        Dictionary with total count and inconsistent count.
    """
    total = len(audit_records)
    inconsistent = sum(1 for r in audit_records if r.get('is_inconsistent', False))

    rate = inconsistent / total if total > 0 else 0.0

    return {
        'total_summaries': total,
        'inconsistent_count': inconsistent,
        'inconsistent_rate': rate
    }


def generate_summary_report(
    audit_json_path: Path,
    prevalence_json_path: Path,
    output_csv_path: Path
) -> Path:
    """
    Generate the summary CSV report.

    Reads the audit report and prevalence data, calculates aggregates,
    and writes the summary CSV.

    Args:
        audit_json_path: Path to audit_report.json.
        prevalence_json_path: Path to prevalence.json.
        output_csv_path: Path where the summary CSV will be written.

    Returns:
        Path to the generated CSV file.

    Raises:
        FileNotFoundError: If input files are missing.
        KeyError: If required data fields are missing.
    """
    logger.info(f"Generating summary report from {audit_json_path} and {prevalence_json_path}")

    # Load data
    audit_records = load_audit_records(audit_json_path)
    prevalence_data = load_prevalence_data(prevalence_json_path)

    # Calculate statistics
    stats = calculate_summary_statistics(audit_records)

    # Prepare row data
    row = {
        'total_summaries': stats['total_summaries'],
        'inconsistent_count': stats['inconsistent_count'],
        'inconsistent_rate': round(stats['inconsistent_rate'], 6),
        'bias_adjusted_rate': round(prevalence_data['bias_adjusted_rate'], 6),
        'wilson_ci_lower': round(prevalence_data['wilson_ci_lower'], 6),
        'wilson_ci_upper': round(prevalence_data['wilson_ci_upper'], 6)
    }

    # Ensure output directory exists
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    fieldnames = [
        'total_summaries',
        'inconsistent_count',
        'inconsistent_rate',
        'bias_adjusted_rate',
        'wilson_ci_lower',
        'wilson_ci_upper'
    ]

    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)

    logger.info(f"Summary report written to {output_csv_path}")
    return output_csv_path


def main() -> int:
    """
    Main entry point for the report generator script.

    Reads from default paths:
        - output/audit_report.json
        - output/prevalence.json
    Writes to:
        - output/summary_report.csv

    Returns:
        0 on success, 1 on failure.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / 'output'

    audit_json = output_dir / 'audit_report.json'
    prevalence_json = output_dir / 'prevalence.json'
    output_csv = output_dir / 'summary_report.csv'

    try:
        generate_summary_report(audit_json, prevalence_json, output_csv)
        logger.info("Report generation completed successfully.")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        return 1
    except KeyError as e:
        logger.error(f"Missing required data field: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
