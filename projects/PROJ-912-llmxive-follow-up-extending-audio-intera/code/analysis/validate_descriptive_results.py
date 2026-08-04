"""
Validation module for Task T033: Ensure results are descriptive (no causal claims).

This module analyzes the generated reports (robustness curve, breaking point, sensitivity)
to ensure that the language and conclusions drawn are strictly descriptive of correlations
and measured performance, avoiding any causal assertions about compression causing robustness
changes without controlled experimental evidence.

It scans text artifacts and JSON metadata for specific causal trigger words and flags
potential violations.
"""
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from config import get_path_config
from utils.logger import get_logger

# Causal trigger words that should NOT appear in descriptive results
CAUSAL_TRIGGERS = {
    "causes", "caused", "cause",
    "leads to", "lead to", "led to",
    "results in", "result in", "resulted in",
    "makes", "made", "cause",
    "forces", "force",
    "drives", "drive",
    "induces", "induce",
    "provokes", "provoke",
    "triggers", "trigger",
    "determines", "determine",
    "ensures", "ensure",
    "guarantees", "guarantee",
    "prevents", "prevent",
    "blocks", "block",
    "stops", "stop",
    "enables"  # Often implies causality in this context
}

# Phrases indicating correlation/descriptive language (safe)
DESCRIPTIVE_PHRASES = {
    "correlates with", "associated with", "linked to",
    "correlation", "relationship", "trend",
    "observed", "measured", "recorded",
    "higher/lower", "increases/decreases"  # Context dependent, but often descriptive
}

def get_logger_for_validation() -> logging.Logger:
    """Get a logger instance for validation tasks."""
    return get_logger("validate_descriptive_results")

def check_text_for_causal_claims(text: str, line_number: int = 0) -> List[Dict[str, Any]]:
    """
    Scan a text string for causal trigger words.

    Args:
        text: The text content to scan.
        line_number: The line number in the source file (for reporting).

    Returns:
        A list of dictionaries containing violation details.
    """
    violations = []
    words = text.lower().split()
    # Clean words of punctuation for matching
    clean_words = [w.strip(".,;:!?\"'()[]{}") for w in words]

    for i, word in enumerate(clean_words):
        if word in CAUSAL_TRIGGERS:
            # Context check: ensure it's not part of a negative or hypothetical
            # Simple heuristic: if preceded by "not", "does not", "cannot"
            # For now, we flag the presence and let human review decide,
            # but we log a warning.
            start_idx = text.lower().find(word, text.lower().find(word) if i == 0 else 0)
            context_start = max(0, start_idx - 20)
            context_end = min(len(text), start_idx + len(word) + 20)
            context = text[context_start:context_end]

            violations.append({
                "line": line_number,
                "word": word,
                "context": context,
                "severity": "warning"
            })

    return violations

def validate_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Validate a JSON file for causal claims in string values.

    Args:
        file_path: Path to the JSON file.

    Returns:
        List of violations found.
    """
    violations = []
    logger = get_logger_for_validation()

    if not file_path.exists():
        logger.warning(f"File not found: {file_path}, skipping JSON validation.")
        return violations

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        def recursive_scan(obj, path="root"):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    recursive_scan(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    recursive_scan(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                found = check_text_for_causal_claims(obj)
                for v in found:
                    v["file"] = str(file_path)
                    v["path"] = path
                    violations.append(v)

        recursive_scan(data)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        violations.append({
            "file": str(file_path),
            "error": "Invalid JSON format",
            "severity": "error"
        })

    return violations

def validate_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Validate a CSV file for causal claims in cell values.

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of violations found.
    """
    violations = []
    logger = get_logger_for_validation()

    if not file_path.exists():
        logger.warning(f"File not found: {file_path}, skipping CSV validation.")
        return violations

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2): # Header is row 1
                for col, value in row.items():
                    if isinstance(value, str):
                        found = check_text_for_causal_claims(value, row_idx)
                        for v in found:
                            v["file"] = str(file_path)
                            v["column"] = col
                            v["row"] = row_idx
                            violations.append(v)
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        violations.append({
            "file": str(file_path),
            "error": str(e),
            "severity": "error"
        })

    return violations

def validate_text_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Validate a text file (e.g., report) for causal claims.

    Args:
        file_path: Path to the text file.

    Returns:
        List of violations found.
    """
    violations = []
    logger = get_logger_for_validation()

    if not file_path.exists():
        logger.warning(f"File not found: {file_path}, skipping text validation.")
        return violations

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                found = check_text_for_causal_claims(line, line_num)
                for v in found:
                    v["file"] = str(file_path)
                    violations.append(v)
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
        violations.append({
            "file": str(file_path),
            "error": str(e),
            "severity": "error"
        })

    return violations

def run_validation() -> Dict[str, Any]:
    """
    Run validation on all relevant output artifacts in data/processed/.

    Returns:
        A summary dictionary of the validation results.
    """
    logger = get_logger_for_validation()
    logger.info("Starting descriptive results validation (T033)...")

    config = get_path_config()
    processed_dir = config.processed_data_dir

    files_to_check = [
        processed_dir / "robustness_curve.png", # Binary, skip text scan but check if exists
        processed_dir / "correlation_data.json",
        processed_dir / "breaking_point.json",
        processed_dir / "sensitivity_report.csv",
        processed_dir / "robustness_metrics.csv",
        processed_dir / "ablation_results.csv"
    ]

    all_violations = []

    # Check for existence and scan text-based files
    for file_path in files_to_check:
        if not file_path.exists():
            logger.warning(f"Expected artifact missing: {file_path}")
            continue

        if file_path.suffix == '.json':
            violations = validate_json_file(file_path)
        elif file_path.suffix == '.csv':
            violations = validate_csv_file(file_path)
        elif file_path.suffix in ['.txt', '.md', '.log']:
            violations = validate_text_file(file_path)
        else:
            # Binary files like PNGs are not scanned for text, but we log their presence
            logger.debug(f"Skipping binary file scan: {file_path}")
            continue

        all_violations.extend(violations)

    # Summary
    total_violations = len(all_violations)
    status = "PASS" if total_violations == 0 else "FAIL"

    result = {
        "status": status,
        "total_violations": total_violations,
        "violations": all_violations,
        "message": "Validation complete. No causal claims detected." if status == "PASS" else "Validation failed. Causal claims detected."
    }

    if total_violations > 0:
        logger.error(f"Validation failed: {total_violations} potential causal claims found.")
        for v in all_violations:
            logger.warning(f"  - {v.get('file', 'N/A')}:{v.get('line', v.get('row', 'N/A'))}: {v.get('context', v.get('word', 'N/A'))}")
    else:
        logger.info("Validation passed: No causal claims detected in descriptive results.")

    return result

def main():
    """Main entry point for the validation script."""
    result = run_validation()

    # Save the validation report
    config = get_path_config()
    report_path = config.processed_data_dir / "validation_report.json"

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print(f"Validation report saved to: {report_path}")
    print(f"Status: {result['status']}")
    print(f"Violations: {result['total_violations']}")

    if result['status'] == "FAIL":
        exit(1)

if __name__ == "__main__":
    main()
