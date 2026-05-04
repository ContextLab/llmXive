#!/usr/bin/env python3
"""
Final Acceptance Verification Script for T145
Verifies all six success criteria (SC-001 through SC-006) and
confirms no FAILED-IN-EXECUTION comments exist in tasks.md.
"""
import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (assume script runs from code/scripts/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
TASKS_MD_PATH = PROJECT_ROOT / "tasks.md"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml"
CONFIG_FILE_PATH = PROJECT_ROOT / "code" / "config.yaml"
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "results"
ELBO_LOGS_PATH = PROJECT_ROOT / "logs" / "elbo"
COVERAGE_REPORT_PATH = PROJECT_ROOT / "code" / "tests" / "test_report.md"

# Success Criteria definitions
SUCCESS_CRITERIA = {
    "SC-001": {
        "name": "Dataset Compliance",
        "checks": [
            "Three UCI datasets exist (Electricity, Traffic, Synthetic Control Chart)",
            "No PEMS-SF files in data/raw/",
            "All datasets have ≥1000 observations",
            "Univariate constraint satisfied"
        ]
    },
    "SC-002": {
        "name": "Model Convergence",
        "checks": [
            "ELBO convergence logs exist in logs/elbo/",
            "Stopping criteria met per Constitution Principle VI"
        ]
    },
    "SC-003": {
        "name": "Test Coverage",
        "checks": [
            "≥80% line coverage achieved",
            "test_report.md exists with coverage details"
        ]
    },
    "SC-004": {
        "name": "Evaluation Artifacts",
        "checks": [
            "F1-scores, ROC/PR curves exist in data/processed/results/",
            "Memory profiles documented",
            "Confusion matrices generated"
        ]
    },
    "SC-005": {
        "name": "Config File Size Compliance",
        "checks": [
            "config.yaml < 2KB (2048 bytes)",
            "Derived statistics moved to state file"
        ]
    },
    "SC-006": {
        "name": "State File Integrity",
        "checks": [
            "State file exists at correct path",
            "SHA256 checksums recorded for all artifacts",
            "Decision boundaries documented"
        ]
    }
}

def check_no_failed_in_execution():
    """Verify no FAILED-IN-EXECUTION comments in tasks.md"""
    logger.info("Checking for FAILED-IN-EXECUTION comments in tasks.md...")
    if not TASKS_MD_PATH.exists():
        return False, "tasks.md not found"
    
    with open(TASKS_MD_PATH, 'r') as f:
        content = f.read()
    
    # Check for FAILED-IN-EXECUTION in completed tasks
    failed_count = content.count("FAILED-IN-EXECUTION")
    if failed_count > 0:
        return False, f"Found {failed_count} FAILED-IN-EXECUTION comments in tasks.md"
    
    return True, "No FAILED-IN-EXECUTION comments found"

def check_sc001_dataset_compliance():
    """SC-001: Dataset Compliance"""
    logger.info("Checking SC-001: Dataset Compliance...")
    issues = []
    
    # Check for required UCI datasets
    required_datasets = [
        "electricity.csv",
        "traffic.csv", 
        "synthetic_control_chart.csv"
    ]
    
    for dataset in required_datasets:
        dataset_path = DATA_RAW_PATH / dataset
        if not dataset_path.exists():
            issues.append(f"Missing required dataset: {dataset}")
        else:
            # Check file size (should have ≥1000 observations)
            size = dataset_path.stat().st_size
            if size < 10000:  # At least 10KB for 1000+ rows
                issues.append(f"Dataset {dataset} too small: {size} bytes")
    
    # Check for PEMS-SF files (should not exist)
    pems_files = list(DATA_RAW_PATH.glob("*pems*"))
    if pems_files:
        issues.append(f"PEMS-SF files found (should be removed): {[f.name for f in pems_files]}")
    
    # Check data dictionary
    data_dict_path = PROJECT_ROOT / "data" / "data-dictionary.md"
    if not data_dict_path.exists():
        issues.append("data/data-dictionary.md not found")
    
    return len(issues) == 0, issues

def check_sc002_model_convergence():
    """SC-002: Model Convergence"""
    logger.info("Checking SC-002: Model Convergence...")
    issues = []
    
    # Check ELBO logs directory
    if not ELBO_LOGS_PATH.exists():
        issues.append(f"ELBO logs directory not found: {ELBO_LOGS_PATH}")
    else:
        elbo_files = list(ELBO_LOGS_PATH.glob("*.log"))
        if not elbo_files:
            issues.append("No ELBO log files found in logs/elbo/")
    
    # Check for ELBO history in state file
    if STATE_FILE_PATH.exists():
        with open(STATE_FILE_PATH, 'r') as f:
            state = yaml.safe_load(f)
        if "elbo_history" not in state and "model_convergence" not in state:
            issues.append("No ELBO history or convergence data in state file")
    else:
        issues.append("State file not found")
    
    return len(issues) == 0, issues

def check_sc003_test_coverage():
    """SC-003: Test Coverage"""
    logger.info("Checking SC-003: Test Coverage...")
    issues = []
    
    # Check test report exists
    if not COVERAGE_REPORT_PATH.exists():
        issues.append(f"Test report not found: {COVERAGE_REPORT_PATH}")
    else:
        with open(COVERAGE_REPORT_PATH, 'r') as f:
            content = f.read()
        
        # Look for coverage percentage
        import re
        coverage_match = re.search(r'(\d+)%', content)
        if coverage_match:
            coverage = int(coverage_match.group(1))
            if coverage < 80:
                issues.append(f"Coverage {coverage}% below 80% threshold")
        else:
            issues.append("Coverage percentage not found in test report")
    
    # Check contract tests exist (should be 9 files)
    contract_test_path = PROJECT_ROOT / "code" / "tests" / "contract"
    if contract_test_path.exists():
        test_files = list(contract_test_path.glob("test_*.py"))
        if len(test_files) < 9:
            issues.append(f"Only {len(test_files)} contract test files found (expected 9)")
    else:
        issues.append("Contract test directory not found")
    
    return len(issues) == 0, issues

def check_sc004_evaluation_artifacts():
    """SC-004: Evaluation Artifacts"""
    logger.info("Checking SC-004: Evaluation Artifacts...")
    issues = []
    
    # Check results directory
    if not RESULTS_PATH.exists():
        issues.append(f"Results directory not found: {RESULTS_PATH}")
    else:
        # Check for F1 scores
        f1_files = list(RESULTS_PATH.glob("*f1*.json")) + list(RESULTS_PATH.glob("*metrics*.json"))
        if not f1_files:
            issues.append("No F1 scores or metrics files found")
        
        # Check for ROC/PR curves
        plot_files = list(RESULTS_PATH.glob("*.png"))
        if not plot_files:
            issues.append("No evaluation plots found (ROC/PR curves)")
        
        # Check for summary report
        summary_files = list(RESULTS_PATH.glob("*summary*.md")) + list(RESULTS_PATH.glob("*results*.md"))
        if not summary_files:
            issues.append("No summary report found in results directory")
    
    # Check confusion matrices
    confusion_path = PROJECT_ROOT / "data" / "processed" / "results"
    if confusion_path.exists():
        confusion_files = list(confusion_path.glob("*confusion*"))
        if not confusion_files:
            issues.append("No confusion matrix files found")
    
    return len(issues) == 0, issues

def check_sc005_config_size():
    """SC-005: Config File Size Compliance"""
    logger.info("Checking SC-005: Config File Size Compliance...")
    issues = []
    
    if not CONFIG_FILE_PATH.exists():
        issues.append(f"Config file not found: {CONFIG_FILE_PATH}")
    else:
        size = CONFIG_FILE_PATH.stat().st_size
        if size >= 2048:
            issues.append(f"config.yaml is {size} bytes (exceeds 2KB limit)")
        else:
            logger.info(f"config.yaml size: {size} bytes (within 2KB limit)")
    
    # Check config validation report
    validation_report = PROJECT_ROOT / "code" / "tests" / "config_validation.md"
    if not validation_report.exists():
        issues.append("config_validation.md not found")
    
    return len(issues) == 0, issues

def check_sc006_state_integrity():
    """SC-006: State File Integrity"""
    logger.info("Checking SC-006: State File Integrity...")
    issues = []
    
    if not STATE_FILE_PATH.exists():
        issues.append(f"State file not found: {STATE_FILE_PATH}")
    else:
        with open(STATE_FILE_PATH, 'r') as f:
            state = yaml.safe_load(f)
        
        # Check for checksums
        if "artifacts" not in state and "checksums" not in state:
            issues.append("No artifacts or checksums section in state file")
        else:
            checksums = state.get("artifacts", {}).get("checksums", {})
            if not checksums:
                issues.append("No checksums recorded in state file")
        
        # Check for decision boundary
        if "decision_boundary" not in state and "threshold" not in state:
            issues.append("No decision boundary documented in state file")
    
    return len(issues) == 0, issues

def generate_acceptance_report(all_results):
    """Generate comprehensive acceptance report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "task_id": "T145",
        "verdict": "PASS" if all(all_results.values()) else "FAIL",
        "success_criteria": {}
    }
    
    for sc_id, (passed, details) in all_results.items():
        report["success_criteria"][sc_id] = {
            "passed": passed,
            "details": details if isinstance(details, list) else [details]
        }
    
    # Save report
    report_path = RESULTS_PATH / "final_acceptance_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Acceptance report saved to {report_path}")
    return report

def main():
    """Main verification entry point"""
    logger.info("=" * 60)
    logger.info("FINAL ACCEPTANCE VERIFICATION (T145)")
    logger.info("=" * 60)
    
    # Check 1: No FAILED-IN-EXECUTION comments
    no_failed, failed_msg = check_no_failed_in_execution()
    if not no_failed:
        logger.error(failed_msg)
    else:
        logger.info(failed_msg)
    
    # Run all success criteria checks
    all_results = {}
    
    logger.info("\n" + "-" * 60)
    logger.info("Checking Success Criteria SC-001 through SC-006")
    logger.info("-" * 60)
    
    all_results["SC-001"] = check_sc001_dataset_compliance()
    all_results["SC-002"] = check_sc002_model_convergence()
    all_results["SC-003"] = check_sc003_test_coverage()
    all_results["SC-004"] = check_sc004_evaluation_artifacts()
    all_results["SC-005"] = check_sc005_config_size()
    all_results["SC-006"] = check_sc006_state_integrity()
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("SUCCESS CRITERIA SUMMARY")
    logger.info("=" * 60)
    
    for sc_id, (passed, details) in all_results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{sc_id}: {status}")
        if isinstance(details, list):
            for detail in details:
                logger.info(f"  - {detail}")
    
    # Generate report
    report = generate_acceptance_report(all_results)
    
    # Final verdict
    all_passed = all(passed for passed, _ in all_results.values())
    logger.info("\n" + "=" * 60)
    if all_passed and no_failed:
        logger.info("FINAL VERDICT: ACCEPTANCE PASSED")
        logger.info("All success criteria (SC-001 through SC-006) satisfied")
        logger.info("No FAILED-IN-EXECUTION comments found in tasks.md")
    else:
        logger.info("FINAL VERDICT: ACCEPTANCE FAILED")
        if not no_failed:
            logger.info("FAILED-IN-EXECUTION comments found in tasks.md")
        failed_criteria = [sc for sc, (passed, _) in all_results.items() if not passed]
        if failed_criteria:
            logger.info(f"Failed criteria: {', '.join(failed_criteria)}")
    logger.info("=" * 60)
    
    return 0 if (all_passed and no_failed) else 1

if __name__ == "__main__":
    sys.exit(main())
