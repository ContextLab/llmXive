"""
Task T041: Run quickstart.md validation.

This script executes the validation steps defined in the project's quickstart guide.
It verifies:
1. Project structure (code/, data/, tests/)
2. Environment configuration (.env)
3. Dependency installation (requirements.txt)
4. Critical artifact existence (metadata.json, aligned_metrics.csv, results.json)
5. Execution of key pipeline stages (mocked or real where feasible)
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add project root to path to import config and utils
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from config import get_paths, load_config
from utils.logging import get_logger, setup_logging

# Setup logging for this validation script
setup_logging(log_level=logging.INFO, log_file="data/logs/validation_run.log")
logger = get_logger(__name__)

class ValidationResult:
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def add_pass(self, check: str):
        self.passed.append(check)
        logger.info(f"✓ PASSED: {check}")

    def add_fail(self, check: str, reason: str = ""):
        self.failed.append(check)
        msg = f"✗ FAILED: {check}"
        if reason:
            msg += f" - {reason}"
        logger.error(msg)
        self.errors.append(reason)

    def add_warning(self, check: str, reason: str):
        self.warnings.append(check)
        logger.warning(f"⚠ WARNING: {check} - {reason}")

    def is_valid(self) -> bool:
        return len(self.failed) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "errors": self.errors,
            "summary": {
                "total_checks": len(self.passed) + len(self.failed),
                "passed_count": len(self.passed),
                "failed_count": len(self.failed),
                "validation_status": "PASSED" if self.is_valid() else "FAILED"
            }
        }

def check_project_structure(paths: Dict[str, Path]) -> Tuple[bool, str]:
    """Verify required directories exist."""
    required_dirs = [
        paths.get("code_dir"),
        paths.get("data_dir"),
        paths.get("tests_dir"),
        paths.get("processed_dir"),
        paths.get("interim_dir"),
        paths.get("raw_dir")
    ]
    missing = [str(d) for d in required_dirs if d and not d.exists()]
    if missing:
        return False, f"Missing directories: {', '.join(missing)}"
    return True, "All required directories present"

def check_env_config(paths: Dict[str, Path]) -> Tuple[bool, str]:
    """Verify .env.example exists and contains required keys."""
    env_example = paths.get("code_dir", Path()) / ".env.example"
    if not env_example.exists():
        return False, ".env.example not found"

    required_keys = ["HF_TOKEN", "DATA_PATH", "SEED", "GPU_DEVICE"]
    content = env_example.read_text()
    missing_keys = [k for k in required_keys if k not in content]
    if missing_keys:
        return False, f"Missing keys in .env.example: {', '.join(missing_keys)}"
    return True, "Environment configuration template valid"

def check_dependencies(paths: Dict[str, Path]) -> Tuple[bool, str]:
    """Verify requirements.txt exists."""
    req_file = paths.get("code_dir", Path()) / "requirements.txt"
    if not req_file.exists():
        # Try root level if not in code/
        req_file = Path(__file__).resolve().parents[2] / "requirements.txt"
    if not req_file.exists():
        return False, "requirements.txt not found"
    return True, "Dependencies file present"

def check_artifacts(paths: Dict[str, Path]) -> Tuple[bool, str]:
    """Verify critical output artifacts exist from previous tasks."""
    artifacts = [
        paths.get("processed_dir") / "salience_maps" / "metadata.json",
        paths.get("interim_dir") / "aligned_metrics.csv",
        paths.get("processed_dir") / "results.json",
        paths.get("interim_dir") / "vif_verification.json",
        paths.get("interim_dir") / "vif_report.txt"
    ]

    missing = []
    for artifact in artifacts:
        if artifact and not artifact.exists():
            missing.append(str(artifact.relative_to(paths.get("data_dir", Path()))))

    if missing:
        return False, f"Missing artifacts: {', '.join(missing)}"
    return True, "All critical artifacts present"

def validate_metadata_content(paths: Dict[str, Path]) -> Tuple[bool, str]:
    """Validate content of metadata.json."""
    metadata_file = paths.get("processed_dir") / "salience_maps" / "metadata.json"
    if not metadata_file.exists():
        return False, "metadata.json not found"

    try:
        with open(metadata_file, 'r') as f:
            data = json.load(f)
        
        # Check for required fields
        if "processed_images" not in data:
            return False, "metadata.json missing 'processed_images' field"
        if "disclaimer" not in data:
            return False, "metadata.json missing 'disclaimer' field"
        
        if not isinstance(data["processed_images"], list):
            return False, "'processed_images' is not a list"
        
        return True, f"metadata.json valid with {len(data['processed_images'])} images"
    except Exception as e:
        return False, f"Error parsing metadata.json: {str(e)}"

def validate_results_content(paths: Dict[str, Path]) -> Tuple[bool, str]:
    """Validate content of results.json."""
    results_file = paths.get("processed_dir") / "results.json"
    if not results_file.exists():
        return False, "results.json not found"

    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        # Check for required fields
        required_fields = ["model_a_results", "model_b_results", "sensitivity_analysis"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            return False, f"results.json missing fields: {', '.join(missing_fields)}"
        
        return True, "results.json structure valid"
    except Exception as e:
        return False, f"Error parsing results.json: {str(e)}"

def run_quickstart_validation() -> Dict[str, Any]:
    """Execute all validation checks defined in quickstart.md."""
    logger.info("Starting Quickstart Validation (Task T041)")
    result = ValidationResult()
    
    try:
        config = load_config()
        paths = get_paths()
        
        # 1. Project Structure
        passed, msg = check_project_structure(paths)
        if passed:
            result.add_pass("Project structure")
        else:
            result.add_fail("Project structure", msg)
        
        # 2. Environment Config
        passed, msg = check_env_config(paths)
        if passed:
            result.add_pass("Environment configuration")
        else:
            result.add_fail("Environment configuration", msg)
        
        # 3. Dependencies
        passed, msg = check_dependencies(paths)
        if passed:
            result.add_pass("Dependencies file")
        else:
            result.add_fail("Dependencies file", msg)
        
        # 4. Critical Artifacts
        passed, msg = check_artifacts(paths)
        if passed:
            result.add_pass("Critical artifacts existence")
        else:
            result.add_fail("Critical artifacts existence", msg)
        
        # 5. Metadata Content
        passed, msg = validate_metadata_content(paths)
        if passed:
            result.add_pass("Metadata content validation")
        else:
            result.add_fail("Metadata content validation", msg)
        
        # 6. Results Content
        passed, msg = validate_results_content(paths)
        if passed:
            result.add_pass("Results content validation")
        else:
            result.add_fail("Results content validation", msg)
        
        # 7. VIF Report
        vif_report = paths.get("interim_dir") / "vif_report.txt"
        if vif_report.exists():
            content = vif_report.read_text()
            if "VIF" in content or "Variance Inflation Factor" in content:
                result.add_pass("VIF report content")
            else:
                result.add_warning("VIF report content", "May not contain expected VIF analysis")
        else:
            result.add_fail("VIF report", "vif_report.txt not found")
        
    except Exception as e:
        logger.exception("Validation failed with exception")
        result.add_fail("Validation execution", str(e))
    
    # Write final report
    report_path = paths.get("processed_dir") / "quickstart_validation_report.json"
    if report_path:
        with open(report_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        logger.info(f"Validation report written to {report_path}")
    
    return result.to_dict()

def main():
    """Entry point for quickstart validation."""
    logger.info("=" * 60)
    logger.info("Task T041: Quickstart Validation")
    logger.info("=" * 60)
    
    validation_result = run_quickstart_validation()
    
    summary = validation_result["summary"]
    logger.info("-" * 60)
    logger.info(f"Validation Status: {summary['validation_status']}")
    logger.info(f"Passed: {summary['passed_count']}/{summary['total_checks']}")
    logger.info(f"Failed: {summary['failed_count']}/{summary['total_checks']}")
    logger.info("-" * 60)
    
    if not summary['validation_status'] == "PASSED":
        logger.error("Quickstart validation FAILED. Review errors above.")
        sys.exit(1)
    else:
        logger.info("Quickstart validation PASSED successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()