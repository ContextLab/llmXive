"""
Validation script for T028: Validate all output artifacts against spec.md requirements.

This script verifies the existence and structural integrity of the following artifacts:
1. data/processed/metrics.csv
2. results/correlations.json
3. results/model_performance.json
4. results/final_report.md

It checks against requirements derived from the project specification:
- metrics.csv: Must contain network metrics and thermal conductivity.
- correlations.json: Must contain Pearson/Spearman coefficients and Bonferroni-corrected p-values.
- model_performance.json: Must contain R² and RMSE for multiple folds.
- final_report.md: Must contain the mandatory "Limitations" text.
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

ARTIFACTS_TO_CHECK = [
    {
        "path": "data/processed/metrics.csv",
        "type": "csv",
        "required_columns": ["material_id", "thermal_conductivity", "average_degree", "average_shortest_path_length", "clustering_coefficient"],
        "min_rows": 50
    },
    {
        "path": "results/correlations.json",
        "type": "json",
        "required_keys": ["pearson", "spearman"],
        "structure_check": "keys must include 'coefficient' and 'p_value' for each metric"
    },
    {
        "path": "results/model_performance.json",
        "type": "json",
        "required_keys": ["r2_scores", "rmse_scores", "mean_r2", "mean_rmse"],
        "structure_check": "r2_scores and rmse_scores must be lists with >= 2 items"
    },
    {
        "path": "results/final_report.md",
        "type": "text",
        "required_text": "This study is observational. Correlations do not imply causality. The thermal conductivity tensor was reduced to a scalar by averaging principal components, which may obscure anisotropic effects."
    }
]

def check_csv_artifact(artifact: Dict[str, Any]) -> Tuple[bool, str]:
    """Validates a CSV file."""
    file_path = PROJECT_ROOT / artifact["path"]
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return False, "CSV is empty or has no headers"

            missing_cols = set(artifact["required_columns"]) - set(headers)
            if missing_cols:
                return False, f"Missing required columns: {missing_cols}"

            row_count = sum(1 for _ in reader)
            if row_count < artifact["min_rows"]:
                return False, f"Insufficient rows: {row_count} (required >= {artifact['min_rows']})"
            
            return True, f"Valid CSV with {row_count} rows and all required columns."
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}"

def check_json_artifact(artifact: Dict[str, Any]) -> Tuple[bool, str]:
    """Validates a JSON file."""
    file_path = PROJECT_ROOT / artifact["path"]
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return False, "JSON root must be an object"

        missing_keys = set(artifact["required_keys"]) - set(data.keys())
        if missing_keys:
            return False, f"Missing required keys: {missing_keys}"

        # Specific structure checks
        if "structure_check" in artifact:
            if "r2_scores" in artifact["required_keys"] or "rmse_scores" in artifact["required_keys"]:
                r2_list = data.get("r2_scores", [])
                rmse_list = data.get("rmse_scores", [])
                if not isinstance(r2_list, list) or not isinstance(rmse_list, list):
                    return False, "r2_scores and rmse_scores must be lists"
                if len(r2_list) < 2 or len(rmse_list) < 2:
                    return False, f"Need at least 2 folds, found {len(r2_list)} R2 scores and {len(rmse_list)} RMSE scores"
            
            if "keys must include 'coefficient' and 'p_value'" in artifact["structure_check"]:
                # Check correlations structure
                for key in data:
                    if isinstance(data[key], dict):
                        if "coefficient" not in data[key] or "p_value" not in data[key]:
                            return False, f"Correlation entry '{key}' missing 'coefficient' or 'p_value'"
                    elif isinstance(data[key], list):
                        # Handle list of correlations if structured differently
                        if len(data[key]) > 0 and isinstance(data[key][0], dict):
                            if "coefficient" not in data[key][0] or "p_value" not in data[key][0]:
                                return False, "Correlation list entries missing 'coefficient' or 'p_value'"

        return True, "Valid JSON with required structure."
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {str(e)}"
    except Exception as e:
        return False, f"Error reading JSON: {str(e)}"

def check_text_artifact(artifact: Dict[str, Any]) -> Tuple[bool, str]:
    """Validates a text/markdown file."""
    file_path = PROJECT_ROOT / artifact["path"]
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_text = artifact["required_text"]
        if required_text not in content:
            return False, f"Missing required text block:\n{required_text}"
        
        return True, "Text file contains all required content."
    except Exception as e:
        return False, f"Error reading text file: {str(e)}"

def main() -> int:
    """Main entry point for validation."""
    logger.info("Starting artifact validation for T028...")
    all_passed = True

    for artifact in ARTIFACTS_TO_CHECK:
        artifact_type = artifact["type"]
        logger.info(f"Checking {artifact['path']} ({artifact_type})...")

        if artifact_type == "csv":
            passed, message = check_csv_artifact(artifact)
        elif artifact_type == "json":
            passed, message = check_json_artifact(artifact)
        elif artifact_type == "text":
            passed, message = check_text_artifact(artifact)
        else:
            logger.warning(f"Unknown artifact type: {artifact_type}")
            passed = False
            message = "Unknown type"

        if passed:
            logger.info(f"  [PASS] {artifact['path']}: {message}")
        else:
            logger.error(f"  [FAIL] {artifact['path']}: {message}")
            all_passed = False

    if all_passed:
        logger.info("All artifacts validated successfully.")
        return 0
    else:
        logger.error("Validation failed for one or more artifacts.")
        return 1

if __name__ == "__main__":
    sys.exit(main())