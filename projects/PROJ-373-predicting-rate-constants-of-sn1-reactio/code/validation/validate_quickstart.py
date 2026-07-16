"""
Validation script for quickstart.md against actual execution.

This script verifies that the instructions in quickstart.md match the steps
and outputs generated in the integration test (T033).
"""
import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logging, get_logger

# Configure logging
logger = setup_logging(level=logging.INFO)

# Define expected artifacts from integration test (T033)
EXPECTED_ARTIFACTS = [
    "data/processed/cleaned_sn1.csv",
    "data/processed/train.csv",
    "data/processed/val.csv",
    "data/processed/test.csv",
    "artifacts/best_model.pt",
    "artifacts/metrics.json",
    "artifacts/hyperparameter_search.log",
    "artifacts/feature_importance.png",
    "artifacts/sensitivity_report.csv",
    "artifacts/perturbation_results.csv",
    "artifacts/integration_test_report.md",
    "specs/001-predict-sn1-rate-constants/quickstart.md",
]

# Define expected steps from quickstart.md
EXPECTED_STEPS = [
    "Install dependencies",
    "Run data ingestion",
    "Run preprocessing",
    "Run model training",
    "Run evaluation",
    "Run interpretability analysis",
    "Verify outputs",
]

def run_command(cmd: list, timeout: int = 300) -> tuple:
    """Run a command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def verify_artifact(path: str) -> bool:
    """Check if an artifact exists and is non-empty."""
    full_path = PROJECT_ROOT / path
    if not full_path.exists():
        return False
    if full_path.is_file() and full_path.stat().st_size == 0:
        return False
    return True

def validate_quickstart_instructions(quickstart_path: str) -> dict:
    """
    Validate quickstart.md against actual execution.

    Returns a report with validation results.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "quickstart_path": quickstart_path,
        "artifacts_check": {},
        "steps_check": {},
        "overall_status": "PASS",
        "issues": [],
    }

    # Check if quickstart.md exists
    if not verify_artifact(quickstart_path):
        report["overall_status"] = "FAIL"
        report["issues"].append(f"quickstart.md not found at {quickstart_path}")
        return report

    # Read quickstart.md content
    with open(PROJECT_ROOT / quickstart_path, "r") as f:
        quickstart_content = f.read()

    # Check if expected steps are mentioned
    for step in EXPECTED_STEPS:
        step_key = step.lower().replace(" ", "_")
        found = step.lower() in quickstart_content.lower()
        report["steps_check"][step_key] = {
            "step": step,
            "found_in_quickstart": found,
        }
        if not found:
            report["issues"].append(f"Step '{step}' not found in quickstart.md")
            report["overall_status"] = "FAIL"

    # Verify all expected artifacts exist
    for artifact in EXPECTED_ARTIFACTS:
        exists = verify_artifact(artifact)
        report["artifacts_check"][artifact] = {
            "exists": exists,
            "path": artifact,
        }
        if not exists:
            report["issues"].append(f"Artifact missing: {artifact}")
            report["overall_status"] = "FAIL"

    # Generate validation summary
    report["summary"] = {
        "total_steps": len(EXPECTED_STEPS),
        "steps_found": sum(1 for s in report["steps_check"].values() if s["found_in_quickstart"]),
        "total_artifacts": len(EXPECTED_ARTIFACTS),
        "artifacts_present": sum(1 for a in report["artifacts_check"].values() if a["exists"]),
        "issues_count": len(report["issues"]),
    }

    return report

def main():
    """Main entry point for validation."""
    parser = argparse.ArgumentParser(description="Validate quickstart.md against execution")
    parser.add_argument(
        "--quickstart",
        type=str,
        default="specs/001-predict-sn1-rate-constants/quickstart.md",
        help="Path to quickstart.md relative to project root",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/quickstart_validation_report.json",
        help="Path to output validation report",
    )
    args = parser.parse_args()

    logger.info(f"Validating quickstart.md: {args.quickstart}")

    # Run validation
    report = validate_quickstart_instructions(args.quickstart)

    # Save report
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to {output_path}")

    # Print summary
    logger.info(f"Overall Status: {report['overall_status']}")
    logger.info(f"Steps Found: {report['summary']['steps_found']}/{report['summary']['total_steps']}")
    logger.info(f"Artifacts Present: {report['summary']['artifacts_present']}/{report['summary']['total_artifacts']}")
    logger.info(f"Issues: {report['summary']['issues_count']}")

    if report["issues"]:
        logger.warning("Issues found:")
        for issue in report["issues"]:
            logger.warning(f"  - {issue}")

    # Return exit code based on validation status
    sys.exit(0 if report["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
