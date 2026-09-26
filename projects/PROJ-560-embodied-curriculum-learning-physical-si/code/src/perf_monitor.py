import subprocess
import sys
import time
import json
import os
import logging
from pathlib import Path

def ensure_output_dir():
    """Ensure the output directory exists."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def run_cli_synthetic(n_records=10000):
    """Run the CLI with synthetic mode and measure time."""
    cmd = [
        sys.executable,
        "code/src/cli.py",
        "--mode=synthetic",
        f"--n={n_records}",
        "--seed=42"
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    duration = end_time - start_time
    
    if result.returncode != 0:
        logging.error(f"CLI execution failed: {result.stderr}")
        raise RuntimeError(f"CLI execution failed with code {result.returncode}")
    
    return duration, result.returncode

def write_perf_log(duration, n_records, output_path=None):
    """Write performance log to JSON file."""
    if output_path is None:
        output_path = "data/processed/perf_log.json"
    
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_records": n_records,
        "duration_seconds": duration
    }
    
    with open(output_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    logging.info(f"Performance log written to {output_path}")
    return log_entry

def main():
    """Main entry point for performance verification."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting performance verification...")
    
    # Ensure output directory exists
    ensure_output_dir()
    
    # Run CLI with synthetic mode
    n_records = 10000
    try:
        duration, returncode = run_cli_synthetic(n_records)
        
        # Write performance log
        log_entry = write_perf_log(duration, n_records)
        
        # Check if within budget
        if duration > 600:
            logger.warning(f"Performance benchmark FAILED: {duration:.2f}s > 600s limit")
            return 1
        else:
            logger.info(f"Performance benchmark PASSED: {duration:.2f}s <= 600s limit")
            return 0
            
    except Exception as e:
        logger.error(f"Performance verification failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
