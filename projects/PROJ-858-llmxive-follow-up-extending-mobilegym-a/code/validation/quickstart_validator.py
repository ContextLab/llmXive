import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger

logger = get_logger("quickstart_validator")

def check_file_exists(path_str: str, description: str) -> bool:
    """Check if a required file exists."""
    path = PROJECT_ROOT / path_str
    if not path.exists():
        logger.error(f"Missing required file: {path_str} ({description})")
        return False
    logger.info(f"Found required file: {path_str} ({description})")
    return True

def validate_structure() -> bool:
    """Validate the basic project directory structure."""
    required_dirs = [
        "code", "code/scheduler", "code/training", "code/analysis", "code/utils",
        "code/validation",
        "data/raw", "data/processed", "data/validation",
        "tests/unit", "tests/integration",
        "contracts", "docs"
    ]
    all_good = True
    for d in required_dirs:
        if not (PROJECT_ROOT / d).is_dir():
            logger.error(f"Missing directory: {d}")
            all_good = False
    if all_good:
        logger.info("Project structure validated successfully.")
    return all_good

def validate_scheduler() -> bool:
    """Validate that the scheduler module can be imported and has expected interface."""
    try:
        from scheduler.curriculum_scheduler import CurriculumScheduler
        # Check for expected methods based on task requirements
        required_methods = ['select_batch', 'update_state', 'reset']
        for method in required_methods:
            if not hasattr(CurriculumScheduler, method):
                logger.error(f"CurriculumScheduler missing method: {method}")
                return False
        logger.info("Scheduler module validated successfully.")
        return True
    except ImportError as e:
        logger.error(f"Failed to import scheduler module: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating scheduler: {e}")
        return False

def validate_analysis_modules() -> bool:
    """Validate that analysis modules can be imported."""
    modules_to_check = [
        ("analysis.convergence", ["load_config", "analyze_convergence"]),
        ("analysis.sensitivity", ["compute_pearson_correlation", "analyze_sensitivity"]),
        ("analysis.transfer", ["evaluate_transfer_performance"]),
    ]
    all_good = True
    for mod_name, funcs in modules_to_check:
        try:
            mod = __import__(mod_name, fromlist=[""])
            for func in funcs:
                if not hasattr(mod, func):
                    logger.error(f"Module {mod_name} missing function: {func}")
                    all_good = False
            logger.info(f"Module {mod_name} validated successfully.")
        except ImportError as e:
            logger.error(f"Failed to import analysis module {mod_name}: {e}")
            all_good = False
    return all_good

def validate_outputs() -> bool:
    """Validate that expected output artifacts exist and are non-empty."""
    required_outputs = [
        ("data/processed/scheduler_trace.json", "Scheduler trace log"),
        ("data/processed/coverage_vectors.json", "Coverage vectors"),
        ("data/processed/sensitivity_report.md", "Sensitivity report"),
        ("data/processed/baseline_logs.json", "Baseline logs"),
        ("data/processed/experimental_logs.json", "Experimental logs"),
        ("data/processed/convergence_results.json", "Convergence results"),
    ]
    all_good = True
    for path_str, desc in required_outputs:
        if not check_file_exists(path_str, desc):
            all_good = False
            continue
        path = PROJECT_ROOT / path_str
        if path.stat().st_size == 0:
            logger.error(f"File is empty: {path_str} ({desc})")
            all_good = False
        else:
            logger.info(f"File validated (size: {path.stat().st_size} bytes): {path_str}")
    return all_good

def run_validation() -> dict:
    """Run the full validation suite."""
    start_time = time.time()
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "success",
        "checks": {}
    }

    checks = [
        ("structure", validate_structure),
        ("scheduler", validate_scheduler),
        ("analysis_modules", validate_analysis_modules),
        ("outputs", validate_outputs),
    ]

    for name, func in checks:
        try:
            result = func()
            results["checks"][name] = {"passed": result, "error": None}
            if not result:
                results["status"] = "failed"
        except Exception as e:
            logger.exception(f"Check {name} raised exception: {e}")
            results["checks"][name] = {"passed": False, "error": str(e)}
            results["status"] = "failed"

    results["duration_seconds"] = time.time() - start_time
    return results

def main():
    """Entry point for the quickstart validator."""
    logger.info("Starting Quickstart Validation on CPU-only runner...")
    results = run_validation()

    # Write results to disk
    output_path = PROJECT_ROOT / "data/validation/quickstart_validation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Validation results written to: {output_path}")

    if results["status"] == "success":
        logger.info("✅ Quickstart validation PASSED. End-to-end pipeline is functional.")
        return 0
    else:
        logger.error("❌ Quickstart validation FAILED. See logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())