import subprocess
import sys
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_safety_check() -> bool:
    """
    Runs 'safety check' on requirements.txt.
    Returns True if no critical vulnerabilities are found, False otherwise.
    """
    logger.info("Running safety check on requirements.txt...")
    requirements_path = Path("requirements.txt")
    
    if not requirements_path.exists():
        logger.error("requirements.txt not found in project root.")
        return False

    try:
        # Run safety check with critical error code
        # safety returns 1 if vulnerabilities are found, 0 if clean
        # We specifically look for critical vulnerabilities
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "safety"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.warning(f"Failed to upgrade safety package: {result.stderr}")
            # Attempt to run even if upgrade failed, assuming it might be installed
        
        cmd = [sys.executable, "-m", "safety", "check", "-r", str(requirements_path)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        logger.info("Safety Check Output:")
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(f"Safety Check Errors: {result.stderr}")
        
        # Safety returns 1 if vulnerabilities found, 0 if clean
        if result.returncode == 0:
            logger.info("No vulnerabilities found.")
            return True
        else:
            # Check if the output mentions critical vulnerabilities
            if "critical" in result.stdout.lower():
                logger.error("Critical vulnerabilities found!")
            else:
                logger.warning("Vulnerabilities found (non-critical).")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error during safety check: {e}")
        return False
    except FileNotFoundError:
        logger.error("Safety package not found. Please install it via: pip install safety")
        return False

def update_vulnerable_packages() -> bool:
    """
    Attempts to update vulnerable packages to their latest secure versions.
    Note: This is a best-effort operation and may require manual intervention
    if dependencies conflict.
    """
    logger.info("Attempting to update vulnerable packages...")
    
    try:
        # First, try to identify specific vulnerabilities and update
        # Safety can output a report with fix commands
        cmd = [sys.executable, "-m", "safety", "check", "-r", "requirements.txt", "--output", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            logger.info("No vulnerabilities to update.")
            return True

        # If vulnerabilities found, attempt to upgrade packages
        # We run pip install --upgrade on packages listed in requirements.txt
        # In a real scenario, we would parse the JSON output to target specific versions
        logger.info("Upgrading all packages to latest versions to resolve vulnerabilities...")
        upgrade_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"]
        upgrade_result = subprocess.run(
            upgrade_cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if upgrade_result.returncode == 0:
            logger.info("Packages upgraded successfully.")
            # Re-run safety check to verify
            return run_safety_check()
        else:
            logger.error(f"Package upgrade failed: {upgrade_result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error during package update: {e}")
        return False

def main():
    """
    Main entry point for the security audit script.
    Runs safety check and updates packages if vulnerabilities are found.
    """
    logger.info("Starting Security Audit (Task T041)...")
    
    success = run_safety_check()
    
    if not success:
        logger.warning("Vulnerabilities detected. Attempting to update packages...")
        success = update_vulnerable_packages()
    
    if success:
        logger.info("Security Audit PASSED: No critical vulnerabilities found.")
        sys.exit(0)
    else:
        logger.error("Security Audit FAILED: Critical vulnerabilities remain.")
        sys.exit(1)

if __name__ == "__main__":
    main()
