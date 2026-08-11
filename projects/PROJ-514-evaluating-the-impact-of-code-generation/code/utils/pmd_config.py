"""
PMD Configuration and Environment Check Module.

Verifies PMD and Java availability, and validates ruleset configuration.
"""

import os
import subprocess
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


def get_pmd_home() -> Optional[str]:
    """
    Retrieves the PMD_HOME environment variable.

    Returns:
        PMD_HOME string or None if not set.
    """
    return os.environ.get("PMD_HOME")


def get_pmd_executable() -> str:
    """
    Determines the PMD executable path or command.

    Returns:
        String command for PMD.
    """
    return os.environ.get("PMDEXT", "pmd")


def check_java_version() -> Tuple[bool, str]:
    """
    Checks if Java is installed and returns its version.

    Returns:
        Tuple of (is_available, version_string).
    """
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # java -version outputs to stderr
        version_info = result.stderr.strip()
        return True, version_info
    except FileNotFoundError:
        return False, "Java not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "Java version check timed out"


def check_pmd_version() -> Tuple[bool, str]:
    """
    Checks if PMD is installed and returns its version.

    Returns:
        Tuple of (is_available, version_string).
    """
    pmd_cmd = get_pmd_executable()
    try:
        result = subprocess.run(
            [pmd_cmd, "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, f"PMD returned error: {result.stderr}"
    except FileNotFoundError:
        return False, f"PMD executable '{pmd_cmd}' not found"
    except subprocess.TimeoutExpired:
        return False, "PMD version check timed out"


def check_pmd_availability() -> bool:
    """
    Verifies that both Java and PMD are available.

    Returns:
        True if both are available, False otherwise.
    """
    java_ok, java_msg = check_java_version()
    if not java_ok:
        logger.error(f"Java check failed: {java_msg}")
        return False

    pmd_ok, pmd_msg = check_pmd_version()
    if not pmd_ok:
        logger.error(f"PMD check failed: {pmd_msg}")
        return False

    logger.info(f"PMD and Java are available. Java: {java_msg[:50]}... PMD: {pmd_msg}")
    return True


def validate_pmd_rulesets(ruleset_paths: Optional[list] = None) -> Tuple[bool, List[str]]:
    """
    Validates that PMD ruleset files exist and are readable.

    Args:
        ruleset_paths: List of paths to ruleset files. If None, uses defaults.

    Returns:
        Tuple of (all_valid, list_of_errors).
    """
    if ruleset_paths is None:
        config = get_config()
        ruleset_dir = Path(config.get("project_root", ".")) / "code" / "02_static_analysis" / "rulesets"
        ruleset_paths = list(ruleset_dir.glob("*_ruleset.xml"))

    errors = []
    for path in ruleset_paths:
        if not path.exists():
            errors.append(f"Ruleset not found: {path}")
        elif not os.access(path, os.R_OK):
            errors.append(f"Ruleset not readable: {path}")
        else:
            # Basic XML validation could be added here
            pass

    return len(errors) == 0, errors


def main():
    """
    Main entry point to check PMD environment.
    """
    logger.info("Checking PMD environment...")
    
    if not check_pmd_availability():
        logger.error("PMD environment check failed. Please install Java and PMD.")
        sys.exit(1)
    
    valid, errors = validate_pmd_rulesets()
    if not valid:
        logger.error("Ruleset validation failed:")
        for err in errors:
            logger.error(f"  - {err}")
        sys.exit(1)
    
    logger.info("PMD environment is valid.")


if __name__ == "__main__":
    main()
