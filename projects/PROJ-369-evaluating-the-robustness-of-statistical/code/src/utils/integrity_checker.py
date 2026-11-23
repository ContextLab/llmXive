"""
Data Integrity Verification Module (T067).

Implements a final integrity check that verifies all processed files
(real and synthetic) have valid checksums and match the expected schema.

Output: data/results/integrity_report.json
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_path, ensure_dirs
from src.utils.logging import setup_logger, log_info, log_error, log_warning, log_critical
from src.data.schemas import TimeSeries, SyntheticData, TestResult, ErrorRateSummary
import pandas as pd
import numpy as np

# Configure logging
logger = setup_logger("integrity_checker")

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        log_error(f"Failed to compute checksum for {file_path}: {e}")
        return ""

def validate_json_schema(file_path: Path, schema_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a JSON file against expected schema structure.
    
    Args:
        file_path: Path to the JSON file
        schema_type: One of 'metrics', 'error_rates', 'regression_model', 
                    'filtered_features', 'null_distribution_gate', 'baseline_status'
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if schema_type == 'metrics':
            # Expected: List of objects with keys: source, length, hurst, acf_vector, spectral_peak_ratio, is_shuffled
            if not isinstance(data, list):
                return False, "Root must be a list"
            required_keys = {'source', 'length', 'hurst', 'acf_vector', 'spectral_peak_ratio', 'is_shuffled'}
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    return False, f"Item {i} is not a dict"
                missing = required_keys - set(item.keys())
                if missing:
                    return False, f"Item {i} missing keys: {missing}"
                if not isinstance(item.get('acf_vector'), list):
                    return False, f"Item {i} acf_vector is not a list"
        
        elif schema_type == 'error_rates':
            # Expected: CSV-like structure or list of dicts with hurst, error_rate, n_eff, etc.
            if not isinstance(data, list):
                return False, "Root must be a list"
            if len(data) > 0:
                required_keys = {'hurst', 'error_rate', 'n_eff', 'configuration'}
                missing = required_keys - set(data[0].keys())
                if missing:
                    return False, f"Missing keys in first item: {missing}"
        
        elif schema_type == 'regression_model':
            # Expected: dict with keys: slope, intercept, p_value, vif, n_eff, r_squared, slope_per_01_unit
            if not isinstance(data, dict):
                return False, "Root must be a dict"
            required_keys = {'slope', 'intercept', 'p_value', 'vif', 'n_eff', 'r_squared', 'slope_per_01_unit'}
            missing = required_keys - set(data.keys())
            if missing:
                return False, f"Missing keys: {missing}"
        
        elif schema_type == 'filtered_features':
            # Expected: dict with keys: filtered_features, excluded_features
            if not isinstance(data, dict):
                return False, "Root must be a dict"
            required_keys = {'filtered_features', 'excluded_features'}
            missing = required_keys - set(data.keys())
            if missing:
                return False, f"Missing keys: {missing}"
            if not isinstance(data.get('filtered_features'), list):
                return False, "filtered_features must be a list"
            if not isinstance(data.get('excluded_features'), list):
                return False, "excluded_features must be a list"
        
        elif schema_type == 'null_distribution_gate':
            # Expected: dict with keys: status, real_count, synthetic_count
            if not isinstance(data, dict):
                return False, "Root must be a dict"
            required_keys = {'status', 'real_count', 'synthetic_count'}
            missing = required_keys - set(data.keys())
            if missing:
                return False, f"Missing keys: {missing}"
            if data.get('status') != 'PASS':
                return False, f"Status is not PASS: {data.get('status')}"
        
        elif schema_type == 'baseline_status':
            # Expected: dict with keys: status, rejection_rate, ci_lower, ci_upper
            if not isinstance(data, dict):
                return False, "Root must be a dict"
            required_keys = {'status', 'rejection_rate', 'ci_lower', 'ci_upper'}
            missing = required_keys - set(data.keys())
            if missing:
                return False, f"Missing keys: {missing}"
            if data.get('status') != 'PASS':
                return False, f"Status is not PASS: {data.get('status')}"
        
        return True, None
    
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Validation error: {e}"

def validate_csv_schema(file_path: Path, expected_columns: List[str]) -> Tuple[bool, Optional[str]]:
    """Validate a CSV file has expected columns."""
    try:
        df = pd.read_csv(file_path)
        missing_cols = set(expected_columns) - set(df.columns)
        if missing_cols:
            return False, f"Missing columns: {missing_cols}"
        if len(df) == 0:
            return False, "File is empty"
        return True, None
    except Exception as e:
        return False, f"CSV validation error: {e}"

def check_file_exists(file_path: Path) -> Tuple[bool, Optional[str]]:
    """Check if a file exists and is non-empty."""
    if not file_path.exists():
        return False, "File does not exist"
    if file_path.stat().st_size == 0:
        return False, "File is empty"
    return True, None

def run_integrity_check() -> Dict[str, Any]:
    """
    Run the full integrity check on all processed files.
    
    Returns:
        Dictionary containing the integrity report.
    """
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "files_checked": 0,
        "files_passed": 0,
        "files_failed": 0,
        "details": []
    }
    
    # Define files to check
    files_to_check = [
        # Metrics files
        {
            "path": "data/processed/metrics.json",
            "type": "json",
            "schema": "metrics",
            "description": "Real and synthetic metrics"
        },
        {
            "path": "data/processed/null_distributions/metrics_shuffled.json",
            "type": "json",
            "schema": "metrics",
            "description": "Shuffled metrics",
            "optional": True
        },
        # Gate files
        {
            "path": "data/results/null_distribution_gate.json",
            "type": "json",
            "schema": "null_distribution_gate",
            "description": "Null distribution gate status"
        },
        {
            "path": "data/results/baseline_status.json",
            "type": "json",
            "schema": "baseline_status",
            "description": "Baseline validation status"
        },
        # Regression files
        {
            "path": "data/results/filtered_features.json",
            "type": "json",
            "schema": "filtered_features",
            "description": "Filtered features list"
        },
        {
            "path": "data/results/regression_model.json",
            "type": "json",
            "schema": "regression_model",
            "description": "Regression model results"
        },
        # Error rates
        {
            "path": "data/results/error_rates.csv",
            "type": "csv",
            "columns": ["hurst", "error_rate", "n_eff", "configuration"],
            "description": "Error rates from hypothesis testing"
        },
        # Sampling metadata
        {
            "path": "data/processed/sampling_metadata.json",
            "type": "json",
            "schema": "any",
            "description": "Sampling metadata (optional)",
            "optional": True
        }
    ]
    
    # Check null distribution directories
    null_dirs = [
        "data/processed/null_distributions/real",
        "data/processed/null_distributions/synthetic"
    ]
    
    for dir_path in null_dirs:
        full_path = get_path(dir_path)
        if not full_path.exists():
            report["status"] = "FAIL"
            detail = {
                "file": dir_path,
                "status": "MISSING",
                "error": "Directory does not exist"
            }
            report["details"].append(detail)
            log_error(f"Missing directory: {dir_path}")
            continue
        
        # Count files in directory
        file_count = len(list(full_path.glob("*.csv")))
        if file_count == 0:
            report["status"] = "FAIL"
            detail = {
                "file": dir_path,
                "status": "EMPTY",
                "error": "Directory is empty"
            }
            report["details"].append(detail)
            log_error(f"Empty directory: {dir_path}")
        else:
            detail = {
                "file": dir_path,
                "status": "PASS",
                "file_count": file_count
            }
            report["details"].append(detail)
            report["files_passed"] += 1
            report["files_checked"] += 1
            log_info(f"Verified directory {dir_path}: {file_count} files")
    
    # Check individual files
    for file_spec in files_to_check:
        full_path = get_path(file_spec["path"])
        report["files_checked"] += 1
        
        # Check existence
        exists_ok, exists_err = check_file_exists(full_path)
        if not exists_ok:
            if file_spec.get("optional", False):
                detail = {
                    "file": file_spec["path"],
                    "status": "SKIP",
                    "error": exists_err
                }
                report["details"].append(detail)
                log_warning(f"Skipping optional file: {file_spec['path']}")
                continue
            else:
                report["status"] = "FAIL"
                detail = {
                    "file": file_spec["path"],
                    "status": "FAIL",
                    "error": exists_err
                }
                report["details"].append(detail)
                report["files_failed"] += 1
                log_error(f"File missing: {file_spec['path']}")
                continue
        
        # Validate schema/content
        if file_spec["type"] == "json":
            is_valid, err = validate_json_schema(full_path, file_spec["schema"])
            if not is_valid:
                report["status"] = "FAIL"
                detail = {
                    "file": file_spec["path"],
                    "status": "FAIL",
                    "error": err
                }
                report["details"].append(detail)
                report["files_failed"] += 1
                log_error(f"Schema validation failed for {file_spec['path']}: {err}")
            else:
                detail = {
                    "file": file_spec["path"],
                    "status": "PASS",
                    "checksum": compute_file_checksum(full_path)
                }
                report["details"].append(detail)
                report["files_passed"] += 1
                log_info(f"Validated JSON: {file_spec['path']}")
        
        elif file_spec["type"] == "csv":
            is_valid, err = validate_csv_schema(full_path, file_spec["columns"])
            if not is_valid:
                report["status"] = "FAIL"
                detail = {
                    "file": file_spec["path"],
                    "status": "FAIL",
                    "error": err
                }
                report["details"].append(detail)
                report["files_failed"] += 1
                log_error(f"CSV validation failed for {file_spec['path']}: {err}")
            else:
                detail = {
                    "file": file_spec["path"],
                    "status": "PASS",
                    "checksum": compute_file_checksum(full_path)
                }
                report["details"].append(detail)
                report["files_passed"] += 1
                log_info(f"Validated CSV: {file_spec['path']}")
    
    # Summary
    report["summary"] = {
        "total_files_checked": report["files_checked"],
        "total_files_passed": report["files_passed"],
        "total_files_failed": report["files_failed"],
        "integrity_status": report["status"]
    }
    
    return report

def main():
    """Main entry point for integrity check."""
    log_info("Starting data integrity verification (T067)...")
    
    # Ensure output directory exists
    output_dir = get_path("data/results")
    ensure_dirs(output_dir)
    
    # Run check
    report = run_integrity_check()
    
    # Write report
    output_path = get_path("data/results/integrity_report.json")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_info(f"Integrity report written to {output_path}")
    log_info(f"Overall status: {report['status']}")
    
    if report['status'] == 'FAIL':
        log_critical("Integrity check FAILED. Review errors above.")
        sys.exit(1)
    else:
        log_info("Integrity check PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
