import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

import pandas as pd

from src.utils.logger import get_logger

# PII patterns: SSN, email, phone, IP addresses, generic names
PII_PATTERNS: Dict[str, re.Pattern] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"),
    "ip_v4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "name": re.compile(r"\b[A-Z][a-z]{1,30}\s[A-Z][a-z]{1,30}\b"),
}

logger = get_logger("validation")


def get_project_root() -> Path:
    """Return the project root directory (parent of 'src')."""
    return Path(__file__).resolve().parent.parent.parent


def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def scan_for_pii(text: str, patterns: Optional[Dict[str, re.Pattern]] = None) -> List[Dict[str, Any]]:
    """
    Scan a text string for PII patterns.
    Returns a list of matches found with pattern type and matched text.
    """
    found = []
    patterns_to_check = patterns or PII_PATTERNS
    for p_name, pattern in patterns_to_check.items():
        for match in pattern.finditer(text):
            found.append({"type": p_name, "match": match.group(), "position": match.start()})
    return found


def validate_no_pii(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate a DataFrame for PII leakage in specified columns.
    If columns is None, checks all object/string columns.
    Returns a report dict: {'passed': bool, 'violations': list, 'checked_columns': list}
    """
    violations = []
    checked_columns = []

    if columns is None:
        # Select only object/string columns
        columns = df.select_dtypes(include=["object", "string"]).columns.tolist()

    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in DataFrame, skipping.")
            continue

        checked_columns.append(col)
        col_data = df[col].dropna().astype(str)

        for idx, val in col_data.items():
            matches = scan_for_pii(val)
            if matches:
                violations.append({
                    "column": col,
                    "row_index": idx,
                    "matches": matches,
                    "value_sample": val[:50] + "..." if len(val) > 50 else val
                })
                # Log first few violations to avoid spam
                if len(violations) <= 5:
                    logger.warning(f"PII found in column '{col}', row {idx}: {matches}")

    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "checked_columns": checked_columns,
        "total_rows_checked": len(df)
    }


def record_checksums(
    files: List[Path],
    state_file: Optional[Path] = None,
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Calculate checksums for a list of files and record them in state/artifact_hashes.json.
    Returns the dict of {relative_path: checksum}.
    """
    project_root = get_project_root()
    if state_file is None:
        state_dir = project_root / "state"
        state_dir.mkdir(exist_ok=True)
        state_file = state_dir / "artifact_hashes.json"

    checksums = {}
    for f_path in files:
        if not f_path.exists():
            logger.error(f"File not found for checksum: {f_path}")
            continue

        # Use relative path from project root for storage
        try:
            rel_path = f_path.relative_to(project_root)
        except ValueError:
            rel_path = f_path.name

        checksum = calculate_file_checksum(f_path, algorithm)
        checksums[str(rel_path)] = checksum
        logger.info(f"Checksum recorded for {rel_path}: {checksum[:16]}...")

    # Load existing state if present
    existing = {}
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as fh:
                existing = json.load(fh)
        except json.JSONDecodeError:
            logger.warning("Existing state file is corrupted, overwriting.")

    # Merge and update
    existing.update(checksums)

    with open(state_file, "w", encoding="utf-8") as fh:
        json.dump(existing, fh, indent=2, sort_keys=True)

    logger.info(f"State file updated: {state_file}")
    return checksums


def validate_and_record(
    data_file: Path,
    state_file: Optional[Path] = None,
    pii_columns: Optional[List[str]] = None
) -> bool:
    """
    Main validation entry point:
    1. Scan data_file for PII.
    2. Calculate and record checksum.
    3. Return True if validation passes (no PII), False otherwise.
    """
    logger.info(f"Starting validation for: {data_file}")

    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        raise FileNotFoundError(f"Data file not found: {data_file}")

    # 1. PII Check
    try:
        df = pd.read_csv(data_file, sep="\t")
    except Exception:
        df = pd.read_csv(data_file)

    report = validate_no_pii(df, columns=pii_columns)

    if not report["passed"]:
        logger.error(f"PII validation FAILED. Found {len(report['violations'])} violations.")
        # Log summary
        for v in report["violations"][:5]:
            logger.error(f"  - {v['column']} (row {v['row_index']}): {v['matches']}")
        return False

    logger.info("PII validation PASSED.")

    # 2. Checksum Recording
    try:
        record_checksums([data_file], state_file)
    except Exception as e:
        logger.error(f"Failed to record checksum: {e}")
        return False

    return True


def build_arg_parser() -> argparse.ArgumentParser:
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate data files for PII and record checksums."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input data file (TSV/CSV) to validate."
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Path to the state file for checksums. Default: state/artifact_hashes.json"
    )
    parser.add_argument(
        "--columns",
        type=str,
        nargs="+",
        default=None,
        help="Specific columns to check for PII. If omitted, all string columns are checked."
    )
    return parser


def main():
    import argparse
    parser = build_arg_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    state_path = Path(args.state) if args.state else None
    columns = args.columns

    success = validate_and_record(input_path, state_path, columns)

    if success:
        logger.info("Validation complete: No PII found. Checksum recorded.")
        sys.exit(0)
    else:
        logger.error("Validation failed: PII detected or checksum recording error.")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
