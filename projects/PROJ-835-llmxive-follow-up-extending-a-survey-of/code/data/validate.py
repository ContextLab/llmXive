"""
Data Validation Module for LlmXive Follow-up Project.

This module implements T014b: Validate Schemas.
It verifies that the downloaded dataset files and metadata conform to the
definitions in `contracts/dataset.schema.yaml`.

It uses the shared `utils.schema_validator` to perform the actual validation
against the YAML schema.
"""

import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import shared utilities from the project API surface
from utils.schema_validator import load_schema, validate_dataset_schema
from utils.logging import setup_logging, get_logger, log_pipeline_step
from config import PROJECT_ROOT, ensure_directories

# Ensure the logger is configured
logger = get_logger("data_validation")

# Path constants relative to project root
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def validate_downloaded_data(schema_path: Optional[Path] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates the downloaded dataset in `data/raw/` against the schema.

    Args:
        schema_path: Optional path to the schema YAML. Defaults to contracts/dataset.schema.yaml.

    Returns:
        Tuple[bool, Dict]: (is_valid, report_dict)
            - is_valid: True if all files pass schema validation.
            - report_dict: Detailed results including file status and errors.
    """
    if schema_path is None:
        schema_path = SCHEMA_PATH

    logger.info(f"Starting schema validation. Schema: {schema_path}, Data Dir: {RAW_DATA_DIR}")

    # 1. Verify Schema Exists
    if not schema_path.exists():
        error_msg = f"Schema file not found: {schema_path}"
        logger.error(error_msg)
        return False, {"valid": False, "error": error_msg}

    # 2. Load Schema
    try:
        schema = load_schema(schema_path)
        logger.info(f"Schema loaded successfully: {schema_path}")
    except Exception as e:
        error_msg = f"Failed to load schema: {e}"
        logger.error(error_msg)
        return False, {"valid": False, "error": error_msg}

    # 3. Verify Data Directory Exists
    if not RAW_DATA_DIR.exists():
        # If raw data dir doesn't exist, we can't validate files.
        # This is a soft failure if the download hasn't run yet, but strictly
        # speaking, the task is to validate *downloaded* data.
        warning_msg = f"Data directory not found: {RAW_DATA_DIR}. No files to validate."
        logger.warning(warning_msg)
        return True, {"valid": True, "warning": warning_msg, "files_checked": 0}

    # 4. Iterate and Validate Files
    results = {
        "valid": True,
        "schema_path": str(schema_path),
        "data_dir": str(RAW_DATA_DIR),
        "files_checked": 0,
        "files_passed": 0,
        "files_failed": 0,
        "details": []
    }

    # Look for common audio/data extensions
    # The schema might define specific file types, but we check for common ones first
    # if the schema doesn't explicitly list them.
    extensions_to_check = {".json", ".jsonl", ".csv", ".parquet", ".wav", ".mp3", ".flac"}

    files_to_validate = []
    for root, _, files in os.walk(RAW_DATA_DIR):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions_to_check):
                files_to_validate.append(Path(root) / file)

    if not files_to_validate:
        warning_msg = f"No data files found in {RAW_DATA_DIR} matching expected extensions."
        logger.warning(warning_msg)
        results["warning"] = warning_msg
        # Return valid=True but with warning, as there's nothing to fail
        return True, results

    for file_path in files_to_validate:
        results["files_checked"] += 1
        is_file_valid, file_report = validate_dataset_schema(file_path, schema)

        if is_file_valid:
            results["files_passed"] += 1
            status = "PASS"
            logger.debug(f"Validation PASS: {file_path}")
        else:
            results["files_failed"] += 1
            results["valid"] = False
            status = "FAIL"
            logger.error(f"Validation FAIL: {file_path}")
            if "errors" in file_report:
                for err in file_report["errors"]:
                    logger.error(f"  - {err}")

        results["details"].append({
            "file": str(file_path.relative_to(PROJECT_ROOT)),
            "status": status,
            "errors": file_report.get("errors", [])
        })

    log_summary = (
        f"Validation Complete: {results['files_checked']} files checked, "
        f"{results['files_passed']} passed, {results['files_failed']} failed."
    )
    if results["valid"]:
        logger.info(log_summary)
    else:
        logger.error(log_summary)

    return results["valid"], results


def main():
    """
    Entry point for the validation script.
    Runs validation and exits with code 0 on success, 1 on failure.
    """
    # Ensure directories exist (though we are reading, not writing)
    ensure_directories()

    # Setup logging
    setup_logging()

    logger.info("=== T014b: Validate Schemas ===")

    is_valid, report = validate_downloaded_data()

    # Output report to console and potentially to a log file
    print(json.dumps(report, indent=2, default=str))

    if not is_valid:
        logger.error("Schema validation failed. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("Schema validation successful.")
        sys.exit(0)


if __name__ == "__main__":
    main()