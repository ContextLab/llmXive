"""
Validation script to ensure the full pipeline is reproducible as per docs/quickstart.md.

This script performs the following checks:
1. Verifies required directories exist (code/, data/, contracts/, tests/).
2. Verifies required schema files exist in contracts/.
3. Verifies critical output files exist if the pipeline has been run.
4. Checks content of key configuration files to ensure they match expected values.
5. Logs all validation steps and results to a JSON file.
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Expected files and directories
REQUIRED_DIRECTORIES = [
    "code", "data", "contracts", "tests", "docs",
    "data/raw", "data/processed", "data/figures", "data/logs"
]

REQUIRED_SCHEMA_FILES = [
    "contracts/dataset.schema.yaml",
    "contracts/output.schema.yaml"
]

REQUIRED_CONFIG_VALUES = {
    "code/config.py": {
        "WINDOW_LENGTH_BASELINE": 30,
        "K_MEANS_K": 5,
        "DENSITY_THRESHOLD_BASELINE": 0.15
    }
}

# Expected output files (optional - only check if they exist, don't fail if missing)
OPTIONAL_OUTPUT_FILES = [
    "data/processed/structural_metrics.csv",
    "data/processed/dynamic_metrics.csv",
    "data/processed/correlation_results.csv",
    "data/processed/structural_density_sensitivity.csv",
    "data/processed/tractography_sensitivity_metrics.csv",
    "data/processed/tractography_correlation_sensitivity.csv",
    "data/processed/completeness_report.json",
    "data/logs/exclusion_log.json"
]

QUICKSTART_PATH = DOCS_DIR / "quickstart.md"

def log_step(step_name: str, status: str, message: str = "", details: Optional[Dict] = None) -> Dict[str, Any]:
    """Log a validation step."""
    entry = {
        "step": step_name,
        "status": status,  # 'passed', 'failed', 'skipped', 'warning'
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "message": message,
        "details": details or {}
    }
    print(f"[{status.upper()}] {step_name}: {message}")
    return entry

def validate_file_exists(path: Path, required: bool = True) -> Tuple[bool, str]:
    """Check if a file exists."""
    if path.exists():
        return True, f"File exists: {path.relative_to(PROJECT_ROOT)}"
    else:
        msg = f"File missing: {path.relative_to(PROJECT_ROOT)}"
        if required:
            return False, msg
        return None, msg  # None indicates optional

def validate_directory_exists(path: Path, required: bool = True) -> Tuple[bool, str]:
    """Check if a directory exists."""
    if path.is_dir():
        return True, f"Directory exists: {path.relative_to(PROJECT_ROOT)}"
    else:
        msg = f"Directory missing: {path.relative_to(PROJECT_ROOT)}"
        if required:
            return False, msg
        return None, msg

def validate_file_content(path: Path, expected_values: Dict[str, Any]) -> Tuple[bool, str, Dict]:
    """Validate that a file contains expected key-value pairs (for config files)."""
    if not path.exists():
        return False, f"File not found for content check: {path.relative_to(PROJECT_ROOT)}", {}

    details = {}
    all_passed = True
    messages = []

    try:
        # Special handling for Python config files
        if path.suffix == ".py":
            # Execute the file in a safe namespace to read variables
            namespace = {}
            exec(path.read_text(), namespace)
            for key, expected_val in expected_values.items():
                if key in namespace:
                    actual_val = namespace[key]
                    if actual_val == expected_val:
                        details[key] = {"expected": expected_val, "actual": actual_val, "status": "match"}
                    else:
                        details[key] = {"expected": expected_val, "actual": actual_val, "status": "mismatch"}
                        all_passed = False
                        messages.append(f"Key '{key}' mismatch: expected {expected_val}, got {actual_val}")
                else:
                    details[key] = {"expected": expected_val, "actual": "MISSING", "status": "missing"}
                    all_passed = False
                    messages.append(f"Key '{key}' missing from {path.name}")
        else:
            # For other files, we might parse YAML/JSON if needed, but for now just note it exists
            details = {"note": "Content validation not implemented for this file type"}

    except Exception as e:
        return False, f"Error reading file {path.name}: {str(e)}", {}

    if all_passed:
        return True, "All expected values found and match", details
    else:
        return False, "; ".join(messages), details

def run_validation_pipeline() -> Dict[str, Any]:
    """Run the full validation pipeline and return results."""
    results = {
        "project": "PROJ-128-investigating-the-influence-of-network-t",
        "validation_script": "validate_quickstart.py",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "steps": [],
        "summary": {
            "total_steps": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
    }

    print("=" * 60)
    print("STARTING QUICKSTART VALIDATION PIPELINE")
    print("=" * 60)

    # 1. Validate Directory Structure
    print("\n--- Step 1: Validating Directory Structure ---")
    for dir_name in REQUIRED_DIRECTORIES:
        dir_path = PROJECT_ROOT / dir_name
        success, msg = validate_directory_exists(dir_path, required=True)
        status = "passed" if success else "failed"
        results["steps"].append(log_step(f"Dir: {dir_name}", status, msg))

    # 2. Validate Schema Files
    print("\n--- Step 2: Validating Schema Files ---")
    for schema_file in REQUIRED_SCHEMA_FILES:
        file_path = PROJECT_ROOT / schema_file
        success, msg = validate_file_exists(file_path, required=True)
        status = "passed" if success else "failed"
        results["steps"].append(log_step(f"Schema: {schema_file}", status, msg))

    # 3. Validate Quickstart Documentation
    print("\n--- Step 3: Validating Quickstart Documentation ---")
    if QUICKSTART_PATH.exists():
        content = QUICKSTART_PATH.read_text()
        # Basic checks: does it have instructions for setup, data fetch, run?
        has_setup = "setup" in content.lower() or "install" in content.lower()
        has_data = "data" in content.lower() and ("fetch" in content.lower() or "download" in content.lower())
        has_run = "run" in content.lower() or "execute" in content.lower()

        if has_setup and has_data and has_run:
            results["steps"].append(log_step("Quickstart Content", "passed", "Documentation contains setup, data, and run instructions."))
        else:
            missing = []
            if not has_setup: missing.append("setup")
            if not has_data: missing.append("data fetching")
            if not has_run: missing.append("execution")
            results["steps"].append(log_step("Quickstart Content", "warning", f"Documentation might be incomplete. Missing sections: {', '.join(missing)}."))
    else:
        results["steps"].append(log_step("Quickstart File", "failed", "docs/quickstart.md does not exist."))

    # 4. Validate Configuration Values
    print("\n--- Step 4: Validating Configuration Values ---")
    config_path = PROJECT_ROOT / "code/config.py"
    if config_path.exists():
        # We need to map the expected values to the actual variable names in config.py
        # Based on T004b, we expect these to be defined
        expected = {
            "WINDOW_LENGTH_BASELINE": 30,
            "K_MEANS_K": 5,
            "DENSITY_THRESHOLD_BASELINE": 0.15
        }
        success, msg, details = validate_file_content(config_path, expected)
        status = "passed" if success else "failed"
        results["steps"].append(log_step("Config Values", status, msg, details))
    else:
        results["steps"].append(log_step("Config File", "failed", "code/config.py does not exist."))

    # 5. Check Optional Output Files (if they exist, note them; if not, don't fail)
    print("\n--- Step 5: Checking for Output Artifacts (Optional) ---")
    output_status = {}
    for file_path_str in OPTIONAL_OUTPUT_FILES:
        file_path = PROJECT_ROOT / file_path_str
        exists = file_path.exists()
        output_status[file_path_str] = exists
        if exists:
            results["steps"].append(log_step(f"Output: {file_path_str}", "passed", "File exists.", {"size_bytes": file_path.stat().st_size}))
        else:
            results["steps"].append(log_step(f"Output: {file_path_str}", "skipped", "File not found (pipeline may not have been run yet)."))

    # 6. Summary
    results["summary"]["total_steps"] = len(results["steps"])
    results["summary"]["passed"] = sum(1 for s in results["steps"] if s["status"] == "passed")
    results["summary"]["failed"] = sum(1 for s in results["steps"] if s["status"] == "failed")
    results["summary"]["warnings"] = sum(1 for s in results["steps"] if s["status"] == "warning")
    results["summary"]["skipped"] = sum(1 for s in results["steps"] if s["status"] == "skipped")

    overall_status = "passed" if results["summary"]["failed"] == 0 else "failed"
    if results["summary"]["warnings"] > 0 and results["summary"]["failed"] == 0:
        overall_status = "passed_with_warnings"

    print("\n" + "=" * 60)
    print(f"VALIDATION COMPLETE: {overall_status.upper()}")
    print(f"Passed: {results['summary']['passed']}, Failed: {results['summary']['failed']}, Warnings: {results['summary']['warnings']}, Skipped: {results['summary']['skipped']}")
    print("=" * 60)

    return results

def main():
    """Main entry point."""
    try:
        results = run_validation_pipeline()

        # Save results to a log file
        log_path = PROJECT_ROOT / "data/logs/quickstart_validation_log.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nValidation log saved to: {log_path.relative_to(PROJECT_ROOT)}")

        # Exit with appropriate code
        if results["summary"]["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"CRITICAL ERROR during validation: {str(e)}")
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()