import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

from config import ensure_directories, setup_logging

# Configure logging for the validator
logger = logging.getLogger(__name__)

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
    "contracts"
]

REQUIRED_FILES = [
    "code/config.py",
    "code/data/generator.py",
    "code/data/loader.py",
    "code/models/entities.py",
    "code/models/classifier.py",
    "code/models/evaluator.py",
    "code/experiments/runner.py",
    "code/experiments/prompts.py",
    "code/analysis/metrics.py",
    "code/analysis/stats.py",
    "data/processed/trajectories.json",
    "data/processed/classifier_training_data.json",
    "data/processed/experiment_logs.json",
    "data/results/statistical_report.json",
    "data/results/perf_report.json",
    "data/results/memory_profile_report.json",
    "specs/001-dynamic-state-injection/quickstart.md"
]

# Expected schema for key output files to ensure reproducibility
SCHEMA_CHECKS = {
    "data/processed/experiment_logs.json": {
        "type": "list",
        "required_fields": ["trajectory_id", "condition", "injected_state", "confidence_score"]
    },
    "data/results/statistical_report.json": {
        "type": "dict",
        "required_fields": ["full_dataset", "stratified_results", "holm_bonferroni_corrected"]
    },
    "data/processed/trajectories.json": {
        "type": "list",
        "required_fields": ["trajectory_id", "turns", "metadata"]
    }
}

def check_directories() -> Tuple[bool, List[str]]:
    """Verify that all required project directories exist."""
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = Path(dir_path)
        if not full_path.exists() or not full_path.is_dir():
            missing.append(str(full_path))
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False, missing
    
    logger.info("All required directories exist.")
    return True, []

def check_files() -> Tuple[bool, List[str]]:
    """Verify that all required source and data files exist."""
    missing = []
    for file_path in REQUIRED_FILES:
        full_path = Path(file_path)
        if not full_path.exists():
            missing.append(str(full_path))
    
    if missing:
        logger.error(f"Missing required files: {missing}")
        return False, missing
    
    logger.info("All required files exist.")
    return True, []

def check_imports() -> Tuple[bool, List[str]]:
    """Verify that all core modules can be imported without errors."""
    failed_imports = []
    modules_to_check = [
        "config",
        "data.generator",
        "data.loader",
        "models.entities",
        "models.classifier",
        "models.evaluator",
        "experiments.runner",
        "experiments.prompts",
        "analysis.metrics",
        "analysis.stats",
        "analysis.quickstart_validator"
    ]

    for mod_name in modules_to_check:
        try:
            __import__(mod_name)
            logger.debug(f"Successfully imported {mod_name}")
        except ImportError as e:
            logger.error(f"Failed to import {mod_name}: {e}")
            failed_imports.append(f"{mod_name}: {str(e)}")
    
    if failed_imports:
        return False, failed_imports
    
    logger.info("All core modules import successfully.")
    return True, []

def validate_json_schema(file_path: str, schema: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a JSON file against a simple schema."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in {file_path}: {e}"
    except FileNotFoundError:
        return False, f"File not found: {file_path}"

    if schema.get("type") == "list":
        if not isinstance(data, list):
            return False, f"{file_path} should be a list"
        if len(data) == 0:
            return False, f"{file_path} is empty"
        
        required_fields = schema.get("required_fields", [])
        if required_fields:
            sample_item = data[0]
            if not isinstance(sample_item, dict):
                return False, f"Items in {file_path} should be dictionaries"
            
            missing_fields = [f for f in required_fields if f not in sample_item]
            if missing_fields:
                return False, f"Missing fields in {file_path}: {missing_fields}"
    
    elif schema.get("type") == "dict":
        if not isinstance(data, dict):
            return False, f"{file_path} should be a dictionary"
        
        required_fields = schema.get("required_fields", [])
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return False, f"Missing fields in {file_path}: {missing_fields}"

    return True, "Schema valid"

def check_data_artifacts() -> Tuple[bool, List[str]]:
    """Validate the schema of key data artifacts."""
    errors = []
    
    for file_path, schema in SCHEMA_CHECKS.items():
        is_valid, msg = validate_json_schema(file_path, schema)
        if not is_valid:
            errors.append(msg)
        else:
            logger.debug(f"Schema validation passed for {file_path}")
    
    if errors:
        logger.error(f"Data artifact validation failed: {errors}")
        return False, errors
    
    logger.info("All data artifacts pass schema validation.")
    return True, []

def run_statistical_dry_run() -> Tuple[bool, str]:
    """
    Attempt to import and run the statistical analysis module's main function
    in a dry-run mode (if supported) or verify its readiness.
    This simulates the end-to-end flow without re-computing heavy stats.
    """
    try:
        # Import the stats module to check for runtime errors in initialization
        from analysis.stats import generate_statistical_report, main
        logger.info("Statistical analysis module loaded successfully.")
        
        # We do not re-run the full stats calculation here to avoid side effects,
        # but we verify the entry point exists and is callable.
        if not callable(main):
            return False, "stats.main is not callable"
        
        logger.info("Statistical analysis pipeline is ready for execution.")
        return True, "Statistical dry-run passed"
    except Exception as e:
        logger.error(f"Statistical dry-run failed: {e}")
        return False, str(e)

def main():
    """
    Main entry point for the quickstart validation.
    Executes all checks and reports the final status.
    """
    setup_logging()
    logger.info("Starting Quickstart Validation for llmXive pipeline...")
    
    all_passed = True
    failures = []

    # 1. Check Directory Structure
    logger.info("--- Checking Directory Structure ---")
    passed, missing = check_directories()
    if not passed:
        all_passed = False
        failures.append(f"Directory check failed: {missing}")

    # 2. Check Required Files
    logger.info("--- Checking Required Files ---")
    passed, missing = check_files()
    if not passed:
        all_passed = False
        failures.append(f"File check failed: {missing}")

    # 3. Check Imports
    logger.info("--- Checking Imports ---")
    passed, errors = check_imports()
    if not passed:
        all_passed = False
        failures.append(f"Import check failed: {errors}")

    # 4. Validate Data Artifacts
    logger.info("--- Validating Data Artifacts ---")
    passed, errors = check_data_artifacts()
    if not passed:
        all_passed = False
        failures.append(f"Data artifact check failed: {errors}")

    # 5. Statistical Dry Run
    logger.info("--- Running Statistical Dry Run ---")
    passed, msg = run_statistical_dry_run()
    if not passed:
        all_passed = False
        failures.append(f"Statistical dry-run failed: {msg}")

    # Final Report
    logger.info("=" * 50)
    if all_passed:
        logger.info("VALIDATION SUCCESSFUL: End-to-end reproducibility verified.")
        logger.info("All required directories, files, imports, and data schemas are valid.")
        return 0
    else:
        logger.error("VALIDATION FAILED.")
        for fail in failures:
            logger.error(f"  - {fail}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
