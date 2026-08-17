import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Constants
DATA_CONFIG = DataConfig()

def setup_validation_logger() -> logging.Logger:
    """Setup logging for the validation stage."""
    logger = get_logger("final_validation")
    logger.setLevel(logging.INFO)
    return logger

def run_command(command: List[str], timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return (return_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def verify_artifact(path: Path, required: bool = True) -> Dict[str, Any]:
    """
    Verify that an artifact exists and is non-empty.
    Returns a dict with status and details.
    """
    result = {
        "path": str(path),
        "exists": path.exists(),
        "non_empty": False,
        "status": "missing"
    }
    
    if path.exists():
        try:
            size = path.stat().st_size
            result["size_bytes"] = size
            result["non_empty"] = size > 0
            result["status"] = "valid" if result["non_empty"] else "empty"
        except Exception as e:
            result["status"] = f"error: {e}"
    
    return result

def compare_with_integration_test(integration_report_path: Path, final_report_path: Path) -> Dict[str, Any]:
    """
    Compare the final validation results with the integration test results.
    Returns a comparison report.
    """
    comparison = {
        "integration_test_passed": False,
        "final_validation_passed": False,
        "discrepancies": []
    }
    
    # Load integration test report
    if integration_report_path.exists():
        try:
            with open(integration_report_path, 'r', encoding='utf-8') as f:
                integration_data = json.load(f)
            comparison["integration_test_passed"] = integration_data.get("status") == "success"
        except Exception as e:
            comparison["integration_test_error"] = str(e)
    
    # Load final validation report
    if final_report_path.exists():
        try:
            with open(final_report_path, 'r', encoding='utf-8') as f:
                final_data = json.load(f)
            comparison["final_validation_passed"] = final_data.get("status") == "success"
        except Exception as e:
            comparison["final_validation_error"] = str(e)
    
    # Compare results
    if comparison["integration_test_passed"] != comparison["final_validation_passed"]:
        comparison["discrepancies"].append(
            "Integration test and final validation results differ"
        )
    
    return comparison

def run_full_validation(logger: logging.Logger) -> Dict[str, Any]:
    """
    Run the full validation process.
    Returns a validation report.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "artifacts": {},
        "pipeline_status": "unknown",
        "comparison": {}
    }
    
    # Define artifacts to verify
    artifacts = [
        DATA_CONFIG.PROCESSED_DIR / "cleaned_sn1.csv",
        DATA_CONFIG.PROCESSED_DIR / "exclusion_report.csv",
        DATA_CONFIG.PROCESSED_DIR / "success_rate.json",
        DATA_CONFIG.PROCESSED_DIR / "post_filter_distribution.json",
        Path("artifacts/metrics.json"),
        Path("artifacts/best_model.pt"),
        Path("artifacts/collinearity_report.json"),
        Path("artifacts/sensitivity_report.csv"),
        Path("artifacts/perturbation_results.csv"),
        Path("artifacts/shap_consistency_report.md"),
        Path("artifacts/final_report.md"),
        Path("artifacts/feasibility_test_log.json"),
    ]
    
    # Verify each artifact
    for artifact_path in artifacts:
        result = verify_artifact(artifact_path)
        report["artifacts"][str(artifact_path)] = result
    
    # Run the full pipeline
    logger.info("Running full pipeline validation")
    return_code, stdout, stderr = run_command(
        ["python", "code/main.py"],
        timeout=None  # No timeout as per task requirements
    )
    
    report["pipeline_status"] = "success" if return_code == 0 else "failed"
    report["pipeline_return_code"] = return_code
    
    if return_code != 0:
        report["pipeline_error"] = stderr
    
    # Compare with integration test
    integration_report_path = Path("artifacts/integration_test_report.md")
    final_report_path = Path("artifacts/final_report.md")
    report["comparison"] = compare_with_integration_test(integration_report_path, final_report_path)
    
    return report

def main():
    """Main entry point for the final validation stage."""
    parser = argparse.ArgumentParser(description="Run final validation of the pipeline")
    parser.add_argument("--output", type=str, default="artifacts/final_validation_report.json",
                      help="Path to save the validation report")
    
    args = parser.parse_args()
    
    logger = setup_validation_logger()
    logger.info("Starting final validation")
    
    try:
        # Ensure directories exist
        ensure_dirs(DATA_CONFIG)
        
        # Run validation
        report = run_full_validation(logger)
        
        # Save report
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {output_path}")
        
        # Return appropriate exit code
        if report["pipeline_status"] == "success":
            logger.info("Final validation completed successfully")
            return 0
        else:
            logger.warning("Final validation completed with errors")
            return 1
        
    except Exception as e:
        logger.error(f"Error during final validation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())
