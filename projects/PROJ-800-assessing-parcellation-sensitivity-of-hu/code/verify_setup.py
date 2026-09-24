"""
Verification script for T001.
Executes ls -R on the project root and saves the output to state/setup_verification.log.
"""
import os
import subprocess
import sys
from pathlib import Path
from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)

PROJECT_ROOT = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")
STATE_DIR = Path("state")
VERIFICATION_LOG = STATE_DIR / "setup_verification.log"

def main() -> None:
    """
    Runs the verification command and logs the output.
    """
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    if not PROJECT_ROOT.exists():
        msg = f"Project root does not exist: {PROJECT_ROOT}"
        logger.error(msg)
        raise ConfigurationError(msg)

    logger.info(f"Running verification command: ls -R {PROJECT_ROOT}")
    
    try:
        result = subprocess.run(
            ["ls", "-R", str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
        
        # Write to log file
        with open(VERIFICATION_LOG, "w", encoding="utf-8") as f:
            f.write(output)
        
        logger.info(f"Verification complete. Output saved to {VERIFICATION_LOG}")
        print(output) # Print to stdout for immediate feedback

    except subprocess.CalledProcessError as e:
        msg = f"Verification command failed: {e.stderr}"
        logger.error(msg)
        raise ConfigurationError(msg) from e

if __name__ == "__main__":
    main()
