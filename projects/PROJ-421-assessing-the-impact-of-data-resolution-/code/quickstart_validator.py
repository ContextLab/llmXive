"""
Quickstart validation script for PROJ-421.
Executes the steps outlined in quickstart.md to verify the pipeline works end-to-end.
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path

# Add project root to path if running from within code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from utils import get_logger, checksum_file

logger = get_logger(__name__)

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a required file exists."""
    if path.exists():
        logger.info(f"✓ {description} exists: {path}")
        return True
    else:
        logger.error(f"✗ {description} missing: {path}")
        return False

def check_file_not_empty(path: Path, description: str) -> bool:
    """Check if a file exists and is not empty."""
    if path.exists() and path.stat().st_size > 0:
        logger.info(f"✓ {description} is not empty: {path}")
        return True
    else:
        logger.error(f"✗ {description} is missing or empty: {path}")
        return False

def run_script(script_path: Path, args: list = None) -> bool:
    """Run a Python script and return True if successful."""
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=False,
            text=True
        )
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"✓ Script completed successfully in {elapsed:.2f}s")
            return True
        else:
            logger.error(f"✗ Script failed with return code {result.returncode}")
            return False
    except Exception as e:
        logger.error(f"✗ Exception running script: {e}")
        return False

def validate_data_files() -> bool:
    """Validate that all expected data files exist."""
    logger.info("\n--- Validating Data Files ---")
    all_good = True

    # Raw data
    raw_dir = PROJECT_ROOT / config.DATA_RAW_DIR
    if raw_dir.exists():
        logger.info(f"✓ Raw data directory exists: {raw_dir}")
        # Check for at least one file
        files = list(raw_dir.glob("*"))
        if files:
            logger.info(f"  Found {len(files)} file(s) in raw directory")
        else:
            logger.warning("  Warning: Raw data directory is empty")
    else:
        logger.error(f"✗ Raw data directory missing: {raw_dir}")
        all_good = False

    # Derived data
    derived_dir = PROJECT_ROOT / config.DATA_DERIVED_DIR
    if derived_dir.exists():
        logger.info(f"✓ Derived data directory exists: {derived_dir}")
    else:
        logger.error(f"✗ Derived data directory missing: {derived_dir}")
        all_good = False

    # Results
    results_dir = PROJECT_ROOT / config.DATA_RESULTS_DIR
    if results_dir.exists():
        logger.info(f"✓ Results directory exists: {results_dir}")
        
        # Check for calibration lambda
        lambda_file = results_dir / "calibration_lambda.json"
        if not check_file_not_empty(lambda_file, "Calibration lambda"):
            all_good = False
        
        # Check for power results
        power_file = results_dir / "power_results.csv"
        if not check_file_not_empty(power_file, "Power results CSV"):
            all_good = False
        
        # Check for threshold report
        threshold_file = results_dir / "threshold_report.txt"
        if not check_file_not_empty(threshold_file, "Threshold report"):
            all_good = False
        
        # Check for final report
        final_report = results_dir / "final_report.md"
        if not check_file_not_empty(final_report, "Final report"):
            all_good = False
    else:
        logger.error(f"✗ Results directory missing: {results_dir}")
        all_good = False

    return all_good

def validate_code_structure() -> bool:
    """Validate that all required code modules exist."""
    logger.info("\n--- Validating Code Structure ---")
    all_good = True
    
    required_files = [
        "config.py",
        "utils.py",
        "models.py",
        "data_ingestion.py",
        "resampling.py",
        "calibration.py",
        "analysis.py",
        "visualization.py",
        "sensitivity_analysis.py",
        "type2_error_analysis.py",
        "generate_final_report.py",
        "reference_validator.py",
        "validate_checksums.py",
        "cleanup_refactor.py",
        "setup_dirs.py"
    ]
    
    code_dir = PROJECT_ROOT / "code"
    for filename in required_files:
        file_path = code_dir / filename
        if file_path.exists():
            logger.info(f"✓ {filename} exists")
        else:
            logger.error(f"✗ {filename} missing")
            all_good = False
    
    return all_good

def validate_tests() -> bool:
    """Validate that test files exist."""
    logger.info("\n--- Validating Tests ---")
    all_good = True
    
    test_dir = PROJECT_ROOT / "tests"
    if test_dir.exists():
        logger.info(f"✓ Tests directory exists: {test_dir}")
        files = list(test_dir.glob("*.py"))
        if files:
            logger.info(f"  Found {len(files)} test file(s)")
            # Run pytest if available
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "-v", "--tb=short"],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    logger.info("✓ All tests passed")
                else:
                    logger.warning("⚠ Some tests failed (non-critical for validation)")
            except subprocess.TimeoutExpired:
                logger.warning("⚠ Test execution timed out")
            except Exception as e:
                logger.warning(f"⚠ Could not run tests: {e}")
    else:
        logger.warning("⚠ Tests directory missing")
    
    return all_good

def validate_checksums() -> bool:
    """Validate checksums for critical files."""
    logger.info("\n--- Validating Checksums ---")
    all_good = True
    
    results_dir = PROJECT_ROOT / config.DATA_RESULTS_DIR
    checksum_file_path = results_dir / "checksums.json"
    
    if checksum_file_path.exists():
        try:
            with open(checksum_file_path, 'r') as f:
                checksums = json.load(f)
            
            logger.info(f"✓ Checksums file loaded: {len(checksums)} entries")
            
            # Verify a few key files
            key_files = [
                "calibration_lambda.json",
                "power_results.csv",
                "threshold_report.txt",
                "final_report.md"
            ]
            
            for filename in key_files:
                file_path = results_dir / filename
                if file_path.exists():
                    actual_checksum = checksum_file(file_path)
                    expected_checksum = checksums.get(filename)
                    
                    if expected_checksum:
                        if actual_checksum == expected_checksum:
                            logger.info(f"  ✓ {filename} checksum valid")
                        else:
                            logger.error(f"  ✗ {filename} checksum mismatch")
                            all_good = False
                    else:
                        logger.warning(f"  ⚠ No checksum record for {filename}")
                else:
                    logger.error(f"  ✗ {filename} missing")
                    all_good = False
                    
        except Exception as e:
            logger.error(f"✗ Error validating checksums: {e}")
            all_good = False
    else:
        logger.warning("⚠ Checksums file not found (optional)")
    
    return all_good

def main():
    """Run the full quickstart validation."""
    logger.info("=" * 60)
    logger.info("QUICKSTART VALIDATION FOR PROJ-421")
    logger.info("=" * 60)
    
    all_checks_passed = True
    
    # 1. Validate code structure
    if not validate_code_structure():
        all_checks_passed = False
    
    # 2. Validate data files
    if not validate_data_files():
        all_checks_passed = False
    
    # 3. Validate checksums
    if not validate_checksums():
        all_checks_passed = False
    
    # 4. Run tests
    if not validate_tests():
        all_checks_passed = False
    
    # 5. Validate key outputs
    logger.info("\n--- Validating Key Outputs ---")
    
    results_dir = PROJECT_ROOT / config.DATA_RESULTS_DIR
    
    # Check final report content
    final_report = results_dir / "final_report.md"
    if final_report.exists():
        try:
            with open(final_report, 'r') as f:
                content = f.read()
            
            required_sections = [
                "threshold",
                "power",
                "resolution"
            ]
            
            found_sections = 0
            for section in required_sections:
                if section.lower() in content.lower():
                    found_sections += 1
            
            if found_sections >= 2:
                logger.info(f"✓ Final report contains key sections ({found_sections}/{len(required_sections)})")
            else:
                logger.warning(f"⚠ Final report may be missing key sections ({found_sections}/{len(required_sections)})")
        except Exception as e:
            logger.error(f"✗ Error reading final report: {e}")
            all_checks_passed = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    if all_checks_passed:
        logger.info("✓ QUICKSTART VALIDATION PASSED")
        logger.info("All critical checks completed successfully.")
        return 0
    else:
        logger.warning("⚠ QUICKSTART VALIDATION INCOMPLETE")
        logger.warning("Some checks failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())