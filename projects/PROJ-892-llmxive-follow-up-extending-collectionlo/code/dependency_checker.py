import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DependencyError(Exception):
    """Custom exception for missing dependencies."""
    pass

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def check_artifact_exists(artifact_path: str, description: str) -> bool:
    """Checks if an artifact exists at the given path."""
    full_path = get_project_root() / artifact_path
    if not full_path.exists():
        logger.error(f"Dependency Error: {description} not found at {full_path}")
        return False
    logger.info(f"Dependency Check Passed: {description} found at {full_path}")
    return True

def validate_baseline_generation() -> bool:
    """Validates that baseline generation artifacts exist."""
    return check_artifact_exists("data/generated/baseline/", "Baseline generation images")

def validate_other_effect_references() -> bool:
    """Validates that other effect references exist."""
    return check_artifact_exists("data/references/other_effect_refs.json", "Other effect references")

def validate_fp16_references() -> bool:
    """Validates that FP16 references exist."""
    return check_artifact_exists("data/references/fp16_refs/", "FP16 reference images")

def validate_subspace_ranks() -> bool:
    """Validates that subspace ranks exist."""
    return check_artifact_exists("data/subspace_ranks_merged.json", "Subspace ranks")

def validate_config() -> bool:
    """Validates that config exists."""
    return check_artifact_exists("code/config.yaml", "Configuration file")

def run_pre_flight_checks() -> None:
    """Runs all pre-flight checks and raises DependencyError if any fail."""
    checks = [
        ("Baseline Generation", validate_baseline_generation),
        ("Other Effect References", validate_other_effect_references),
        ("FP16 References", validate_fp16_references),
        ("Subspace Ranks", validate_subspace_ranks),
        ("Config", validate_config)
    ]
    
    failed = False
    for name, check_func in checks:
        if not check_func():
            failed = True
    
    if failed:
        raise DependencyError("Pre-flight checks failed. Missing required artifacts.")
    logger.info("All pre-flight checks passed.")

def main():
    """Main entry point for dependency_checker."""
    try:
        run_pre_flight_checks()
        logger.info("Dependency check successful.")
    except DependencyError as e:
        logger.error(f"Dependency check failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during dependency check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
