"""
Export Validator Module (T059, T060).

Validates consistency between the JSON audit report and the CSV summary report.
Logs ERR-201 if counts do not match.
"""
import json
import csv
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

logger = get_default_logger(__name__)


def load_audit_records_from_json(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load audit records from a JSON file.

    Args:
        json_path: Path to the JSON file containing audit records.

    Returns:
        List of audit record dictionaries.
    """
    if not json_path.exists():
        logger.error(f"JSON file not found: {json_path}")
        return []

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "records" in data:
                return data["records"]
            else:
                logger.warning(f"Unexpected JSON structure in {json_path}")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return []


def load_summary_counts_from_csv(csv_path: Path) -> Dict[str, int]:
    """
    Load summary counts from a CSV file.

    Expects a CSV with headers: total_summaries, inconsistent_count, ...

    Args:
        csv_path: Path to the CSV file.

    Returns:
        Dictionary with 'total_summaries' and 'inconsistent_count' keys.
    """
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return {"total_summaries": 0, "inconsistent_count": 0}

    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader, None)
            if row is None:
                logger.warning(f"CSV file is empty or has no header: {csv_path}")
                return {"total_summaries": 0, "inconsistent_count": 0}

            total = int(row.get("total_summaries", 0))
            inconsistent = int(row.get("inconsistent_count", 0))
            return {
                "total_summaries": total,
                "inconsistent_count": inconsistent
            }
    except (ValueError, KeyError) as e:
        logger.error(f"Failed to parse CSV counts: {e}")
        return {"total_summaries": 0, "inconsistent_count": 0}


def validate_export_consistency(
    json_records: List[Dict[str, Any]],
    csv_counts: Dict[str, int]
) -> Tuple[bool, Optional[str]]:
    """
    Validate that the JSON audit report counts match the CSV summary report counts.

    Args:
        json_records: List of audit records from JSON.
        csv_counts: Dictionary of counts from CSV.

    Returns:
        Tuple of (is_consistent, error_message).
        If inconsistent, error_message contains details and ERR-201 is logged.
    """
    # Calculate counts from JSON
    json_total = len(json_records)
    json_inconsistent = sum(1 for r in json_records if r.get("is_inconsistent", False))

    csv_total = csv_counts.get("total_summaries", 0)
    csv_inconsistent = csv_counts.get("inconsistent_count", 0)

    errors = []

    # Check total count
    if json_total != csv_total:
        errors.append(
            f"Total count mismatch: JSON has {json_total}, CSV has {csv_total}"
        )

    # Check inconsistent count
    if json_inconsistent != csv_inconsistent:
        errors.append(
            f"Inconsistent count mismatch: JSON has {json_inconsistent}, CSV has {csv_inconsistent}"
        )

    if errors:
        error_msg = "; ".join(errors)
        # Log ERR-201 as per requirement
        logger.error(f"ERR-201: Export consistency validation failed. {error_msg}")
        return False, error_msg

    logger.info("Export consistency validation passed.")
    return True, None


def run_export_validation(
    json_path: Path,
    csv_path: Path,
    raise_on_error: bool = False
) -> bool:
    """
    Run the full export validation pipeline.

    Args:
        json_path: Path to the audit report JSON.
        csv_path: Path to the summary report CSV.
        raise_on_error: If True, raise ValueError if validation fails.

    Returns:
        True if consistent, False otherwise.
    """
    logger.info(f"Starting export validation: JSON={json_path}, CSV={csv_path}")

    json_records = load_audit_records_from_json(json_path)
    csv_counts = load_summary_counts_from_csv(csv_path)

    is_consistent, error_message = validate_export_consistency(json_records, csv_counts)

    if not is_consistent and raise_on_error:
        raise ValueError(f"Export validation failed: {error_message}")

    return is_consistent


def main():
    """CLI entry point for export validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate export consistency between JSON and CSV reports.")
    parser.add_argument("--json", type=Path, required=True, help="Path to audit_report.json")
    parser.add_argument("--csv", type=Path, required=True, help="Path to summary_report.csv")
    parser.add_argument("--strict", action="store_true", help="Exit with error code if validation fails")

    args = parser.parse_args()

    success = run_export_validation(args.json, args.csv, raise_on_error=args.strict)

    if not success:
        logger.error("Validation failed. Check logs for ERR-201 details.")
        if args.strict:
            exit(1)
    else:
        logger.info("Validation successful.")
        exit(0)


if __name__ == "__main__":
    main()
