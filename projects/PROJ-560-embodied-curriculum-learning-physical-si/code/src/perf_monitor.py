"""
Performance monitoring utility for T039.
Runs the CLI with synthetic mode and records wall-clock time.
"""
import subprocess
import sys
import time
import json
import os
import logging
from pathlib import Path
from datetime import datetime

# Configure logging to avoid cluttering stdout during measurement
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = PROJECT_ROOT / "src" / "cli.py"
OUTPUT_DIR = PROJECT_ROOT.parent / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "perf_log.json"

def ensure_output_dir():
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_cli_synthetic(n_records: int) -> float:
    """
    Run the CLI in synthetic mode with N records.
    Returns the wall-clock duration in seconds.
    """
    cmd = [
        sys.executable,
        str(CLI_PATH),
        "--mode", "synthetic",
        "--n", str(n_records)
    ]

    logger.info(f"Running command: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout as per SC-001
        )
        
        duration = time.time() - start_time
        
        if result.returncode != 0:
            logger.error(f"CLI execution failed with code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            raise RuntimeError(f"CLI execution failed: {result.stderr}")
        
        logger.info(f"CLI execution completed successfully in {duration:.2f} seconds")
        return duration

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"CLI execution timed out after {duration:.2f} seconds")
        raise RuntimeError(f"CLI execution timed out after {duration:.2f} seconds")

def write_perf_log(n_records: int, duration: float):
    """Write the performance log to JSON."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "n_records": n_records,
        "duration_seconds": round(duration, 3)
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Performance log written to {OUTPUT_FILE}")
    return log_entry

def main():
    """Main entry point for performance verification."""
    n_records = 10000
    
    try:
        ensure_output_dir()
        duration = run_cli_synthetic(n_records)
        
        # Verify constraint SC-001: < 600s
        if duration >= 600:
            logger.warning(f"Performance constraint violated: {duration:.2f}s >= 600s")
        else:
            logger.info(f"Performance constraint satisfied: {duration:.2f}s < 600s")
        
        log_entry = write_perf_log(n_records, duration)
        print(f"Result: {log_entry}")
        
    except Exception as e:
        logger.error(f"Performance verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()