import os
import sys
import logging
import subprocess
from typing import List
from utils import setup_logging

logger = logging.getLogger(__name__)

def run_script(script_name: str, args: List[str] = None) -> bool:
    """Run a Python script from the code directory."""
    script_path = os.path.join("code", script_name)
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed with return code {e.returncode}")
        return False

def main():
    setup_logging("INFO")
    logger.info("Running t012_run_baseline_analysis.py...")
    success = run_script("t012_run_baseline_analysis.py")
    if not success:
        logger.error("Pipeline failed at t012_run_baseline_analysis.py")
        sys.exit(1)
    logger.info("Pipeline step T012 completed successfully.")

if __name__ == "__main__":
    main()
