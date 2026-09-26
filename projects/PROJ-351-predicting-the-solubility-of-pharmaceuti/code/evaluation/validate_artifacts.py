"""
Artifact Validation Module for PROJ-351.

This module verifies that all output artifacts exist, are non-empty,
and match the expected schema as per Constitution Principles III, IV, V.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Import seed handling if needed for deterministic validation paths
from config.seeds import get_seed

# Define expected artifact paths relative to project root
EXPECTED_JSON_ARTIFACTS = [
    "results/baseline_metrics.json",
    "results/gnn_metrics.json",
    "results/model_comparison.json",
    "results/metrics.json",
    "results/final_report.json",
    "data/processed/rf_fold_predictions.json",
    "data/processed/gnn_fold_predictions.json",
    "data/processed/aggregated_predictions.json",
]

EXPECTED_PNG_ARTIFACTS = [
    # We expect at least 5 PNG files in results/ based on T030
    # We will validate that there are >= 5 files matching the pattern
    "results/feature_importance_*.png",
]

EXPECTED_MD_ARTIFACTS = [
    "docs/reports/final_report.md",
]

EXPECTED_YAML_ARTIFACTS = [
    "state/projects/PROJ-351-predicting-the-solubility-of-pharmaceuti.yaml",
]

# Expected JSON schemas (minimal keys required)
JSON_SCHEMAS = {
    "results/baseline_metrics.json": {"RMSE", "R2"},
    "results/gnn_metrics.json": {"RMSE", "R2"},
    "results/model_comparison.json": {"baseline_rmse", "gnn_rmse", "delta_rmse"},
    "results/metrics.json": {"RMSE", "R2", "p_value", "power"},
    "data/processed/aggregated_predictions.json": None, # List of dicts, check structure dynamically
    "data/processed/rf_fold_predictions.json": None,
    "data/processed/gnn_fold_predictions.json": None,
}

def validate_file_exists(file_path: Path) -> Tuple[bool, str]:
    """Check if a file exists."""
    if file_path.exists():
        return True, f"File exists: {file_path}"
    return False, f"File missing: {file_path}"

def validate_file_not_empty(file_path: Path) -> Tuple[bool, str]:
    """Check if a file is non-empty."""
    if not file_path.exists():
        return False, f"File missing (cannot check size): {file_path}"
    size = file_path.stat().st_size
    if size > 0:
        return True, f"File size OK ({size} bytes): {file_path}"
    return False, f"File is empty: {file_path}"

def validate_json_structure(file_path: Path, required_keys: Optional[set] = None) -> Tuple[bool, str]:
    """Check if a file is valid JSON and contains required keys."""
    exists, msg = validate_file_exists(file_path)
    if not exists:
        return False, msg

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in {file_path}: {e}"

    if required_keys:
        if not isinstance(data, dict):
            return False, f"JSON root in {file_path} is not a dict, cannot check keys."
        missing = required_keys - set(data.keys())
        if missing:
            return False, f"Missing keys in {file_path}: {missing}"

    return True, f"JSON structure valid for {file_path}"

def validate_png_files(results_dir: Path) -> Tuple[bool, str]:
    """Validate that expected PNG files exist and are non-empty."""
    if not results_dir.exists():
        return False, f"Results directory missing: {results_dir}"

    png_files = list(results_dir.glob("feature_importance_*.png"))
    if len(png_files) < 5:
        return False, f"Expected at least 5 feature importance PNGs, found {len(png_files)} in {results_dir}"

    empty_files = [f for f in png_files if f.stat().st_size == 0]
    if empty_files:
        return False, f"Found empty PNG files: {[f.name for f in empty_files]}"

    return True, f"Found {len(png_files)} valid feature importance PNGs"

def validate_yaml_structure(file_path: Path) -> Tuple[bool, str]:
    """Validate YAML file structure (basic check for non-empty and valid YAML)."""
    import yaml
    exists, msg = validate_file_exists(file_path)
    if not exists:
        return False, msg

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        if content is None:
            return False, f"YAML file is empty or invalid: {file_path}"
        return True, f"YAML structure valid: {file_path}"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in {file_path}: {e}"

def run_validation(root_dir: Path) -> Dict[str, Any]:
    """Run all validation checks and return a report."""
    validation_results = {
        "timestamp": "validation_run", # Placeholder for real timestamp logic
        "status": "passed",
        "details": []
    }

    # Check JSON files
    for rel_path in EXPECTED_JSON_ARTIFACTS:
        full_path = root_dir / rel_path
        exists_ok, msg_exists = validate_file_exists(full_path)
        if not exists_ok:
            validation_results["status"] = "failed"
            validation_results["details"].append({"file": rel_path, "status": "missing", "message": msg_exists})
            continue

        size_ok, msg_size = validate_file_not_empty(full_path)
        if not size_ok:
            validation_results["status"] = "failed"
            validation_results["details"].append({"file": rel_path, "status": "empty", "message": msg_size})
            continue

        schema_ok, msg_schema = "OK", "N/A"
        if rel_path in JSON_SCHEMAS:
            schema_ok, msg_schema = validate_json_structure(full_path, JSON_SCHEMAS[rel_path])
            if not schema_ok:
                validation_results["status"] = "failed"
                validation_results["details"].append({"file": rel_path, "status": "schema_error", "message": msg_schema})
                continue

        validation_results["details"].append({"file": rel_path, "status": "passed", "message": "Valid"})

    # Check PNG files
    results_dir = root_dir / "results"
    png_ok, msg_png = validate_png_files(results_dir)
    if not png_ok:
        validation_results["status"] = "failed"
        validation_results["details"].append({"file": "results/feature_importance_*.png", "status": "validation_failed", "message": msg_png})
    else:
        validation_results["details"].append({"file": "results/feature_importance_*.png", "status": "passed", "message": msg_png})

    # Check MD files
    for rel_path in EXPECTED_MD_ARTIFACTS:
        full_path = root_dir / rel_path
        exists_ok, msg_exists = validate_file_exists(full_path)
        if not exists_ok:
            validation_results["status"] = "failed"
            validation_results["details"].append({"file": rel_path, "status": "missing", "message": msg_exists})
            continue
        
        size_ok, msg_size = validate_file_not_empty(full_path)
        if not size_ok:
            validation_results["status"] = "failed"
            validation_results["details"].append({"file": rel_path, "status": "empty", "message": msg_size})
            continue

        validation_results["details"].append({"file": rel_path, "status": "passed", "message": "Valid"})

    # Check YAML files
    for rel_path in EXPECTED_YAML_ARTIFACTS:
        full_path = root_dir / rel_path
        yaml_ok, msg_yaml = validate_yaml_structure(full_path)
        if not yaml_ok:
            validation_results["status"] = "failed"
            validation_results["details"].append({"file": rel_path, "status": "yaml_error", "message": msg_yaml})
            continue
        validation_results["details"].append({"file": rel_path, "status": "passed", "message": "Valid"})

    return validation_results

def save_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the validation report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logging.info(f"Validation report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Validate project artifacts.")
    parser.add_argument(
        "--root-dir",
        type=Path,
        default=Path("."),
        help="Root directory of the project (default: current directory)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/validation_report.json"),
        help="Path to save the validation report"
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logging.info(f"Starting artifact validation for project at: {args.root_dir}")

    report = run_validation(args.root_dir)

    save_validation_report(report, args.output)

    if report["status"] == "passed":
        logging.info("All artifact validations PASSED.")
        return 0
    else:
        logging.error("Artifact validation FAILED. Check results/validation_report.json for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())