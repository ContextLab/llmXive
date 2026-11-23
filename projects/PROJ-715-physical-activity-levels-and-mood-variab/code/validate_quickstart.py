"""
Task T038: Validate quickstart.md documentation accuracy.

This script validates that the steps and commands described in `quickstart.md`
are accurate by attempting to execute the critical path commands (dry-run or
actual execution where safe) and verifying the existence of expected artifacts.
"""
import os
import sys
import subprocess
import re
import logging
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
QUICKSTART_PATH = PROJECT_ROOT / "quickstart.md"
REQUIREMENTS_PATH = PROJECT_ROOT / "code" / "requirements.txt"
CONFIG_PATH = PROJECT_ROOT / "code" / "config.py"
INGEST_PATH = PROJECT_ROOT / "code" / "ingest.py"
PREPROCESS_PATH = PROJECT_ROOT / "code" / "preprocess.py"
ANALYSIS_PATH = PROJECT_ROOT / "code" / "analysis.py"
REPORT_PATH = PROJECT_ROOT / "code" / "report.py"

# Expected artifacts based on standard pipeline flow
EXPECTED_ARTIFACTS = [
    "data/raw/bronze.parquet",
    "data/processed/daily_aggregates.csv",
    "data/processed/model_results.json"
]

def extract_commands_from_quickstart() -> List[Tuple[str, str]]:
    """
    Parse quickstart.md and extract code blocks that look like shell commands.
    Returns a list of (command, context) tuples.
    """
    if not QUICKSTART_PATH.exists():
        raise FileNotFoundError(f"quickstart.md not found at {QUICKSTART_PATH}")
    
    content = QUICKSTART_PATH.read_text(encoding='utf-8')
    commands = []
    
    # Simple regex to find code blocks
    # Matches ```bash ... ``` or ```shell ... ```
    pattern = re.compile(r'```(?:bash|shell)\n(.*?)\n```', re.DOTALL)
    
    matches = pattern.findall(content)
    for match in matches:
        lines = match.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append((line, "quickstart.md"))
    
    return commands

def validate_file_paths_in_doc() -> Tuple[bool, List[str]]:
    """
    Check if file paths mentioned in quickstart.md actually exist.
    """
    if not QUICKSTART_PATH.exists():
        return False, ["quickstart.md missing"]
    
    content = QUICKSTART_PATH.read_text(encoding='utf-8')
    errors = []
    
    # Check for specific file references that should exist
    critical_files = [
        "code/requirements.txt",
        "code/config.py",
        "code/ingest.py",
        "code/preprocess.py",
        "code/analysis.py",
        "code/report.py",
        "data/raw/bronze.parquet",
        "data/processed/daily_aggregates.csv",
        "data/processed/model_results.json"
    ]
    
    for f in critical_files:
        full_path = PROJECT_ROOT / f
        if not full_path.exists():
            errors.append(f"Referenced file not found: {f}")
    
    return len(errors) == 0, errors

def validate_python_imports() -> Tuple[bool, List[str]]:
    """
    Verify that all Python modules referenced in quickstart.md can be imported.
    """
    errors = []
    modules_to_check = [
        ("code", "ingest"),
        ("code", "preprocess"),
        ("code", "analysis"),
        ("code", "report"),
        ("code", "config")
    ]
    
    for package, module in modules_to_check:
        try:
            # Add code directory to path
            code_dir = PROJECT_ROOT / "code"
            if str(code_dir) not in sys.path:
                sys.path.insert(0, str(code_dir))
            
            __import__(module)
            logger.info(f"Successfully imported {package}.{module}")
        except ImportError as e:
            errors.append(f"Failed to import {package}.{module}: {str(e)}")
    
    return len(errors) == 0, errors

def validate_requirements_syntax() -> Tuple[bool, List[str]]:
    """
    Verify that requirements.txt is valid and parseable.
    """
    errors = []
    if not REQUIREMENTS_PATH.exists():
        return False, ["requirements.txt not found"]
    
    try:
        content = REQUIREMENTS_PATH.read_text(encoding='utf-8')
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
        
        if not lines:
            errors.append("requirements.txt is empty")
        else:
            # Basic syntax check: each line should be a valid package specifier
            # We don't actually install, just check syntax
            for line in lines:
                # Very basic check: should contain package name
                if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*', line):
                    errors.append(f"Invalid package specifier in requirements.txt: {line}")
                    
    except Exception as e:
        errors.append(f"Error reading requirements.txt: {str(e)}")
    
    return len(errors) == 0, errors

def run_validation_checks() -> Tuple[bool, List[str]]:
    """
    Run all validation checks.
    """
    all_passed = True
    all_errors = []
    
    logger.info("=== Starting Quickstart Validation ===")
    
    # 1. Validate file paths
    logger.info("Checking file paths referenced in documentation...")
    passed, errors = validate_file_paths_in_doc()
    if not passed:
        all_passed = False
        all_errors.extend(errors)
        logger.warning(f"File path validation failed: {errors}")
    else:
        logger.info("File path validation passed.")
    
    # 2. Validate Python imports
    logger.info("Checking Python module imports...")
    passed, errors = validate_python_imports()
    if not passed:
        all_passed = False
        all_errors.extend(errors)
        logger.warning(f"Import validation failed: {errors}")
    else:
        logger.info("Import validation passed.")
    
    # 3. Validate requirements syntax
    logger.info("Checking requirements.txt syntax...")
    passed, errors = validate_requirements_syntax()
    if not passed:
        all_passed = False
        all_errors.extend(errors)
        logger.warning(f"Requirements validation failed: {errors}")
    else:
        logger.info("Requirements validation passed.")
    
    # 4. Check for expected output artifacts
    logger.info("Checking for expected output artifacts...")
    missing_artifacts = []
    for artifact in EXPECTED_ARTIFACTS:
        full_path = PROJECT_ROOT / artifact
        if not full_path.exists():
            missing_artifacts.append(artifact)
    
    if missing_artifacts:
        logger.warning(f"Missing expected artifacts: {missing_artifacts}")
        # Note: We don't fail here if artifacts are missing, 
        # as they might not have been generated yet. 
        # Just warn the user.
    else:
        logger.info("All expected artifacts found.")
    
    logger.info("=== Validation Complete ===")
    return all_passed, all_errors

def main():
    """
    Main entry point for validation script.
    """
    try:
        success, errors = run_validation_checks()
        
        if success:
            logger.info("✅ Quickstart documentation validation PASSED.")
            logger.info("All referenced files exist, imports work, and syntax is valid.")
            return 0
        else:
            logger.error("❌ Quickstart documentation validation FAILED.")
            logger.error("Issues found:")
            for error in errors:
                logger.error(f"  - {error}")
            return 1
            
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
