"""
Directory Structure Verification Script for T153

Verifies that:
1. No legacy `data/results/` path exists
2. All results are stored under `data/processed/results/`
3. Directory structure follows plan.md specification

Usage:
    python verify_directory_structure.py

Returns exit code 0 if verification passes, 1 if issues found.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (parent of code/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Expected paths
LEGACY_RESULTS_PATH = PROJECT_ROOT / "data" / "results"
PROPER_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "results"
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"

# Nested raw data paths to check (for T154 compliance)
NESTED_RAW_PATHS = [
    PROJECT_ROOT / "data" / "raw" / "raw",
    PROJECT_ROOT / "data" / "raw" / "raw" / "raw",
]

def check_legacy_results_path() -> Tuple[bool, List[str]]:
    """Check if legacy data/results/ path exists."""
    issues = []
    if LEGACY_RESULTS_PATH.exists():
        issues.append(f"LEGACY PATH EXISTS: {LEGACY_RESULTS_PATH}")
        # List contents
        for item in LEGACY_RESULTS_PATH.rglob("*"):
            if item.is_file():
                issues.append(f"  - {item.relative_to(PROJECT_ROOT)}")
    return len(issues) == 0, issues

def check_proper_results_path() -> Tuple[bool, List[str]]:
    """Check if proper data/processed/results/ path exists and is used."""
    issues = []
    if not PROPER_RESULTS_PATH.exists():
        issues.append(f"PROPER RESULTS PATH MISSING: {PROPER_RESULTS_PATH}")
        issues.append("  - Create this directory for evaluation artifacts")
    else:
        logger.info(f"Proper results path exists: {PROPER_RESULTS_PATH}")
    return len(issues) == 0, issues

def check_nested_raw_paths() -> Tuple[bool, List[str]]:
    """Check for nested data/raw/raw/ structures (T154 compliance)."""
    issues = []
    for nested_path in NESTED_RAW_PATHS:
        if nested_path.exists():
            issues.append(f"NESTED RAW PATH EXISTS: {nested_path}")
            for item in nested_path.rglob("*"):
                if item.is_file():
                    issues.append(f"  - {item.relative_to(PROJECT_ROOT)}")
    return len(issues) == 0, issues

def check_data_directory_structure() -> Tuple[bool, List[str]]:
    """Verify overall data directory structure."""
    issues = []

    # Check data/raw exists
    if not RAW_DATA_PATH.exists():
        issues.append(f"RAW DATA PATH MISSING: {RAW_DATA_PATH}")
    else:
        logger.info(f"Raw data path exists: {RAW_DATA_PATH}")

    # Check data/processed exists
    if not PROCESSED_DATA_PATH.exists():
        issues.append(f"PROCESSED DATA PATH MISSING: {PROCESSED_DATA_PATH}")
    else:
        logger.info(f"Processed data path exists: {PROCESSED_DATA_PATH}")

    return len(issues) == 0, issues

def scan_for_results_files() -> Tuple[bool, List[str]]:
    """Scan for any .csv, .json, .png files in legacy vs proper locations."""
    issues = []
    results_extensions = {".csv", ".json", ".png", ".jpg", ".yaml", ".txt"}

    # Find files in legacy location
    legacy_files = []
    if LEGACY_RESULTS_PATH.exists():
        for ext in results_extensions:
            legacy_files.extend(LEGACY_RESULTS_PATH.rglob(f"*{ext}"))

    # Find files in proper location
    proper_files = []
    if PROPER_RESULTS_PATH.exists():
        for ext in results_extensions:
            proper_files.extend(PROPER_RESULTS_PATH.rglob(f"*{ext}"))

    if legacy_files:
        issues.append(f"FILES FOUND IN LEGACY LOCATION ({LEGACY_RESULTS_PATH}):")
        for f in legacy_files:
            issues.append(f"  - {f.relative_to(PROJECT_ROOT)}")

    logger.info(f"Files in proper location: {len(proper_files)}")
    return len(issues) == 0, issues

def generate_verification_report(
    results: List[Tuple[str, bool, List[str]]]
) -> str:
    """Generate a formatted verification report."""
    lines = []
    lines.append("=" * 60)
    lines.append("DIRECTORY STRUCTURE VERIFICATION REPORT (T153)")
    lines.append("=" * 60)
    lines.append(f"Project Root: {PROJECT_ROOT}")
    lines.append(f"Verification Time: {Path(__file__).parent.parent.parent.name}")
    lines.append("")

    all_passed = True
    for check_name, passed, issues in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        lines.append(f"[{status}] {check_name}")
        if issues:
            for issue in issues:
                lines.append(f"    {issue}")
        if not passed:
            all_passed = False
        lines.append("")

    lines.append("=" * 60)
    if all_passed:
        lines.append("OVERALL: ALL CHECKS PASSED")
    else:
        lines.append("OVERALL: VERIFICATION FAILED - ISSUES DETECTED")
    lines.append("=" * 60)

    return "\n".join(lines)

def main() -> int:
    """Main verification routine."""
    logger.info("Starting directory structure verification (T153)")

    # Run all checks
    checks = []

    # Check 1: No legacy data/results/ path
    passed, issues = check_legacy_results_path()
    checks.append(("Legacy data/results/ path removed", passed, issues))

    # Check 2: Proper data/processed/results/ exists
    passed, issues = check_proper_results_path()
    checks.append(("Proper data/processed/results/ exists", passed, issues))

    # Check 3: No nested data/raw/raw/ structures
    passed, issues = check_nested_raw_paths()
    checks.append(("No nested data/raw/raw/ structures", passed, issues))

    # Check 4: Overall data directory structure
    passed, issues = check_data_directory_structure()
    checks.append(("Data directory structure valid", passed, issues))

    # Check 5: Files in correct locations
    passed, issues = scan_for_results_files()
    checks.append(("Results files in correct locations", passed, issues))

    # Generate and print report
    report = generate_verification_report(checks)
    print(report)

    # Return appropriate exit code
    all_passed = all(passed for _, passed, _ in checks)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
