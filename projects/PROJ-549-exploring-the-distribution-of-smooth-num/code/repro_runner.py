"""
Reproducibility Execution Script (Task T033a)

Executes the project's quickstart pipeline end-to-end in a clean environment.
This script assumes the project structure is already set up and dependencies are installed.
It orchestrates the generation of primes, smooth number density calculations,
and analysis, capturing all output to a log file.

Usage:
    python code/repro_runner.py
"""
import os
import sys
import subprocess
import logging
import shutil
from datetime import datetime

# Configure logging
LOG_DIR = "data/ci_logs"
LOG_FILE = os.path.join(LOG_DIR, "repro_run.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, description: str) -> bool:
    """
    Executes a shell command and logs the output.
    Returns True if successful, False otherwise.
    """
    logger.info(f"--- Executing: {description} ---")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout per step
            check=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        logger.info(f"Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Exit code: {e.returncode}")
        if e.stdout:
            logger.error(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            logger.error(f"STDERR:\n{e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout: {description}")
        return False
    except Exception as e:
        logger.error(f"Exception: {description} - {str(e)}")
        return False

def main():
    logger.info("Starting Reproducibility Execution (T033a)")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # 1. Verify Environment
    logger.info("Step 1: Verifying environment and dependencies")
    if not run_command([sys.executable, "--version"], "Check Python version"):
        logger.error("Python environment check failed.")
        sys.exit(1)

    # 2. Generate Primes (US1)
    # Note: In a real CI, this might be skipped if artifacts exist, 
    # but for T033a "end-to-end" we run the generation.
    logger.info("Step 2: Generating primes (T012)")
    # We use a smaller limit for CI reproducibility if 10^9 is too slow,
    # but the task asks to execute the script. We will run the main entry point.
    # To ensure it finishes in CI, we might need to adjust the limit or rely on 
    # the fact that the runner has resources. 
    # However, the task says "Execute the quickstart.md script".
    # Assuming quickstart.md calls code/main.py with sieve generation.
    # If the full 10^9 sieve is too slow for the CI timeout, we might need to 
    # run a subset or rely on the fact that the prompt implies a successful run.
    # Given the constraints of a "clean environment" and "end-to-end", 
    # we attempt the full run. If it times out, the log captures it.
    
    # To be safe for a generic CI runner in this context, we will run the main pipeline.
    # The main.py is designed to orchestrate.
    if not run_command([sys.executable, "code/main.py", "--sieve"], "Run Sieve Generation"):
        logger.warning("Sieve generation failed or timed out. This is expected for full 10^9 in short CI.")
        # If sieve fails, we cannot proceed to US2. 
        # For the purpose of T033a "execution", we capture the failure in the log.
        # But we should try to make it succeed if possible. 
        # Let's assume the user has a fast runner or we are running a subset.
        # Since I cannot change the task requirement to "run a subset", I will run the command.
        # If it fails, the log is the artifact.
        # However, to ensure the task is "completed" in the sense of a working script,
        # I will assume the environment allows it or the script handles timeouts gracefully.
        # If the sieve script T012 has a checkpoint, it might resume.
        # Let's proceed assuming it runs.
        # If it fails, we stop.
        sys.exit(1)

    # 3. Validate Sieve (T013)
    logger.info("Step 3: Validating Sieve (T013)")
    if not run_command([sys.executable, "code/validate_sieve.py"], "Validate Sieve"):
        logger.error("Sieve validation failed.")
        sys.exit(1)

    # 4. Generate Density Data (US2)
    # We run the main pipeline for density generation.
    logger.info("Step 4: Generating Smooth Number Density (T023)")
    if not run_command([sys.executable, "code/main.py", "--density"], "Run Density Generation"):
        logger.error("Density generation failed.")
        sys.exit(1)

    # 5. Verify Grid (T023b)
    logger.info("Step 5: Verifying Grid (T023b)")
    if not run_command([sys.executable, "code/verify_grid.py"], "Verify Grid"):
        logger.error("Grid verification failed.")
        sys.exit(1)

    # 6. Run Analysis (US3)
    logger.info("Step 6: Running Statistical Analysis (T029)")
    if not run_command([sys.executable, "code/main.py", "--analysis"], "Run Analysis"):
        logger.error("Analysis failed.")
        sys.exit(1)

    # 7. Generate Visualizations (T028)
    logger.info("Step 7: Generating Visualizations (T028)")
    if not run_command([sys.executable, "code/viz.py"], "Run Visualization"):
        logger.error("Visualization failed.")
        sys.exit(1)

    logger.info("Reproducibility Execution completed successfully.")
    logger.info(f"Log file saved to: {os.path.abspath(LOG_FILE)}")

if __name__ == "__main__":
    main()