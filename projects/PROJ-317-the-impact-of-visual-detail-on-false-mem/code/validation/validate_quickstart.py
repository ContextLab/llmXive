"""
T045: Quickstart Validation Script.

This script validates the project's quickstart.md by:
1. Verifying that all documented CLI commands exist and run without error.
2. Verifying that all documented output artifacts are generated.
3. Verifying that the project structure matches expectations.

It exits with code 0 on success, 1 on failure.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from config import get_project_root, get_data_dir, get_stimuli_dir, get_stimuli_metadata_dir, get_processed_dir
from utils.logging import setup_logging, get_logger

# Configure logging
setup_logging(log_level="INFO")
logger = get_logger("quickstart_validation")

# Paths
PROJECT_ROOT = get_project_root()
QUICKSTART_PATH = PROJECT_ROOT / "quickstart.md"
DATA_DIR = get_data_dir()
STIMULI_DIR = get_stimuli_dir()
STIMULI_META_DIR = get_stimuli_metadata_dir()
PROCESSED_DIR = get_processed_dir()

def check_file_exists(path: Path, description: str) -> bool:
    if not path.exists():
        logger.error(f"Missing required artifact: {description} ({path})")
        return False
    logger.info(f"Found: {description} ({path})")
    return True

def check_directory_exists(path: Path, description: str) -> bool:
    if not path.exists():
        logger.error(f"Missing required directory: {description} ({path})")
        return False
    if not path.is_dir():
        logger.error(f"Path exists but is not a directory: {description} ({path})")
        return False
    logger.info(f"Found directory: {description} ({path})")
    return True

def run_command(cmd: List[str], description: str, expected_outputs: List[Path]) -> bool:
    """Run a CLI command and verify outputs."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per command
        )

        if result.returncode != 0:
            logger.error(f"Command failed with code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            return False

        logger.info(f"Command '{description}' completed successfully.")

        # Verify expected outputs
        all_found = True
        for output_path in expected_outputs:
            if not output_path.exists():
                logger.error(f"Expected output missing: {output_path}")
                all_found = False
            else:
                logger.info(f"Output verified: {output_path}")

        return all_found

    except subprocess.TimeoutExpired:
        logger.error(f"Command '{description}' timed out")
        return False
    except Exception as e:
        logger.error(f"Error running command '{description}': {e}")
        return False

def validate_project_structure() -> bool:
    """Validate that the project structure is correct."""
    logger.info("Validating project structure...")
    checks = [
        (check_directory_exists, PROJECT_ROOT / "data", "Data root"),
        (check_directory_exists, DATA_DIR, "Data directory"),
        (check_directory_exists, STIMULI_DIR, "Stimuli directory"),
        (check_directory_exists, STIMULI_META_DIR, "Stimuli metadata directory"),
        (check_directory_exists, PROCESSED_DIR, "Processed data directory"),
        (check_file_exists, PROJECT_ROOT / "requirements.txt", "Requirements file"),
        (check_file_exists, PROJECT_ROOT / "README.md", "README file"),
    ]

    all_pass = True
    for check_func, path, desc in checks:
        if not check_func(path, desc):
            all_pass = False

    return all_pass

def validate_quickstart_commands() -> bool:
    """Validate that quickstart.md commands work."""
    logger.info("Validating quickstart commands...")

    if not QUICKSTART_PATH.exists():
        logger.error(f"quickstart.md not found at {QUICKSTART_PATH}")
        return False

    # Read quickstart to understand expected commands
    # For now, we validate the core CLI commands that should exist
    # based on the implementation plan

    commands_to_test = [
        {
            "name": "Generate Mock Data",
            "cmd": [sys.executable, "-m", "code.data.loader", "--mode", "mock", "--count", "2"],
            "outputs": [
                STIMULI_DIR / "mock_image_0.png",
                STIMULI_DIR / "mock_image_1.png",
                STIMULI_META_DIR / "mock_image_0.yaml",
                STIMULI_META_DIR / "mock_image_1.yaml",
            ]
        },
        {
            "name": "Run Stimuli Manipulation",
            "cmd": [sys.executable, "-m", "code.cli", "manipulate", "--input", str(STIMULI_DIR), "--output", str(STIMULI_DIR / "manipulated")],
            "outputs": [
                STIMULI_DIR / "manipulated",
            ]
        },
        {
            "name": "Run Simulated Session",
            "cmd": [sys.executable, "-m", "code.cli", "simulate", "--count", "1", "--stimuli-dir", str(STIMULI_DIR)],
            "outputs": [
                DATA_DIR / "responses",
            ]
        },
        {
            "name": "Run Analysis",
            "cmd": [sys.executable, "-m", "code.cli", "analyze"],
            "outputs": [
                PROCESSED_DIR / "anova_results.json",
                PROJECT_ROOT / "figures" / "false_memory_rates.png",
            ]
        },
    ]

    all_pass = True
    for test in commands_to_test:
        # Ensure output directories exist before running
        for out in test["outputs"]:
            if out.parent and not out.parent.exists():
                out.parent.mkdir(parents=True, exist_ok=True)

        if not run_command(test["cmd"], test["name"], test["outputs"]):
            all_pass = False

    return all_pass

def main() -> int:
    """Main validation entry point."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation (T045)")
    logger.info("=" * 60)

    success = True

    # Step 1: Validate project structure
    if not validate_project_structure():
        success = False

    # Step 2: Validate quickstart commands
    if not validate_quickstart_commands():
        success = False

    logger.info("=" * 60)
    if success:
        logger.info("VALIDATION PASSED: All quickstart requirements satisfied.")
        return 0
    else:
        logger.error("VALIDATION FAILED: Some requirements not met.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
