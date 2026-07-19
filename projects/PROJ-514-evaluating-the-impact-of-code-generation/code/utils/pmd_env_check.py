"""
Utility script to verify PMD and JRE availability in the current environment.
This script is used by the CI pipeline and local development setup to ensure
the static analysis tools are correctly installed.
"""
import subprocess
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional

# Configure logging to match project style
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_java_version() -> Tuple[bool, Optional[str]]:
    """Check if Java is installed and returns its version."""
    try:
        result = subprocess.run(
            ['java', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # java -version writes to stderr
        version_info = result.stderr.strip()
        if "openjdk" in version_info or "java" in version_info:
            logger.info(f"Java detected: {version_info.split(chr(10))[0]}")
            return True, version_info
        else:
            logger.warning("Java detected but version string unexpected.")
            return False, version_info
    except FileNotFoundError:
        logger.error("Java (java command) not found in PATH.")
        return False, None
    except subprocess.TimeoutExpired:
        logger.error("Java version check timed out.")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error checking Java: {e}")
        return False, None

def check_pmd_version() -> Tuple[bool, Optional[str]]:
    """Check if PMD is installed and returns its version."""
    try:
        result = subprocess.run(
            ['pmd', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version_info = result.stdout.strip()
            logger.info(f"PMD detected: {version_info}")
            return True, version_info
        else:
            logger.warning(f"PMD returned non-zero exit code: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except FileNotFoundError:
        logger.error("PMD (pmd command) not found in PATH.")
        return False, None
    except subprocess.TimeoutExpired:
        logger.error("PMD version check timed out.")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error checking PMD: {e}")
        return False, None

def validate_pmd_rulesets() -> bool:
    """
    Validate that standard PMD rulesets are available.
    This is a basic check to ensure the PMD installation is functional.
    """
    try:
        # Try to list rulesets or run a dummy check
        result = subprocess.run(
            ['pmd', 'check', '-R', 'rulesets/java/quickstart.xml', '-d', '/tmp'],
            capture_output=True,
            text=True,
            timeout=30
        )
        # A "no files found" or similar error is expected if /tmp has no Java,
        # but "ruleset not found" or "command not found" indicates a bad install.
        if "ruleset" in result.stderr.lower() and "not found" in result.stderr.lower():
            logger.error("PMD ruleset 'rulesets/java/quickstart.xml' not found.")
            return False
        # If we get here, PMD understood the command structure
        return True
    except Exception as e:
        logger.error(f"Error validating PMD rulesets: {e}")
        return False

def main():
    """Main entry point for environment check."""
    logger.info("Starting PMD and JRE environment check...")
    
    java_ok, java_ver = check_java_version()
    pmd_ok, pmd_ver = check_pmd_version()
    
    if java_ok and pmd_ok:
        logger.info("Environment check PASSED. PMD and JRE are available.")
        # Optional: validate rulesets
        if validate_pmd_rulesets():
            logger.info("PMD rulesets validation PASSED.")
            sys.exit(0)
        else:
            logger.error("PMD rulesets validation FAILED.")
            sys.exit(1)
    else:
        logger.error("Environment check FAILED.")
        if not java_ok:
            logger.error("Missing: Java Runtime Environment (JRE)")
        if not pmd_ok:
            logger.error("Missing: PMD CLI tool")
        sys.exit(1)

if __name__ == "__main__":
    main()