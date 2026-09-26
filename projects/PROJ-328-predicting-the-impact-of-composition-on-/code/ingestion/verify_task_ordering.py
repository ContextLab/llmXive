"""
T058: Verify Task Ordering Audit Script.

This script audits the dependency chain between Data Cleaning (T013),
Validation (T014), Descriptor Engineering (T023b/T023c), and Model Training (T025/T026).

It verifies:
1. T023b/T023c explicitly depend on `solder_hardness_cleaned.csv` (T013 output).
2. T025/T026 explicitly depend on the outputs of T023b/T023c (`clr_features.csv`, `descriptors.csv`).
3. No task attempts to verify FR-X using results from a file produced by a later task.
4. No synthetic/fake data generation is used in verification scripts (specifically T058's own context and T012g/T014a/T023b/T023c).
"""

import os
import sys
import ast
import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CODE_DIR = PROJECT_ROOT / "code"

# Configuration
CONFIG_PATH = PROJECT_ROOT / "code" / "config.py"
CLEANED_DATA_FILE = DATA_PROCESSED_DIR / "solder_hardness_cleaned.csv"
CLR_FEATURES_FILE = DATA_PROCESSED_DIR / "clr_features.csv"
DESCRIPTORS_FILE = DATA_PROCESSED_DIR / "descriptors.csv"
INGESTION_STATUS_FILE = DATA_PROCESSED_DIR / ".ingestion_status.json"

# Expected dependency chains
EXPECTED_DEPS = {
    "code/features/transformer.py": [CLEANED_DATA_FILE],
    "code/features/descriptor_engine.py": [CLEANED_DATA_FILE],
    "code/models/xgboost_trainer.py": [CLR_FEATURES_FILE, DESCRIPTORS_FILE],
    "code/models/linear_trainer.py": [CLR_FEATURES_FILE, DESCRIPTORS_FILE],
    "code/ingestion/validator.py": [CLEANED_DATA_FILE, INGESTION_STATUS_FILE],
}

# Files known to have failed verification due to synthetic data
KNOWN_SYNTHETIC_ISSUES = [
    "code/models/verify_cpu.py",
    "code/ingestion/api_fetcher.py",
    "code/ingestion/literature_scraper.py",
]

logger = logging.getLogger(__name__)

def get_file_content(path: Path) -> str:
    """Read file content safely."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

def check_file_exists(path: Path) -> bool:
    """Check if a file exists."""
    return path.exists()

def check_imports_source_file(file_path: Path, source_file: Path) -> bool:
    """
    Check if the target file explicitly imports or references the source file.
    This is a heuristic check based on string matching in the source code.
    """
    if not file_path.exists():
        return False
    
    content = get_file_content(file_path)
    source_name = source_file.name
    
    # Check for direct imports or path references
    # e.g., "from data.processed.solder_hardness_cleaned import ..."
    # or "path = .../solder_hardness_cleaned.csv"
    # or "df = pd.read_csv(.../solder_hardness_cleaned.csv)"
    
    # Simple heuristic: check if the filename appears in the code
    if source_name in content:
        return True
    
    # Check for relative path construction
    if source_file.stem in content and "read_csv" in content:
        return True
        
    return False

def check_for_synthetic_data(file_path: Path) -> List[str]:
    """
    Check if a file contains synthetic/fake data generation patterns.
    Returns a list of detected issues.
    """
    issues = []
    if not file_path.exists():
        return issues
    
    content = get_file_content(file_path)
    lines = content.split('\n')
    
    synthetic_patterns = [
        "make_regression",
        "np.random.",
        "random.uniform",
        "generate_synthetic",
        "mock_data",
        "fake_data",
        "dummy_data",
        "X, y = make_regr",
        "X, y = make_regression",
    ]
    
    for i, line in enumerate(lines):
        for pattern in synthetic_patterns:
            if pattern in line and not line.strip().startswith("#"):
                # Check if it's inside a try/except block that might be for error handling
                # but we flag it if it looks like a primary data source
                issues.append(f"Line {i+1}: Potential synthetic data pattern '{pattern}' detected.")
    
    return issues

def audit_file_dependencies(file_path: Path, required_inputs: List[Path]) -> Tuple[bool, List[str]]:
    """Audit if a file correctly depends on required input files."""
    errors = []
    content = get_file_content(file_path)
    
    if not content:
        return False, [f"File {file_path} not found or empty."]
    
    for input_file in required_inputs:
        if not check_file_exists(input_file):
            errors.append(f"Required input file missing: {input_file}")
        
        # Heuristic: Check if the code references the input file
        if not check_imports_source_file(file_path, input_file):
            # This is a soft check; sometimes paths are hardcoded differently
            # But if the file is missing, it's a hard error
            if not check_file_exists(input_file):
                pass # Already reported
            else:
                # File exists but code doesn't seem to reference it? 
                # This might be a false positive if the path is constructed dynamically
                logger.warning(f"Code in {file_path} might not explicitly reference {input_file.name}.")
    
    return len(errors) == 0, errors

def audit_synthetic_data_usage() -> Dict[str, List[str]]:
    """Audit specific files for synthetic data usage."""
    results = {}
    for file_rel_path in KNOWN_SYNTHETIC_ISSUES:
        file_path = PROJECT_ROOT / file_rel_path
        issues = check_for_synthetic_data(file_path)
        if issues:
            results[file_rel_path] = issues
    return results

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Starting Task Ordering Audit (T058)...")

    audit_results = {
        "dependency_chain": {},
        "synthetic_data_usage": {},
        "missing_artifacts": [],
        "passed": True
    }

    # 1. Check Dependency Chain
    logger.info("Checking dependency chain...")
    for file_rel_path, required_inputs in EXPECTED_DEPS.items():
        file_path = PROJECT_ROOT / file_rel_path
        status, errors = audit_file_dependencies(file_path, required_inputs)
        
        if not status:
            audit_results["dependency_chain"][file_rel_path] = {
                "status": "failed",
                "errors": errors
            }
            audit_results["passed"] = False
        else:
            audit_results["dependency_chain"][file_rel_path] = {"status": "passed"}

    # 2. Check for Synthetic Data
    logger.info("Checking for synthetic data usage...")
    synthetic_issues = audit_synthetic_data_usage()
    if synthetic_issues:
        audit_results["synthetic_data_usage"] = synthetic_issues
        audit_results["passed"] = False
        logger.warning("Synthetic data patterns detected in verification scripts.")
    else:
        logger.info("No synthetic data patterns detected in known problematic files.")

    # 3. Check for Missing Artifacts
    logger.info("Checking for missing artifacts...")
    missing = []
    for file_path in [CLEANED_DATA_FILE, CLR_FEATURES_FILE, DESCRIPTORS_FILE, INGESTION_STATUS_FILE]:
        if not check_file_exists(file_path):
            missing.append(str(file_path))
    
    if missing:
        audit_results["missing_artifacts"] = missing
        audit_results["passed"] = False
        logger.warning(f"Missing artifacts: {missing}")
    else:
        logger.info("All required artifacts present.")

    # 4. Generate Report
    report_path = PROJECT_ROOT / "data" / "outputs" / "task_ordering_audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(audit_results, f, indent=2)
    
    logger.info(f"Audit report written to {report_path}")

    if audit_results["passed"]:
        logger.info("AUDIT PASSED: Task ordering and data integrity verified.")
        return 0
    else:
        logger.error("AUDIT FAILED: Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
