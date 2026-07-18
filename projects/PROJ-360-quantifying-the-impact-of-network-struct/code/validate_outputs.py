"""
Validation script for T028: Check that all required output artifacts exist
and contain the necessary keys/columns as defined in spec.md.

Exits with code 0 on success, code 1 on failure.
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("validate_outputs")

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = {
    "metrics_csv": PROJECT_ROOT / "data" / "processed" / "metrics.csv",
    "correlations_json": PROJECT_ROOT / "results" / "correlations.json",
    "model_performance_json": PROJECT_ROOT / "results" / "model_performance.json",
    "final_report_md": PROJECT_ROOT / "results" / "final_report.md"
}

# Required keys/columns based on spec.md and task descriptions
REQUIRED_KEYS = {
    "metrics_csv": {
        "columns": [
            "material_id",
            "average_degree",
            "average_shortest_path_length",
            "clustering_coefficient",
            "thermal_conductivity_scalar"
        ]
    },
    "correlations_json": {
        "keys": [
            "pearson_correlations",
            "spearman_correlations",
            "bonferroni_corrected_p_values",
            "alpha_threshold"
        ]
    },
    "model_performance_json": {
        "keys": [
            "r2_scores",
            "rmse_scores",
            "mean_r2",
            "std_r2",
            "mean_rmse",
            "std_rmse",
            "r2_interpretation"
        ]
    },
    "final_report_md": {
        "required_text": [
            "Limitations",
            "This study is observational. Correlations do not imply causality.",
            "The thermal conductivity tensor was reduced to a scalar by averaging principal components"
        ]
    }
}

def check_file_exists(path: Path) -> bool:
    """Check if a file exists."""
    if not path.exists():
        logger.error(f"File not found: {path}")
        return False
    if path.stat().st_size == 0:
        logger.error(f"File is empty: {path}")
        return False
    return True

def validate_csv(path: Path, required_columns: List[str]) -> bool:
    """Validate CSV file has required columns."""
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                logger.error(f"CSV file {path} has no headers")
                return False
            
            missing_cols = set(required_columns) - set(reader.fieldnames)
            if missing_cols:
                logger.error(f"CSV file {path} missing columns: {missing_cols}")
                return False
            
            # Check if there's at least one row
            rows = list(reader)
            if len(rows) == 0:
                logger.error(f"CSV file {path} has no data rows")
                return False
            
            logger.info(f"CSV file {path} validated successfully with {len(rows)} rows")
            return True
    except Exception as e:
        logger.error(f"Error reading CSV file {path}: {e}")
        return False

def validate_json(path: Path, required_keys: List[str]) -> bool:
    """Validate JSON file has required keys."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        missing_keys = set(required_keys) - set(data.keys())
        if missing_keys:
            logger.error(f"JSON file {path} missing keys: {missing_keys}")
            return False
        
        logger.info(f"JSON file {path} validated successfully")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading JSON file {path}: {e}")
        return False

def validate_text(path: Path, required_text: List[str]) -> bool:
    """Validate text file contains required text strings."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_text = []
        for text in required_text:
            if text not in content:
                missing_text.append(text)
        
        if missing_text:
            logger.error(f"Text file {path} missing required text: {missing_text}")
            return False
        
        logger.info(f"Text file {path} validated successfully")
        return True
    except Exception as e:
        logger.error(f"Error reading text file {path}: {e}")
        return False

def main() -> int:
    """Main validation function."""
    logger.info("Starting output validation for T028")
    
    all_passed = True
    
    # Check metrics.csv
    if not check_file_exists(ARTIFACTS["metrics_csv"]):
        all_passed = False
    elif not validate_csv(
        ARTIFACTS["metrics_csv"], 
        REQUIRED_KEYS["metrics_csv"]["columns"]
    ):
        all_passed = False
    
    # Check correlations.json
    if not check_file_exists(ARTIFACTS["correlations_json"]):
        all_passed = False
    elif not validate_json(
        ARTIFACTS["correlations_json"], 
        REQUIRED_KEYS["correlations_json"]["keys"]
    ):
        all_passed = False
    
    # Check model_performance.json
    if not check_file_exists(ARTIFACTS["model_performance_json"]):
        all_passed = False
    elif not validate_json(
        ARTIFACTS["model_performance_json"], 
        REQUIRED_KEYS["model_performance_json"]["keys"]
    ):
        all_passed = False
    
    # Check final_report.md
    if not check_file_exists(ARTIFACTS["final_report_md"]):
        all_passed = False
    elif not validate_text(
        ARTIFACTS["final_report_md"], 
        REQUIRED_KEYS["final_report_md"]["required_text"]
    ):
        all_passed = False
    
    if all_passed:
        logger.info("All validations passed!")
        return 0
    else:
        logger.error("Validation failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())