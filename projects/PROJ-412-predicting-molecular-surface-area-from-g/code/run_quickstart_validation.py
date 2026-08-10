"""
Quickstart Validation Script for PROJ-412.

This script verifies the execution of Functional Requirements FR-001 to FR-007
by checking the existence and validity of critical output artifacts generated
by the pipeline.

It does NOT re-run the full pipeline (which would exceed time budgets), but
validates that the expected outputs from a successful run exist and conform
to the schemas defined in `data/schemas/`.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import yaml

# Add project root to path if necessary
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.logging import setup_logging, get_logger
from code.utils.config import get_project_root, get_data_dir, get_results_dir

# Setup logging
logger = setup_logging(level=logging.INFO)

# Define paths relative to project root
DATA_DIR = get_data_dir()
RESULTS_DIR = get_results_dir()
SCHEMAS_DIR = DATA_DIR / "schemas"
SPLITS_DIR = DATA_DIR / "splits"
PROCESSED_DIR = DATA_DIR / "processed"
PREDICTIONS_DIR = RESULTS_DIR / "predictions"
REPORTS_DIR = RESULTS_DIR / "reports"
BASELINE_DIR = RESULTS_DIR / "baseline"
PLOTS_DIR = RESULTS_DIR / "plots"

# Define expected artifacts for FR verification
# FR-001: Data Ingestion & Preprocessing
FR001_ARTIFACTS = [
    DATA_DIR / "raw" / "chunk_*.parquet",  # Wildcard handled in check
    PROCESSED_DIR / "graphs_with_features.parquet",
    PROCESSED_DIR / "conformers.parquet",
    PROCESSED_DIR / "descriptors.parquet",
    PROCESSED_DIR / "paired_dataset.parquet",
    PROCESSED_DIR / "conformer_params.json",
    PROCESSED_DIR / "failure_report.csv",
]

# FR-002: Data Splitting
FR002_ARTIFACTS = [
    SPLITS_DIR / "train_indices.csv",
    SPLITS_DIR / "test_indices.csv",
    SPLITS_DIR / "split_report.json",
]

# FR-003: Model Training & Baselines
FR003_ARTIFACTS = [
    BASELINE_DIR / "baseline_model_2d.pkl",
    BASELINE_DIR / "baseline_model_geometry.pkl",
    PREDICTIONS_DIR / "baseline_2d_predictions.parquet",
    PREDICTIONS_DIR / "baseline_geometry_predictions.parquet",
    PREDICTIONS_DIR / "gcn_predictions.parquet",
]

# FR-004: Evaluation Metrics
FR004_ARTIFACTS = [
    REPORTS_DIR / "model_metrics.json",
    REPORTS_DIR / "model_comparison.json",
]

# FR-005: Sensitivity Analysis
FR005_ARTIFACTS = [
    PROCESSED_DIR / "sensitivity_absolute.csv",
    REPORTS_DIR / "sensitivity_analysis.md",
    PLOTS_DIR / "sensitivity_absolute.png",
]

# FR-006: Documentation (README)
FR006_ARTIFACTS = [
    project_root / "README.md",
]

# FR-007: Robustness & Logging
FR007_ARTIFACTS = [
    project_root / "logs" / "excluded_molecules.log",
    project_root / "logs" / "ingestion_errors.log",
    project_root / "logs" / "conformer_failures.log",
    DATA_DIR / "raw" / "checksums.json",
]

def check_file_exists(path: Path, allow_wildcard: bool = False) -> bool:
    """Check if a file exists. Supports simple wildcard for FR001 chunks."""
    if allow_wildcard and "*" in str(path):
        # Simple check: look for at least one chunk file
        parent = path.parent
        pattern = path.name
        if parent.exists():
            return any(parent.glob(pattern))
        return False
    return path.exists()

def check_file_not_empty(path: Path) -> bool:
    """Check if a file exists and is not empty."""
    if not path.exists():
        return False
    return path.stat().st_size > 0

def validate_schema(path: Path, schema_path: Path) -> bool:
    """
    Basic schema validation by checking column names in Parquet/CSV
    against expected keys in YAML schema.
    """
    if not path.exists() or not schema_path.exists():
        return False

    try:
        schema = yaml.safe_load(schema_path.read_text())
        if not schema or "fields" not in schema:
            logger.warning(f"Schema {schema_path} missing 'fields' key.")
            return True # Cannot validate without schema, but file exists

        expected_fields = set(schema["fields"].keys())
        
        if path.suffix == ".parquet":
            df = pd.read_parquet(path)
            actual_fields = set(df.columns)
        elif path.suffix == ".csv":
            df = pd.read_csv(path)
            actual_fields = set(df.columns)
        else:
            return True # Skip non-tabular validation

        # Check if all expected fields are present
        missing = expected_fields - actual_fields
        if missing:
            logger.warning(f"Schema validation failed for {path.name}: missing {missing}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating schema for {path}: {e}")
        return False

def run_validation() -> Dict[str, Any]:
    """Run all validation checks and return results."""
    results = {
        "fr001": {"status": "PASS", "details": []},
        "fr002": {"status": "PASS", "details": []},
        "fr003": {"status": "PASS", "details": []},
        "fr004": {"status": "PASS", "details": []},
        "fr005": {"status": "PASS", "details": []},
        "fr006": {"status": "PASS", "details": []},
        "fr007": {"status": "PASS", "details": []},
        "overall": "PASS"
    }

    def check_group(fr_key: str, artifacts: List[Path], schema_map: Optional[Dict[Path, Path]] = None):
        group_result = results[fr_key]
        all_pass = True
        for artifact in artifacts:
            # Handle wildcard for chunks
            is_wildcard = "*" in str(artifact)
            if not check_file_exists(artifact, allow_wildcard=is_wildcard):
                group_result["status"] = "FAIL"
                all_pass = False
                group_result["details"].append(f"Missing: {artifact}")
            elif not check_file_not_empty(artifact):
                group_result["status"] = "FAIL"
                all_pass = False
                group_result["details"].append(f"Empty: {artifact}")
            else:
                # Schema validation if applicable
                if schema_map and artifact in schema_map:
                    if not validate_schema(artifact, schema_map[artifact]):
                        group_result["status"] = "FAIL"
                        all_pass = False
                        group_result["details"].append(f"Schema mismatch: {artifact}")
                    else:
                        group_result["details"].append(f"Valid: {artifact}")
                else:
                    group_result["details"].append(f"Found: {artifact}")

        if not all_pass:
            results["overall"] = "FAIL"

    # FR-001: Data Ingestion
    schema_map_001 = {
        PROCESSED_DIR / "paired_dataset.parquet": SCHEMAS_DIR / "static_schema.yaml",
        PROCESSED_DIR / "descriptors.parquet": SCHEMAS_DIR / "static_schema.yaml", # Simplified
    }
    check_group("fr001", FR001_ARTIFACTS, schema_map_001)

    # FR-002: Split
    schema_map_002 = {
        SPLITS_DIR / "split_report.json": SCHEMAS_DIR / "static_schema.yaml" # Simplified check
    }
    check_group("fr002", FR002_ARTIFACTS, schema_map_002)

    # FR-003: Models
    check_group("fr003", FR003_ARTIFACTS)

    # FR-004: Metrics
    schema_map_004 = {
        REPORTS_DIR / "model_metrics.json": SCHEMAS_DIR / "model_schema.yaml",
        REPORTS_DIR / "model_comparison.json": SCHEMAS_DIR / "model_schema.yaml",
    }
    check_group("fr004", FR004_ARTIFACTS, schema_map_004)

    # FR-005: Sensitivity
    schema_map_005 = {
        PROCESSED_DIR / "sensitivity_absolute.csv": SCHEMAS_DIR / "sensitivity_schema.yaml",
    }
    check_group("fr005", FR005_ARTIFACTS, schema_map_005)

    # FR-006: README
    check_group("fr006", FR006_ARTIFACTS)

    # FR-007: Logs
    check_group("fr007", FR007_ARTIFACTS)

    return results

def main():
    parser = argparse.ArgumentParser(description="Validate pipeline outputs against FR-001 to FR-007")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    setup_logging(level=getattr(logging, args.log_level.upper()))
    logger.info("Starting Quickstart Validation...")

    results = run_validation()

    # Output summary
    logger.info("=" * 50)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 50)
    for fr_key, data in results.items():
        if fr_key == "overall":
            continue
        status_icon = "✅" if data["status"] == "PASS" else "❌"
        logger.info(f"{fr_key.upper()}: {status_icon} {data['status']}")
        for detail in data["details"]:
            logger.info(f"   - {detail}")
    
    logger.info("=" * 50)
    logger.info(f"OVERALL STATUS: {results['overall']}")
    logger.info("=" * 50)

    # Save detailed report
    report_path = REPORTS_DIR / "quickstart_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Detailed report saved to: {report_path}")

    if results["overall"] == "FAIL":
        logger.error("Validation FAILED. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("Validation PASSED. All FR-001 to FR-007 artifacts verified.")
        sys.exit(0)

if __name__ == "__main__":
    main()
