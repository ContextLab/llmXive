"""
Quickstart Validator for PROJ-082.
Validates end-to-end pipeline execution and artifact generation.
"""
import argparse
import json
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Ensure we can import project modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger

logger = get_logger(__name__)

def check_directories():
    """Verify required directory structure exists."""
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/derived",
        "data/logs",
        "paper",
        "contracts",
        "specs"
    ]
    missing = []
    for dir_name in required_dirs:
        path = PROJECT_ROOT / dir_name
        if not path.exists():
            missing.append(dir_name)
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created missing directory: {dir_name}")

    if missing:
        logger.warning(f"Created missing directories: {missing}")
    else:
        logger.info("All required directories exist.")
    return len(missing) == 0

def run_pipeline_execution():
    """Execute the main pipeline script and capture results."""
    main_script = PROJECT_ROOT / "code" / "main.py"
    if not main_script.exists():
        logger.error(f"Main script not found: {main_script}")
        return False

    logger.info("Starting pipeline execution...")
    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, str(main_script)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=900  # 15 minutes timeout
        )

        elapsed = time.time() - start_time
        logger.info(f"Pipeline execution finished in {elapsed:.2f} seconds.")

        if result.returncode != 0:
            logger.error(f"Pipeline failed with return code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            return False

        return True

    except subprocess.TimeoutExpired:
        logger.error("Pipeline execution timed out (>15 minutes)")
        return False
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        return False

def verify_artifacts():
    """Verify all expected output artifacts exist and are non-empty."""
    required_artifacts = [
        "data/processed/extracted_studies.csv",
        "data/processed/study_count.json",
        "data/processed/tract_count.json",
        "data/processed/meta_status.json",
        "data/derived/results.json",
        "data/logs/exclusion_log.csv",
        "data/logs/quickstart_report.md"
    ]

    # Conditionally required based on N
    # If N < 10, we expect narrative_summary.md instead of some quantitative plots
    # If N >= 10, we expect forest_plot.png, funnel_plot.png, correlation_summary.png

    missing = []
    for artifact in required_artifacts:
        path = PROJECT_ROOT / artifact
        if not path.exists():
            missing.append(artifact)
            logger.warning(f"Missing artifact: {artifact}")
        elif path.stat().st_size == 0:
            missing.append(artifact)
            logger.warning(f"Empty artifact: {artifact}")
        else:
            logger.info(f"Verified artifact: {artifact} ({path.stat().st_size} bytes)")

    # Check for plot artifacts if quantitative analysis ran
    meta_status_path = PROJECT_ROOT / "data" / "processed" / "meta_status.json"
    if meta_status_path.exists():
        with open(meta_status_path, 'r') as f:
            meta_status = json.load(f)
            if meta_status.get("status") == "completed":
                plots = [
                    "data/derived/forest_plot.png",
                    "data/derived/funnel_plot.png",
                    "data/derived/correlation_summary.png"
                ]
                for plot in plots:
                    path = PROJECT_ROOT / plot
                    if not path.exists():
                        missing.append(plot)
                        logger.warning(f"Missing plot: {plot}")
                    else:
                        logger.info(f"Verified plot: {plot} ({path.stat().st_size} bytes)")
            elif meta_status.get("status") == "skipped":
                narrative_path = PROJECT_ROOT / "data" / "derived" / "narrative_summary.md"
                if not narrative_path.exists():
                    missing.append("data/derived/narrative_summary.md")
                    logger.warning("Missing narrative summary (expected when meta-analysis skipped)")
                else:
                    logger.info(f"Verified narrative summary: {narrative_path} ({narrative_path.stat().st_size} bytes)")

    if missing:
        logger.error(f"Missing or empty artifacts: {missing}")
        return False

    logger.info("All required artifacts verified.")
    return True

def validate_json_content():
    """Validate JSON artifacts are well-formed."""
    json_files = [
        "data/processed/study_count.json",
        "data/processed/tract_count.json",
        "data/processed/meta_status.json",
        "data/derived/results.json"
    ]

    for json_file in json_files:
        path = PROJECT_ROOT / json_file
        if not path.exists():
            continue  # Already handled by verify_artifacts

        try:
            with open(path, 'r') as f:
                json.load(f)
            logger.info(f"Valid JSON: {json_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file}: {e}")
            return False

    return True

def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description="Quickstart Validator")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel("DEBUG")

    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation")
    logger.info("=" * 60)

    start_time = time.time()
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "checks": {},
        "errors": []
    }

    # Check 1: Directory Structure
    logger.info("Check 1: Directory Structure")
    dir_ok = check_directories()
    report["checks"]["directories"] = dir_ok
    if not dir_ok:
        report["errors"].append("Directory structure incomplete")

    # Check 2: Pipeline Execution
    logger.info("Check 2: Pipeline Execution")
    exec_ok = run_pipeline_execution()
    report["checks"]["execution"] = exec_ok
    if not exec_ok:
        report["status"] = "failed"
        report["errors"].append("Pipeline execution failed")
        # Even if execution fails, we continue to see what artifacts exist

    # Check 3: Artifact Verification
    logger.info("Check 3: Artifact Verification")
    art_ok = verify_artifacts()
    report["checks"]["artifacts"] = art_ok
    if not art_ok:
        report["status"] = "failed"
        report["errors"].append("Artifact verification failed")

    # Check 4: JSON Validation
    logger.info("Check 4: JSON Content Validation")
    json_ok = validate_json_content()
    report["checks"]["json_validation"] = json_ok
    if not json_ok:
        report["status"] = "failed"
        report["errors"].append("JSON validation failed")

    # Write Report
    report_path = PROJECT_ROOT / "data" / "logs" / "quickstart_report.md"
    ensure_directory(report_path.parent)

    elapsed = time.time() - start_time
    report["total_runtime_seconds"] = elapsed

    with open(report_path, 'w') as f:
        f.write("# Quickstart Validation Report\n\n")
        f.write(f"**Status**: {report['status'].upper()}\n")
        f.write(f"**Timestamp**: {report['timestamp']}\n")
        f.write(f"**Total Runtime**: {elapsed:.2f} seconds\n\n")

        f.write("## Check Results\n\n")
        for check, passed in report["checks"].items():
            status_icon = "✅" if passed else "❌"
            f.write(f"- {status_icon} **{check}**: {'Passed' if passed else 'Failed'}\n")

        if report["errors"]:
            f.write("\n## Errors\n\n")
            for error in report["errors"]:
                f.write(f"- {error}\n")

        f.write("\n## Summary\n\n")
        if report["status"] == "success":
            f.write("All validation checks passed. The pipeline executed successfully and produced all expected artifacts.\n")
        else:
            f.write("Validation failed. Please review the errors above and fix the underlying issues.\n")

    logger.info(f"Validation report written to: {report_path}")
    logger.info("=" * 60)

    if report["status"] == "success":
        logger.info("✅ Quickstart Validation PASSED")
        return 0
    else:
        logger.error("❌ Quickstart Validation FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
