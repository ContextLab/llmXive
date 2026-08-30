"""
Quickstart validation script for the llmXive pipeline.
Validates that the full pipeline produces expected artifacts and logs.
"""
import os
import sys
import json
import time
import traceback
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config_dict, ensure_directories
from main import main as run_main_pipeline
from analysis.generate_correlation_results import main as run_correlation_pipeline
from analysis.robustness import main as run_robustness_pipeline
from reports.generate_report import main as run_report_generation
from reports.validate_report import main as run_report_validation
from reports.audit_associational_language import main as run_language_audit

def log_step(step_name: str, status: str, message: str = ""):
    """Log a validation step."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "step": step_name,
        "status": status,
        "message": message
    }
    print(f"[{timestamp}] {status}: {step_name} - {message}")
    return log_entry

def validate_file_exists(file_path: Path, required: bool = True) -> bool:
    """Check if a file exists."""
    exists = file_path.exists()
    status = "PASS" if exists else "FAIL"
    msg = f"File {file_path} {'exists' if exists else 'MISSING'}"
    log_step(f"Check: {file_path.name}", status, msg)
    if required and not exists:
        return False
    return exists

def run_validation():
    """Run the full quickstart validation sequence."""
    print("=" * 60)
    print("Starting Quickstart Validation Pipeline")
    print("=" * 60)

    start_time = time.time()
    validation_log = []
    all_passed = True

    # Ensure directories exist
    config = get_config_dict()
    ensure_directories()

    # 1. Run Main Pipeline (Structural & Dynamic Metrics)
    log_step("Pipeline: Main", "START", "Running main pipeline to generate structural and dynamic metrics")
    try:
        run_main_pipeline()
        log_step("Pipeline: Main", "PASS", "Main pipeline completed successfully")
    except Exception as e:
        log_step("Pipeline: Main", "FAIL", f"Main pipeline failed: {str(e)}")
        all_passed = False
        validation_log.append(log_step("Pipeline: Main", "FAIL", str(e)))

    # Validate Main Pipeline Outputs
    if all_passed:
        files_to_check = [
            PROJECT_ROOT / "data" / "processed" / "structural_metrics.csv",
            PROJECT_ROOT / "data" / "processed" / "dynamic_metrics.csv",
            PROJECT_ROOT / "data" / "logs" / "exclusion_log.json"
        ]
        for f in files_to_check:
            if not validate_file_exists(f):
                all_passed = False

    # 2. Run Correlation Pipeline
    if all_passed:
        log_step("Pipeline: Correlation", "START", "Running correlation analysis")
        try:
            run_correlation_pipeline()
            log_step("Pipeline: Correlation", "PASS", "Correlation analysis completed")
        except Exception as e:
            log_step("Pipeline: Correlation", "FAIL", f"Correlation analysis failed: {str(e)}")
            all_passed = False

        if all_passed:
            if not validate_file_exists(PROJECT_ROOT / "data" / "processed" / "correlation_results.csv"):
                all_passed = False

    # 3. Run Robustness Pipeline
    if all_passed:
        log_step("Pipeline: Robustness", "START", "Running robustness analysis")
        try:
            run_robustness_pipeline()
            log_step("Pipeline: Robustness", "PASS", "Robustness analysis completed")
        except Exception as e:
            log_step("Pipeline: Robustness", "FAIL", f"Robustness analysis failed: {str(e)}")
            all_passed = False

        if all_passed:
            if not validate_file_exists(PROJECT_ROOT / "data" / "processed" / "sensitivity_results.json"):
                all_passed = False

    # 4. Generate Final Report
    if all_passed:
        log_step("Pipeline: Report", "START", "Generating final report")
        try:
            run_report_generation()
            log_step("Pipeline: Report", "PASS", "Final report generated")
        except Exception as e:
            log_step("Pipeline: Report", "FAIL", f"Report generation failed: {str(e)}")
            all_passed = False

        if all_passed:
            if not validate_file_exists(PROJECT_ROOT / "data" / "reports" / "final_report.json"):
                all_passed = False

    # 5. Validate Report Schema
    if all_passed:
        log_step("Pipeline: Schema Validation", "START", "Validating report against schema")
        try:
            run_report_validation()
            log_step("Pipeline: Schema Validation", "PASS", "Report schema validation passed")
        except Exception as e:
            log_step("Pipeline: Schema Validation", "FAIL", f"Schema validation failed: {str(e)}")
            all_passed = False

    # 6. Audit Associational Language
    if all_passed:
        log_step("Pipeline: Language Audit", "START", "Auditing report for causality language")
        try:
            run_language_audit()
            log_step("Pipeline: Language Audit", "PASS", "Language audit completed")
        except Exception as e:
            log_step("Pipeline: Language Audit", "FAIL", f"Language audit failed: {str(e)}")
            all_passed = False

        if all_passed:
            if not validate_file_exists(PROJECT_ROOT / "data" / "reports" / "language_audit.json"):
                all_passed = False

    end_time = time.time()
    duration = end_time - start_time

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total Duration: {duration:.2f} seconds")
    print(f"Overall Status: {'PASS' if all_passed else 'FAIL'}")

    # Save validation log
    log_path = PROJECT_ROOT / "data" / "logs" / "quickstart_validation.json"
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": duration,
            "status": "PASS" if all_passed else "FAIL",
            "steps": validation_log
        }, f, indent=2)

    print(f"Validation log saved to: {log_path}")

    if not all_passed:
        print("\nERROR: Validation failed. Please check the logs above.")
        sys.exit(1)
    else:
        print("\nSUCCESS: Full pipeline reproducibility validated.")
        sys.exit(0)

if __name__ == "__main__":
    run_validation()
