"""
Artifact Validation Module for T028.
Validates all output artifacts against spec.md requirements.
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging for this module
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = PROJECT_ROOT / "models"

# Artifact paths to validate
ARTIFACTS_TO_VALIDATE = {
    "metrics_csv": DATA_PROCESSED / "metrics.csv",
    "correlations_json": RESULTS_DIR / "correlations.json",
    "model_performance_json": RESULTS_DIR / "model_performance.json",
    "final_report_md": RESULTS_DIR / "final_report.md",
    "filtered_features_csv": DATA_PROCESSED / "filtered_features.csv",
    "network_manifest_json": DATA_PROCESSED / "network_manifest.json",
    "runtime_log": RESULTS_DIR / "runtime.log",
    "power_analysis_log": RESULTS_DIR / "power_analysis.log",
    "thermal_predictor_pkl": MODELS_DIR / "thermal_predictor.pkl",
}

# Required columns for metrics.csv (Network metrics + Thermal conductivity + Diagnostics)
REQUIRED_METRICS_COLUMNS = [
    "material_id",
    "average_degree",
    "average_shortest_path_length",
    "clustering_coefficient",
    "thermal_conductivity",
    "unit_cell_volume",
    "total_atom_count",
    "mean_atomic_mass"
]

# Required keys for correlations.json
REQUIRED_CORRELATION_KEYS = ["pearson", "spearman", "bonferroni_corrected_p_values"]

# Required keys for model_performance.json
REQUIRED_MODEL_KEYS = ["r2_scores", "rmse_scores", "mean_r2", "std_r2", "mean_rmse", "std_rmse", "r2_interpretation"]

# Mandatory text for final_report.md (Limitations section)
MANDATORY_LIMITATIONS_TEXT = (
    "This study is observational. Correlations do not imply causality. "
    "The thermal conductivity tensor was reduced to a scalar by averaging principal components, "
    "which may obscure anisotropic effects."
)

def check_csv_artifact(path: Path, required_columns: List[str]) -> Tuple[bool, str]:
    """Validate a CSV artifact exists, is non-empty, and has required columns."""
    if not path.exists():
        return False, f"File does not exist: {path}"
    
    if path.stat().st_size == 0:
        return False, f"File is empty: {path}"
    
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return False, f"CSV has no headers: {path}"
            
            missing_cols = [col for col in required_columns if col not in headers]
            if missing_cols:
                return False, f"Missing columns in {path}: {missing_cols}"
            
            # Check for at least one data row
            rows = list(reader)
            if not rows:
                return False, f"CSV has no data rows: {path}"
            
            return True, f"Valid CSV with {len(rows)} rows and correct headers"
    except Exception as e:
        return False, f"Error reading CSV {path}: {str(e)}"

def check_json_artifact(path: Path, required_keys: List[str], is_nested: bool = False) -> Tuple[bool, str]:
    """Validate a JSON artifact exists, is valid JSON, and contains required keys."""
    if not path.exists():
        return False, f"File does not exist: {path}"
    
    if path.stat().st_size == 0:
        return False, f"File is empty: {path}"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if is_nested:
            # For correlations.json, check nested structure
            for key in required_keys:
                if key not in data:
                    return False, f"Missing top-level key '{key}' in {path}"
                if isinstance(data[key], dict):
                    if not data[key]:
                        return False, f"Key '{key}' is empty in {path}"
        else:
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                return False, f"Missing keys in {path}: {missing_keys}"
        
        return True, f"Valid JSON with required keys"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in {path}: {str(e)}"
    except Exception as e:
        return False, f"Error reading JSON {path}: {str(e)}"

def check_text_artifact(path: Path, required_text: Optional[str] = None) -> Tuple[bool, str]:
    """Validate a text artifact exists, is non-empty, and optionally contains required text."""
    if not path.exists():
        return False, f"File does not exist: {path}"
    
    if path.stat().st_size == 0:
        return False, f"File is empty: {path}"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if required_text and required_text not in content:
            return False, f"Missing required text in {path}: '{required_text[:50]}...'"
        
        return True, f"Valid text file"
    except Exception as e:
        return False, f"Error reading text {path}: {str(e)}"

def main():
    """Main validation function for T028."""
    logger.info("Starting artifact validation for T028...")
    
    all_valid = True
    results = {}
    
    # 1. Validate metrics.csv
    logger.info("Validating data/processed/metrics.csv...")
    valid, msg = check_csv_artifact(ARTIFACTS_TO_VALIDATE["metrics_csv"], REQUIRED_METRICS_COLUMNS)
    results["metrics_csv"] = {"valid": valid, "message": msg}
    if not valid:
        all_valid = False
        logger.error(f"metrics.csv validation failed: {msg}")
    else:
        logger.info(f"metrics.csv validation passed: {msg}")
    
    # 2. Validate correlations.json
    logger.info("Validating results/correlations.json...")
    valid, msg = check_json_artifact(
        ARTIFACTS_TO_VALIDATE["correlations_json"], 
        REQUIRED_CORRELATION_KEYS, 
        is_nested=True
    )
    results["correlations_json"] = {"valid": valid, "message": msg}
    if not valid:
        all_valid = False
        logger.error(f"correlations.json validation failed: {msg}")
    else:
        logger.info(f"correlations.json validation passed: {msg}")
    
    # 3. Validate model_performance.json
    logger.info("Validating results/model_performance.json...")
    valid, msg = check_json_artifact(
        ARTIFACTS_TO_VALIDATE["model_performance_json"], 
        REQUIRED_MODEL_KEYS, 
        is_nested=False
    )
    results["model_performance_json"] = {"valid": valid, "message": msg}
    if not valid:
        all_valid = False
        logger.error(f"model_performance.json validation failed: {msg}")
    else:
        logger.info(f"model_performance.json validation passed: {msg}")
    
    # 4. Validate final_report.md
    logger.info("Validating results/final_report.md...")
    valid, msg = check_text_artifact(
        ARTIFACTS_TO_VALIDATE["final_report_md"], 
        required_text=MANDATORY_LIMITATIONS_TEXT
    )
    results["final_report_md"] = {"valid": valid, "message": msg}
    if not valid:
        all_valid = False
        logger.error(f"final_report.md validation failed: {msg}")
    else:
        logger.info(f"final_report.md validation passed: {msg}")
    
    # 5. Validate filtered_features.csv (T021 output)
    logger.info("Validating data/processed/filtered_features.csv...")
    if ARTIFACTS_TO_VALIDATE["filtered_features_csv"].exists():
        valid, msg = check_csv_artifact(ARTIFACTS_TO_VALIDATE["filtered_features_csv"], ["material_id"])
        results["filtered_features_csv"] = {"valid": valid, "message": msg}
        if not valid:
            all_valid = False
            logger.warning(f"filtered_features.csv validation failed: {msg}")
        else:
            logger.info(f"filtered_features.csv validation passed: {msg}")
    else:
        results["filtered_features_csv"] = {"valid": False, "message": "File does not exist"}
        all_valid = False
        logger.warning("filtered_features.csv does not exist")
    
    # 6. Validate network_manifest.json (T011 output)
    logger.info("Validating data/processed/network_manifest.json...")
    if ARTIFACTS_TO_VALIDATE["network_manifest_json"].exists():
        valid, msg = check_json_artifact(ARTIFACTS_TO_VALIDATE["network_manifest_json"], ["materials"])
        results["network_manifest_json"] = {"valid": valid, "message": msg}
        if not valid:
            all_valid = False
            logger.warning(f"network_manifest.json validation failed: {msg}")
        else:
            logger.info(f"network_manifest.json validation passed: {msg}")
    else:
        results["network_manifest_json"] = {"valid": False, "message": "File does not exist"}
        all_valid = False
        logger.warning("network_manifest.json does not exist")
    
    # 7. Validate runtime.log (T029 output)
    logger.info("Validating results/runtime.log...")
    if ARTIFACTS_TO_VALIDATE["runtime_log"].exists():
        valid, msg = check_text_artifact(ARTIFACTS_TO_VALIDATE["runtime_log"])
        results["runtime_log"] = {"valid": valid, "message": msg}
        if not valid:
            all_valid = False
            logger.warning(f"runtime.log validation failed: {msg}")
        else:
            # Check for < 6 hours assertion
            with open(ARTIFACTS_TO_VALIDATE["runtime_log"], 'r') as f:
                content = f.read()
                if "6 hours" in content and "<" not in content.split("6 hours")[0][-20:]:
                    logger.warning("runtime.log might indicate >= 6 hours, manual check recommended")
            logger.info(f"runtime.log validation passed: {msg}")
    else:
        results["runtime_log"] = {"valid": False, "message": "File does not exist"}
        all_valid = False
        logger.warning("runtime.log does not exist")
    
    # 8. Validate power_analysis.log (T018/T021 output)
    logger.info("Validating results/power_analysis.log...")
    if ARTIFACTS_TO_VALIDATE["power_analysis_log"].exists():
        valid, msg = check_text_artifact(ARTIFACTS_TO_VALIDATE["power_analysis_log"])
        results["power_analysis_log"] = {"valid": valid, "message": msg}
        if not valid:
            all_valid = False
            logger.warning(f"power_analysis.log validation failed: {msg}")
        else:
            logger.info(f"power_analysis.log validation passed: {msg}")
    else:
        results["power_analysis_log"] = {"valid": False, "message": "File does not exist"}
        all_valid = False
        logger.warning("power_analysis.log does not exist")
    
    # 9. Validate thermal_predictor.pkl (T022 output)
    logger.info("Validating models/thermal_predictor.pkl...")
    if ARTIFACTS_TO_VALIDATE["thermal_predictor_pkl"].exists():
        if ARTIFACTS_TO_VALIDATE["thermal_predictor_pkl"].stat().st_size > 0:
            results["thermal_predictor_pkl"] = {"valid": True, "message": "File exists and is non-empty"}
            logger.info("thermal_predictor.pkl validation passed")
        else:
            results["thermal_predictor_pkl"] = {"valid": False, "message": "File is empty"}
            all_valid = False
            logger.warning("thermal_predictor.pkl is empty")
    else:
        results["thermal_predictor_pkl"] = {"valid": False, "message": "File does not exist"}
        all_valid = False
        logger.warning("thermal_predictor.pkl does not exist")
    
    # Summary
    logger.info("=" * 50)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 50)
    
    for artifact, result in results.items():
        status = "PASS" if result["valid"] else "FAIL"
        logger.info(f"{artifact}: {status} - {result['message']}")
    
    if all_valid:
        logger.info("ALL ARTIFACTS VALIDATED SUCCESSFULLY")
        print("\n✓ All artifacts validated successfully.")
        print("  - metrics.csv: Contains required columns and data")
        print("  - correlations.json: Contains Pearson/Spearman/Bonferroni results")
        print("  - model_performance.json: Contains R², RMSE, and interpretation")
        print("  - final_report.md: Contains mandatory limitations text")
        return 0
    else:
        failed_count = sum(1 for r in results.values() if not r["valid"])
        logger.warning(f"VALIDATION FAILED: {failed_count} artifact(s) failed validation")
        print(f"\n✗ Validation failed: {failed_count} artifact(s) failed.")
        print("  Review logs above for details.")
        return 1

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    sys.exit(main())
