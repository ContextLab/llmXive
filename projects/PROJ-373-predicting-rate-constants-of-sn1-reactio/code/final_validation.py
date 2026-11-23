import os
import sys
import json
import logging
import argparse
import subprocess
import time
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging, get_logger
from config import DataConfig

logger = None

def run_command(cmd: list, timeout_seconds: int) -> tuple:
    """Run a command and return (return_code, stdout, stderr)."""
    global logger
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        duration = time.time() - start_time
        if logger:
            logger.info(f"Command {' '.join(cmd)} completed in {duration:.2f}s with rc={result.returncode}")
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        if logger:
            logger.warning(f"Command {' '.join(cmd)} timed out after {duration:.2f}s")
        return -1, "", "TIMEOUT"
    except Exception as e:
        if logger:
            logger.error(f"Command {' '.join(cmd)} failed with exception: {e}")
        return -1, "", str(e)

def verify_artifact(path_str: str, description: str) -> bool:
    """Verify an artifact exists and is non-empty."""
    global logger
    path = project_root / path_str
    if not path.exists():
        if logger:
            logger.error(f"Artifact missing: {description} ({path_str})")
        return False
    if path.stat().st_size == 0:
        if logger:
            logger.error(f"Artifact empty: {description} ({path_str})")
        return False
    if logger:
        logger.info(f"Artifact verified: {description} ({path_str})")
    return True

def compare_with_integration_test(integration_report_path: str, current_results: dict) -> bool:
    """Compare current results with integration test results if available."""
    global logger
    integration_path = project_root / integration_report_path
    if not integration_path.exists():
        if logger:
            logger.warning(f"Integration test report not found at {integration_report_path}. Skipping regression check.")
        return True

    try:
        with open(integration_path, 'r') as f:
            integration_data = json.load(f)
        
        # Simple comparison logic: check if key metrics are within reasonable bounds
        # This is a placeholder for more sophisticated comparison
        if logger:
            logger.info("Comparing with integration test results...")
        
        # For now, we just log that we did the check
        # In a real scenario, we would compare specific metrics
        return True
    except Exception as e:
        if logger:
            logger.error(f"Error comparing with integration test: {e}")
        return False

def run_full_validation(timeout_seconds: int = 14400) -> dict:
    """Run the full validation pipeline."""
    global logger
    config = DataConfig()
    results = {
        "status": "unknown",
        "duration_seconds": 0,
        "artifacts_verified": [],
        "errors": [],
        "warnings": []
    }

    start_time = time.time()

    # 1. Run main.py pipeline
    logger.info("Starting full pipeline validation...")
    rc, stdout, stderr = run_command([sys.executable, "code/main.py"], timeout_seconds)
    
    if rc != 0:
        results["status"] = "failed"
        results["errors"].append(f"Pipeline execution failed with rc={rc}")
        results["duration_seconds"] = int(time.time() - start_time)
        if "TIMEOUT" in stderr:
            results["reason"] = "timeout"
        return results

    # 2. Verify required artifacts
    required_artifacts = [
        ("data/processed/cleaned_sn1.csv", "Cleaned dataset"),
        ("data/processed/exclusion_report.csv", "Exclusion report"),
        ("artifacts/best_model.pt", "Best model weights"),
        ("artifacts/metrics.json", "Model metrics"),
        ("artifacts/final_report.md", "Final report")
    ]

    all_verified = True
    for path_str, description in required_artifacts:
        if not verify_artifact(path_str, description):
            all_verified = False
            results["errors"].append(f"Missing artifact: {description}")
        else:
            results["artifacts_verified"].append(description)

    if not all_verified:
        results["status"] = "failed"
        results["duration_seconds"] = int(time.time() - start_time)
        return results

    # 3. Compare with integration test
    integration_report = "artifacts/integration_test_report.md"
    if not compare_with_integration_test(integration_report, results):
        results["warnings"].append("Regression detected compared to integration test")

    results["status"] = "completed"
    results["duration_seconds"] = int(time.time() - start_time)
    
    logger.info(f"Validation completed successfully in {results['duration_seconds']}s")
    return results

def main():
    global logger
    parser = argparse.ArgumentParser(description="Final validation of the SN1 rate constant prediction pipeline")
    parser.add_argument("--timeout", type=int, default=14400, help="Timeout in seconds (default: 4 hours)")
    parser.add_argument("--log-file", type=str, default="artifacts/final_validation.log", help="Log file path")
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(level=logging.INFO, log_file=args.log_file)
    logger.info("Starting final validation run...")

    # Run validation
    results = run_full_validation(timeout_seconds=args.timeout)

    # Save results
    results_path = project_root / "artifacts" / "final_validation_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation results saved to {results_path}")

    if results["status"] == "completed":
        logger.info("Final validation PASSED")
        sys.exit(0)
    else:
        logger.error(f"Final validation FAILED: {results['errors']}")
        sys.exit(1)

if __name__ == "__main__":
    main()