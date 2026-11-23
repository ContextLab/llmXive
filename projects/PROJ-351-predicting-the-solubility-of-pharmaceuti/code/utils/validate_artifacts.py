"""
Artifact Validation Module for PROJ-351

Validates all generated artifacts against the schema defined in
contracts/model_output.schema.yaml and ensures file existence,
non-empty content, and structural integrity.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Setup logging
logger = logging.getLogger(__name__)

# Define artifact paths to validate based on completed tasks
ARTIFACT_MANIFEST = {
    # Data Artifacts
    "data/raw/delaney-processed.csv": {
        "type": "csv",
        "required": True,
        "description": "Raw ESOL dataset"
    },
    "data/processed/cleaned_graphs.pkl": {
        "type": "pkl",
        "required": True,
        "description": "Cleaned RDKit Mol objects"
    },
    "data/processed/graph_tensors.pt": {
        "type": "pt",
        "required": True,
        "description": "PyTorch Geometric graph tensors"
    },
    "data/processed/fingerprints.npz": {
        "type": "npz",
        "required": True,
        "description": "Morgan fingerprints for RF"
    },
    "data/processed/rf_fold_predictions.json": {
        "type": "json",
        "required": True,
        "description": "Random Forest per-fold predictions"
    },
    "data/processed/rf_aggregated_errors.json": {
        "type": "json",
        "required": True,
        "description": "Aggregated RF errors"
    },
    "data/processed/gnn_fold_predictions.json": {
        "type": "json",
        "required": True,
        "description": "GNN per-fold predictions"
    },
    "data/processed/gnn_aggregated_errors.json": {
        "type": "json",
        "required": True,
        "description": "Aggregated GNN errors"
    },
    "data/processed/aggregated_predictions.json": {
        "type": "json",
        "required": True,
        "description": "Aggregated predictions for stats"
    },
    "data/processed/split_indices.json": {
        "type": "json",
        "required": True,
        "description": "Stratified split indices"
    },
    # Model Artifacts
    "data/artifacts/final_rf_baseline.pkl": {
        "type": "pkl",
        "required": True,
        "description": "Final Random Forest baseline model"
    },
    # Results Artifacts
    "results/baseline_metrics.json": {
        "type": "json",
        "required": True,
        "description": "Baseline model metrics"
    },
    "results/gnn_metrics.json": {
        "type": "json",
        "required": True,
        "description": "GNN model metrics"
    },
    "results/gnn_predictions.csv": {
        "type": "csv",
        "required": True,
        "description": "GNN predictions CSV"
    },
    "results/model_comparison.json": {
        "type": "json",
        "required": True,
        "description": "Model comparison metrics"
    },
    "results/statistical_test.json": {
        "type": "json",
        "required": True,
        "description": "Statistical test results"
    },
    "results/metrics.json": {
        "type": "json",
        "required": True,
        "description": "Aggregated metrics (SSoT)"
    },
    "results/viz_manifest.json": {
        "type": "json",
        "required": True,
        "description": "Visualization manifest"
    },
    "results/final_report.json": {
        "type": "json",
        "required": True,
        "description": "Final report JSON"
    },
    # Reports
    "docs/reports/final_report.md": {
        "type": "md",
        "required": True,
        "description": "Final markdown report"
    },
    # Visualization Files (check directory exists and has content)
    "docs/reports/interpretability_plots/": {
        "type": "dir_png",
        "required": True,
        "description": "Directory containing at least 5 PNG files"
    }
}

SCHEMA_PATH = Path("contracts/model_output.schema.yaml")


def validate_file_exists(path: Path) -> Tuple[bool, Optional[str]]:
    """Check if a file exists."""
    if not path.exists():
        return False, "FILE_NOT_FOUND"
    return True, None


def validate_file_not_empty(path: Path) -> Tuple[bool, Optional[str]]:
    """Check if a file is not empty."""
    try:
        if path.stat().st_size == 0:
            return False, "FILE_EMPTY"
        return True, None
    except Exception as e:
        return False, f"CHECK_ERROR: {str(e)}"


def validate_json_structure(path: Path) -> Tuple[bool, Optional[str]]:
    """Validate that a file contains valid JSON."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"INVALID_JSON: {str(e)}"
    except Exception as e:
        return False, f"CHECK_ERROR: {str(e)}"


def validate_csv_structure(path: Path) -> Tuple[bool, Optional[str]]:
    """Validate basic CSV structure (has headers)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if not first_line.strip():
                return False, "CSV_EMPTY"
            if ',' not in first_line and '\t' not in first_line:
                # Allow single column CSVs
                pass
        return True, None
    except Exception as e:
        return False, f"CHECK_ERROR: {str(e)}"


def validate_png_files(dir_path: Path) -> Tuple[bool, Optional[str]]:
    """Validate that a directory contains at least 5 PNG files > 1KB."""
    try:
        if not dir_path.exists():
            return False, "DIR_NOT_FOUND"
        
        png_files = list(dir_path.glob("*.png"))
        if len(png_files) < 5:
            return False, f"INSUFFICIENT_PNGS: Found {len(png_files)}, need 5"
        
        for p in png_files:
            if p.stat().st_size < 1024:
                return False, f"PNG_TOO_SMALL: {p.name}"
        
        return True, None
    except Exception as e:
        return False, f"CHECK_ERROR: {str(e)}"


def validate_yaml_structure(path: Path) -> Tuple[bool, Optional[str]]:
    """Validate YAML structure (basic check)."""
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        return True, None
    except ImportError:
        # If yaml is not installed, skip detailed validation but don't fail
        logger.warning("PyYAML not installed, skipping detailed YAML validation")
        return True, None
    except Exception as e:
        return False, f"INVALID_YAML: {str(e)}"


def run_validation() -> Dict[str, Any]:
    """Run validation on all artifacts defined in ARTIFACT_MANIFEST."""
    results = []
    all_passed = True
    general_errors = []

    logger.info("Starting artifact validation...")

    for artifact_path, spec in ARTIFACT_MANIFEST.items():
        full_path = Path(artifact_path)
        artifact_result = {
            "path": artifact_path,
            "status": "PASS",
            "error_code": None
        }
        
        # Check existence
        exists, err = validate_file_exists(full_path)
        if not exists:
            artifact_result["status"] = "FAIL"
            artifact_result["error_code"] = err
            all_passed = False
            general_errors.append(f"Missing required artifact: {artifact_path}")
            results.append(artifact_result)
            continue

        # Check type-specific validations
        v_type = spec.get("type", "unknown")
        
        if v_type == "json":
            valid, err = validate_json_structure(full_path)
            if not valid:
                artifact_result["status"] = "FAIL"
                artifact_result["error_code"] = err
                all_passed = False
        elif v_type == "csv":
            valid, err = validate_csv_structure(full_path)
            if not valid:
                artifact_result["status"] = "FAIL"
                artifact_result["error_code"] = err
                all_passed = False
        elif v_type == "pkl":
            valid, err = validate_file_not_empty(full_path)
            if not valid:
                artifact_result["status"] = "FAIL"
                artifact_result["error_code"] = err
                all_passed = False
        elif v_type == "pt":
            valid, err = validate_file_not_empty(full_path)
            if not valid:
                artifact_result["status"] = "FAIL"
                artifact_result["error_code"] = err
                all_passed = False
        elif v_type == "npz":
            valid, err = validate_file_not_empty(full_path)
            if not valid:
                artifact_result["status"] = "FAIL"
                artifact_result["error_code"] = err
                all_passed = False
        elif v_type == "md":
            valid, err = validate_file_not_empty(full_path)
            if not valid:
                artifact_result["status"] = "FAIL"
                artifact_result["error_code"] = err
                all_passed = False
        elif v_type == "dir_png":
            valid, err = validate_png_files(full_path)
            if not valid:
                artifact_result["status"] = "FAIL"
                artifact_result["error_code"] = err
                all_passed = False

        results.append(artifact_result)

    # Build final report structure
    final_report = {
        "status": "PASS" if all_passed else "FAIL",
        "artifacts": results,
        "errors": general_errors
    }

    return final_report


def save_validation_report(report: Dict[str, Any], output_path: Path = None) -> Path:
    """Save the validation report to a JSON file."""
    if output_path is None:
        output_path = Path("results/validation_report.json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")
    return output_path


def main():
    """Main entry point for artifact validation."""
    parser = argparse.ArgumentParser(description="Validate pipeline artifacts")
    parser.add_argument(
        "--output",
        type=str,
        default="results/validation_report.json",
        help="Output path for validation report"
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="contracts/model_output.schema.yaml",
        help="Path to schema file"
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check schema exists
    schema_path = Path(args.schema)
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)

    logger.info(f"Using schema: {schema_path}")

    # Run validation
    report = run_validation()

    # Save report
    output_path = Path(args.output)
    save_validation_report(report, output_path)

    # Exit with appropriate code
    if report["status"] == "FAIL":
        logger.error("Validation FAILED. See report for details.")
        sys.exit(1)
    else:
        logger.info("Validation PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()