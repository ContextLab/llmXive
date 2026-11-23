import os
import json
import sys
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_DIR, MODELS_DIR, REPORTS_DIR, ERRORS_DIR, LOG_DIR
from data.checksum import compute_sha256, load_checksums, verify_checksums, save_checksums
from utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

# Define expected artifacts based on completed tasks
EXPECTED_ARTIFACTS = [
    # Data Artifacts (from T008, T013, T014)
    "data/raw/fetched_diffusion.csv",
    "data/curated/filtered.csv",
    "data/logs/exclusions.log",
    "errors/missing_atomic_data.csv",
    
    # Model Artifacts (from T024, T025)
    "models/final_rf.pkl",
    "models/final_gb.pkl",
    "models/linear_coef.json",
    "models/metrics.json",
    
    # Report Artifacts (from T034)
    "reports/validation_report.json",
]

# Define expected checksum file
CHECKSUM_FILE = "data/artifacts/checksums.json"

def validate_artifact_exists(path_str: str) -> Tuple[bool, str]:
    """Check if an artifact exists at the specified path."""
    full_path = PROJECT_ROOT / path_str
    exists = full_path.exists()
    size = full_path.stat().st_size if exists else 0
    return exists, f"{'OK' if exists else 'MISSING'}: {path_str} (size: {size} bytes)"

def validate_file_not_empty(path_str: str) -> Tuple[bool, str]:
    """Check if an artifact is not empty."""
    full_path = PROJECT_ROOT / path_str
    if not full_path.exists():
        return False, f"MISSING: {path_str}"
    
    size = full_path.stat().st_size
    is_valid = size > 0
    return is_valid, f"{'OK' if is_valid else 'EMPTY'}: {path_str} (size: {size} bytes)"

def validate_json_structure(path_str: str, required_keys: List[str]) -> Tuple[bool, str]:
    """Validate a JSON file has required keys."""
    full_path = PROJECT_ROOT / path_str
    if not full_path.exists():
        return False, f"MISSING: {path_str}"
    
    try:
        with open(full_path, 'r') as f:
            data = json.load(f)
        
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            return False, f"INVALID JSON: {path_str} missing keys: {missing_keys}"
        
        return True, f"OK: {path_str} contains all required keys"
    except json.JSONDecodeError as e:
        return False, f"INVALID JSON: {path_str} - {str(e)}"

def validate_metrics_structure(path_str: str) -> Tuple[bool, str]:
    """Specific validation for models/metrics.json structure."""
    full_path = PROJECT_ROOT / path_str
    if not full_path.exists():
        return False, f"MISSING: {path_str}"
    
    try:
        with open(full_path, 'r') as f:
            data = json.load(f)
        
        # Check for RF and GB metrics
        if 'rf' not in data or 'gb' not in data:
            return False, f"INVALID: {path_str} missing 'rf' or 'gb' keys"
        
        # Check for required metrics in each model
        for model_type in ['rf', 'gb']:
            model_data = data[model_type]
            required_metrics = ['r2', 'rmse', 'mae']
            missing_metrics = [m for m in required_metrics if m not in model_data]
            if missing_metrics:
                return False, f"INVALID: {path_str} missing {missing_metrics} for {model_type}"
        
        return True, f"OK: {path_str} has valid structure"
    except json.JSONDecodeError as e:
        return False, f"INVALID JSON: {path_str} - {str(e)}"

def validate_checksums() -> Tuple[bool, str]:
    """Validate that all artifacts have checksums and verify them."""
    checksum_path = PROJECT_ROOT / CHECKSUM_FILE
    
    if not checksum_path.exists():
        logger.warning(f"Checksum file not found at {CHECKSUM_FILE}. Generating...")
        generate_checksums()
    
    try:
        with open(checksum_path, 'r') as f:
            checksums = json.load(f)
        
        # Verify all expected artifacts are in checksums
        missing_in_checksums = []
        for artifact in EXPECTED_ARTIFACTS:
            if artifact not in checksums:
                missing_in_checksums.append(artifact)
        
        if missing_in_checksums:
            return False, f"Missing checksums for: {missing_in_checksums}"
        
        # Verify checksums
        verification_results = verify_checksums()
        if not verification_results['all_valid']:
            invalid_files = [r['file'] for r in verification_results['results'] if not r['valid']]
            return False, f"Checksum verification failed for: {invalid_files}"
        
        return True, "All checksums valid"
    except Exception as e:
        return False, f"Checksum validation error: {str(e)}"

def generate_checksums():
    """Generate checksums for all expected artifacts."""
    checksums = {}
    
    for artifact_path in EXPECTED_ARTIFACTS:
        full_path = PROJECT_ROOT / artifact_path
        if full_path.exists():
            checksums[artifact_path] = compute_sha256(full_path)
        else:
            logger.warning(f"Artifact not found for checksum: {artifact_path}")
    
    # Ensure directory exists
    checksum_file_path = PROJECT_ROOT / CHECKSUM_FILE
    checksum_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checksum_file_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Generated checksums for {len(checksums)} artifacts at {CHECKSUM_FILE}")

def run_validation() -> Tuple[bool, Dict[str, Any]]:
    """Run all validation checks and return results."""
    results = {
        'artifacts_exist': [],
        'artifacts_not_empty': [],
        'json_valid': [],
        'checksums': [],
        'overall_success': True
    }
    
    # 1. Check all expected artifacts exist
    logger.info("Checking artifact existence...")
    for artifact in EXPECTED_ARTIFACTS:
        exists, message = validate_artifact_exists(artifact)
        results['artifacts_exist'].append({'artifact': artifact, 'valid': exists, 'message': message})
        if not exists:
            results['overall_success'] = False
            logger.error(f"Missing artifact: {artifact}")
    
    # 2. Check all artifacts are not empty
    logger.info("Checking artifact sizes...")
    for artifact in EXPECTED_ARTIFACTS:
        not_empty, message = validate_file_not_empty(artifact)
        results['artifacts_not_empty'].append({'artifact': artifact, 'valid': not_empty, 'message': message})
        if not not_empty:
            results['overall_success'] = False
            logger.error(f"Empty artifact: {artifact}")
    
    # 3. Validate JSON structures
    logger.info("Validating JSON structures...")
    
    # Validate models/metrics.json
    metrics_valid, metrics_msg = validate_metrics_structure("models/metrics.json")
    results['json_valid'].append({'file': 'models/metrics.json', 'valid': metrics_valid, 'message': metrics_msg})
    if not metrics_valid:
        results['overall_success'] = False
        logger.error(f"Invalid metrics structure: {metrics_msg}")
    
    # Validate reports/validation_report.json
    report_valid, report_msg = validate_json_structure(
        "reports/validation_report.json",
        ['r2', 'rmse', 'p_value', 'confidence_interval', 'stability_metrics']
    )
    results['json_valid'].append({'file': 'reports/validation_report.json', 'valid': report_valid, 'message': report_msg})
    if not report_valid:
        results['overall_success'] = False
        logger.error(f"Invalid report structure: {report_msg}")
    
    # Validate models/linear_coef.json
    coef_valid, coef_msg = validate_json_structure(
        "models/linear_coef.json",
        ['intercept', 'coefficients', 'p_values']
    )
    results['json_valid'].append({'file': 'models/linear_coef.json', 'valid': coef_valid, 'message': coef_msg})
    if not coef_valid:
        results['overall_success'] = False
        logger.error(f"Invalid coefficients structure: {coef_msg}")
    
    # 4. Validate checksums
    logger.info("Validating checksums...")
    checksum_valid, checksum_msg = validate_checksums()
    results['checksums'].append({'valid': checksum_valid, 'message': checksum_msg})
    if not checksum_valid:
        results['overall_success'] = False
        logger.error(f"Checksum validation failed: {checksum_msg}")
    
    return results['overall_success'], results

def main():
    """Main entry point for quickstart validation."""
    logger.info("Starting quickstart validation...")
    
    # Ensure directories exist
    from config import ensure_directories
    ensure_directories()
    
    # Run validation
    success, results = run_validation()
    
    # Print summary
    print("\n" + "="*60)
    print("QUICKSTART VALIDATION SUMMARY")
    print("="*60)
    
    print(f"\nOverall Status: {'✓ PASSED' if success else '✗ FAILED'}")
    
    print(f"\nArtifact Existence Check:")
    for item in results['artifacts_exist']:
        status = "✓" if item['valid'] else "✗"
        print(f"  {status} {item['message']}")
    
    print(f"\nArtifact Size Check:")
    for item in results['artifacts_not_empty']:
        status = "✓" if item['valid'] else "✗"
        print(f"  {status} {item['message']}")
    
    print(f"\nJSON Structure Check:")
    for item in results['json_valid']:
        status = "✓" if item['valid'] else "✗"
        print(f"  {status} {item['message']}")
    
    print(f"\nChecksum Validation:")
    for item in results['checksums']:
        status = "✓" if item['valid'] else "✗"
        print(f"  {status} {item['message']}")
    
    print("\n" + "="*60)
    
    if not success:
        logger.error("Validation failed. Please check the errors above.")
        sys.exit(1)
    else:
        logger.info("All validations passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()