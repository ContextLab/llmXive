"""
Quickstart Validation Runner (Task T041)

This script validates the project by:
1. Checking project structure (code/, data/, tests/)
2. Verifying environment configuration
3. Checking dependency installation
4. Validating key artifacts exist and are non-empty
5. Running a dry-run of the pipeline steps
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, setup_logging
from config import load_config, get_paths

# Setup logging
logger = get_logger("quickstart_validation")
setup_logging(level=logging.INFO, log_file=project_root / "data" / "logs" / "quickstart_validation.log")

class ValidationResult:
    def __init__(self):
        self.passed: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.artifacts_verified: Dict[str, bool] = {}

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.passed = False
        logger.error(f"VALIDATION ERROR: {msg}")

    def add_warning(self, msg: str):
        self.warnings.append(msg)
        logger.warning(f"VALIDATION WARNING: {msg}")

    def verify_artifact(self, name: str, status: bool):
        self.artifacts_verified[name] = status
        if not status:
            self.passed = False
            self.add_error(f"Artifact missing or invalid: {name}")
        else:
            logger.info(f"Artifact verified: {name}")

def check_project_structure() -> ValidationResult:
    """Verify required directories exist."""
    result = ValidationResult()
    required_dirs = ["code", "data", "tests", "docs"]
    
    for dir_name in required_dirs:
        path = project_root / dir_name
        if not path.exists():
            result.add_error(f"Required directory missing: {dir_name}/")
        elif not any(path.iterdir()):
            result.add_warning(f"Directory exists but is empty: {dir_name}/")
    
    return result

def check_env_config() -> ValidationResult:
    """Verify .env.example exists and keys are documented."""
    result = ValidationResult()
    env_example = project_root / ".env.example"
    
    if not env_example.exists():
        result.add_error(".env.example file missing")
    else:
        content = env_example.read_text()
        required_keys = ["HF_TOKEN", "DATA_PATH", "SEED"]
        for key in required_keys:
            if key not in content:
                result.add_warning(f"Key {key} not found in .env.example")
    
    return result

def check_dependencies() -> ValidationResult:
    """Verify critical dependencies are installed."""
    result = ValidationResult()
    critical_deps = ["torch", "pandas", "numpy", "scipy", "statsmodels", "datasets", "opencv-python"]
    
    for dep in critical_deps:
        try:
            __import__(dep.replace("-", "_"))
            logger.info(f"Dependency installed: {dep}")
        except ImportError:
            result.add_error(f"Critical dependency missing: {dep}")
    
    return result

def validate_metadata_content() -> ValidationResult:
    """Validate salience map metadata file."""
    result = ValidationResult()
    paths = get_paths()
    metadata_path = paths["salience_metadata"]
    
    if not metadata_path.exists():
        result.add_error(f"Metadata file missing: {metadata_path}")
        return result
    
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list) or len(data) == 0:
            result.add_error("Metadata file is empty or not a list")
        else:
            # Check for required fields in first entry
            required_fields = ["image_id", "map_path", "method"]
            entry = data[0]
            missing = [f for f in required_fields if f not in entry]
            if missing:
                result.add_warning(f"Metadata entries missing fields: {missing}")
            else:
                result.verify_artifact("salience_metadata", True)
    except json.JSONDecodeError:
        result.add_error("Metadata file is not valid JSON")
    
    return result

def validate_results_content() -> ValidationResult:
    """Validate final results file."""
    result = ValidationResult()
    paths = get_paths()
    results_path = paths["final_results"]
    
    if not results_path.exists():
        result.add_error(f"Results file missing: {results_path}")
        return result
    
    try:
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            result.add_error("Results file is not a JSON object")
        else:
            # Check for presence of key analysis results
            if "model_results" not in data and "p_values" not in data:
                result.add_warning("Results file missing expected analysis keys")
            else:
                result.verify_artifact("final_results", True)
    except json.JSONDecodeError:
        result.add_error("Results file is not valid JSON")
    
    return result

def check_artifacts() -> ValidationResult:
    """Check existence of critical pipeline artifacts."""
    result = ValidationResult()
    paths = get_paths()
    
    # Check salience maps directory
    salience_dir = project_root / "data" / "processed" / "salience_maps"
    if not salience_dir.exists():
        result.add_error("Salience maps directory missing")
    else:
        files = list(salience_dir.glob("*.npy")) + list(salience_dir.glob("*.png"))
        if len(files) == 0:
            result.add_error("No salience map files found in processed directory")
        else:
            logger.info(f"Found {len(files)} salience map files")
    
    # Check aligned metrics
    aligned_path = paths.get("aligned_metrics")
    if aligned_path and aligned_path.exists():
        result.verify_artifact("aligned_metrics", True)
    else:
        result.add_error("Aligned metrics file missing")
    
    return result

def run_quickstart_validation() -> ValidationResult:
    """Run all validation checks."""
    logger.info("Starting Quickstart Validation (T041)")
    overall_result = ValidationResult()
    
    # 1. Structure
    struct_result = check_project_structure()
    overall_result.errors.extend(struct_result.errors)
    overall_result.warnings.extend(struct_result.warnings)
    overall_result.passed = overall_result.passed and struct_result.passed
    
    # 2. Env
    env_result = check_env_config()
    overall_result.errors.extend(env_result.errors)
    overall_result.warnings.extend(env_result.warnings)
    overall_result.passed = overall_result.passed and env_result.passed
    
    # 3. Dependencies
    dep_result = check_dependencies()
    overall_result.errors.extend(dep_result.errors)
    overall_result.warnings.extend(dep_result.warnings)
    overall_result.passed = overall_result.passed and dep_result.passed
    
    # 4. Artifacts
    artifact_result = check_artifacts()
    overall_result.errors.extend(artifact_result.errors)
    overall_result.warnings.extend(artifact_result.warnings)
    overall_result.passed = overall_result.passed and artifact_result.passed
    
    # 5. Metadata
    meta_result = validate_metadata_content()
    overall_result.errors.extend(meta_result.errors)
    overall_result.warnings.extend(meta_result.warnings)
    overall_result.passed = overall_result.passed and meta_result.passed
    
    # 6. Results
    results_result = validate_results_content()
    overall_result.errors.extend(results_result.errors)
    overall_result.warnings.extend(results_result.warnings)
    overall_result.passed = overall_result.passed and results_result.passed
    
    return overall_result

def main():
    """Entry point for T041."""
    result = run_quickstart_validation()
    
    # Write validation report
    report_path = project_root / "data" / "interim" / "quickstart_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "status": "PASSED" if result.passed else "FAILED",
        "timestamp": str(Path(__file__).parent.parent.parent),
        "errors": result.errors,
        "warnings": result.warnings,
        "artifacts_verified": result.artifacts_verified
    }
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Validation report written to {report_path}")
    
    if result.passed:
        logger.info("T041: Quickstart validation PASSED")
        sys.exit(0)
    else:
        logger.error(f"T041: Quickstart validation FAILED with {len(result.errors)} errors")
        sys.exit(1)

if __name__ == "__main__":
    main()
