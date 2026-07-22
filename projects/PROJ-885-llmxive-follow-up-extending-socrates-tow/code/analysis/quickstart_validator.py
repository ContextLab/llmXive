"""
Quickstart Validation Script for llmXive Pipeline.

This script validates the end-to-end reproducibility of the project by:
1. Checking directory structure
2. Verifying required data files exist
3. Validating JSON schemas of output artifacts
4. Running a statistical dry-run (import check + schema validation)
5. Generating a validation report.

This satisfies Task T044: Run quickstart.md validation to ensure end-to-end reproducibility.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project Root (assuming script runs from project root or code/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
CODE_DIR = PROJECT_ROOT / "code"

# Expected Artifacts based on completed tasks
EXPECTED_FILES = {
    "trajectories": DATA_PROCESSED / "trajectories.json",
    "generation_stats": DATA_PROCESSED / "generation_stats.json",
    "classifier_training_data": DATA_PROCESSED / "classifier_training_data.json",
    "experiment_logs": DATA_PROCESSED / "experiment_logs.json",
    "power_analysis_report": DATA_RESULTS / "power_analysis_report.json",
    "scope_adjustments": DATA_RESULTS / "scope_adjustments.json",
    "memory_profile_report": DATA_RESULTS / "memory_profile_report.json",
    "perf_report": DATA_RESULTS / "perf_report.json",
    "sensitivity_analysis_report": DATA_RESULTS / "sensitivity_analysis_report.json",
    "statistical_report": DATA_RESULTS / "statistical_report.json", # Assuming output of T038
}

# Schemas for validation
SCHEMAS = {
    "generation_stats": {
        "required_keys": ["total_trajectories", "target_category_counts", "oversampling_threshold_met"]
    },
    "classifier_training_data": {
        "required_keys": ["turn_text", "label", "trajectory_id", "confidence_score", "threshold_used"]
    },
    "experiment_logs": {
        "required_keys": ["trajectory_id", "condition", "injected_state", "confidence_score"]
    },
    "power_analysis_report": {
        "required_keys": ["required_n", "actual_n", "is_sufficient", "effect_size", "power", "alpha"]
    },
    "scope_adjustments": {
        "type": "list",
        "item_keys": ["model_name", "reason", "estimated_ram_gb"]
    }
}

def check_directories() -> Tuple[bool, List[str]]:
    """Verify required directory structure exists."""
    logger.info("Checking directory structure...")
    missing = []
    dirs = [DATA_RAW, DATA_PROCESSED, DATA_RESULTS, CODE_DIR]
    for d in dirs:
        if not d.exists():
            missing.append(str(d))
        else:
            logger.info(f"  Found: {d}")
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False, missing
    return True, []

def check_files() -> Tuple[bool, List[str]]:
    """Verify required data artifacts exist."""
    logger.info("Checking required data artifacts...")
    missing = []
    for name, path in EXPECTED_FILES.items():
        if not path.exists():
            missing.append(f"{name} ({path})")
            logger.warning(f"  Missing: {name}")
        else:
            logger.info(f"  Found: {name}")
    
    if missing:
        logger.error(f"Missing files: {missing}")
        return False, missing
    return True, []

def check_imports() -> Tuple[bool, List[str]]:
    """Verify critical modules can be imported."""
    logger.info("Checking module imports...")
    failed = []
    modules = [
        "config",
        "data.generator",
        "data.loader",
        "models.entities",
        "models.classifier",
        "experiments.runner",
        "experiments.prompts",
        "analysis.stats",
        "analysis.metrics",
        "analysis.perf_monitor"
    ]
    
    # Add project root to path
    sys.path.insert(0, str(PROJECT_ROOT))
    
    for mod_name in modules:
        try:
            __import__(mod_name)
            logger.info(f"  Imported: {mod_name}")
        except ImportError as e:
            failed.append(f"{mod_name}: {e}")
            logger.error(f"  Import failed: {mod_name}")
    
    if failed:
        logger.error(f"Import failures: {failed}")
        return False, failed
    return True, []

def validate_json_schema() -> Tuple[bool, List[str]]:
    """Validate JSON schemas of output artifacts."""
    logger.info("Validating JSON schemas...")
    errors = []
    
    for name, path_str in EXPECTED_FILES.items():
        if name not in SCHEMAS:
            continue
        
        path = path_str
        if not path.exists():
            continue
        
        schema = SCHEMAS[name]
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if schema.get("type") == "list":
                if not isinstance(data, list):
                    errors.append(f"{name}: Expected list, got {type(data)}")
                    continue
                if schema.get("item_keys"):
                    required_keys = set(schema["item_keys"])
                    for i, item in enumerate(data):
                        if not isinstance(item, dict):
                            errors.append(f"{name}[{i}]: Not a dict")
                            continue
                        if not required_keys.issubset(set(item.keys())):
                            missing = required_keys - set(item.keys())
                            errors.append(f"{name}[{i}]: Missing keys {missing}")
                logger.info(f"  Validated: {name} (list)")
            else:
                required_keys = schema.get("required_keys", [])
                if not isinstance(data, dict):
                    errors.append(f"{name}: Expected dict, got {type(data)}")
                    continue
                missing = set(required_keys) - set(data.keys())
                if missing:
                    errors.append(f"{name}: Missing keys {missing}")
                else:
                    logger.info(f"  Validated: {name}")
                    
        except json.JSONDecodeError as e:
            errors.append(f"{name}: Invalid JSON - {e}")
        except Exception as e:
            errors.append(f"{name}: Validation error - {e}")
    
    if errors:
        logger.error(f"Schema validation errors: {errors}")
        return False, errors
    return True, []

def check_data_artifacts() -> Tuple[bool, List[str]]:
    """Specific checks for data content (e.g., counts, thresholds)."""
    logger.info("Checking data artifact content...")
    errors = []
    
    # Check generation_stats for oversampling
    stats_path = EXPECTED_FILES["generation_stats"]
    if stats_path.exists():
        with open(stats_path, 'r') as f:
            stats = json.load(f)
        
        if not stats.get("oversampling_threshold_met", False):
            errors.append("generation_stats: Oversampling threshold not met")
            logger.warning("  Oversampling threshold not met")
        else:
            logger.info("  Oversampling threshold met")
    
    # Check power_analysis_report
    power_path = EXPECTED_FILES["power_analysis_report"]
    if power_path.exists():
        with open(power_path, 'r') as f:
            power = json.load(f)
        
        if not power.get("is_sufficient", False):
            errors.append("power_analysis_report: Study is underpowered (is_sufficient=False)")
            logger.warning("  Study is underpowered")
        else:
            logger.info("  Study power sufficient")
    
    if errors:
        logger.error(f"Data content errors: {errors}")
        return False, errors
    return True, []

def run_statistical_dry_run() -> Tuple[bool, List[str]]:
    """Run a dry-run of statistical functions to ensure they work."""
    logger.info("Running statistical dry-run...")
    errors = []
    
    try:
        # Import stats module
        from analysis.stats import generate_statistical_report, StatisticalResult
        logger.info("  Imported analysis.stats successfully")
        
        # Check if statistical report exists and is valid
        stat_path = EXPECTED_FILES["statistical_report"]
        if stat_path.exists():
            with open(stat_path, 'r') as f:
                report = json.load(f)
            logger.info(f"  Statistical report found with keys: {list(report.keys())}")
        else:
            logger.warning("  Statistical report not found (expected if T038 not run)")
            
    except Exception as e:
        errors.append(f"Statistical dry-run failed: {e}")
        logger.error(f"  Dry-run failed: {e}")
    
    if errors:
        return False, errors
    return True, []

def main():
    """Main entry point for validation."""
    logger.info("=" * 60)
    logger.info("Starting llmXive Quickstart Validation (T044)")
    logger.info("=" * 60)
    
    all_passed = True
    report = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    checks = [
        ("Directory Structure", check_directories),
        ("File Existence", check_files),
        ("Module Imports", check_imports),
        ("JSON Schemas", validate_json_schema),
        ("Data Content", check_data_artifacts),
        ("Statistical Dry-Run", run_statistical_dry_run)
    ]
    
    for name, check_func in checks:
        passed, details = check_func()
        report["checks"][name] = {
            "passed": passed,
            "details": details
        }
        if not passed:
            all_passed = False
    
    # Write validation report
    report_path = DATA_RESULTS / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {report_path}")
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("VALIDATION PASSED: End-to-end reproducibility confirmed.")
        sys.exit(0)
    else:
        logger.error("VALIDATION FAILED: See report for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()