"""
Task T032c: Validate Benchmark Result
Reads the benchmark results for N=5,000,000 and asserts the wall-clock time
is within the 1-hour limit. Raises BenchmarkFailure if the limit is exceeded
and logs the status to a dedicated JSON file.
"""
import os
import sys
import json
import logging
from datetime import timedelta

# Add project root to path if running as script
if __name__ == "__main__" and "code" not in sys.path[0]:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from exceptions import BenchmarkFailure
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BENCHMARK_FILE = "results/reports/benchmark_N5M.json"
STATUS_FILE = "results/reports/benchmark_status.json"
LIMIT_HOURS = 1
LIMIT_SECONDS = LIMIT_HOURS * 3600

def validate_benchmark_result():
    """
    Validates the benchmark result against the 1-hour limit.
    Raises BenchmarkFailure if the time exceeds the limit.
    """
    config = load_config()
    # The task specifically asks to validate N=5,000,000 benchmark
    # We assume the benchmark file exists as per T032b completion.
    
    if not os.path.exists(BENCHMARK_FILE):
        logger.error(f"Benchmark file not found: {BENCHMARK_FILE}. "
                     "Please ensure T032b has been run successfully.")
        # We raise a generic error or handle as failure, but the task
        # specifically mentions raising BenchmarkFailure on time violation.
        # If file missing, it's a prerequisite failure.
        raise FileNotFoundError(f"Benchmark result file {BENCHMARK_FILE} not found.")

    try:
        with open(BENCHMARK_FILE, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse benchmark JSON: {e}")
        raise

    elapsed_time = data.get('elapsed_time_seconds')
    
    if elapsed_time is None:
        logger.error("Missing 'elapsed_time_seconds' in benchmark result.")
        raise KeyError("Missing 'elapsed_time_seconds' in benchmark result.")

    logger.info(f"Benchmark elapsed time: {elapsed_time:.2f} seconds "
                f"({timedelta(seconds=int(elapsed_time))})")
    logger.info(f"Allowed limit: {LIMIT_SECONDS} seconds ({timedelta(seconds=LIMIT_SECONDS)})")

    if elapsed_time > LIMIT_SECONDS:
        logger.error(f"BENCHMARK FAILED: Elapsed time {elapsed_time:.2f}s exceeds limit {LIMIT_SECONDS}s.")
        
        # Raise the specific exception defined in T014
        raise BenchmarkFailure(elapsed_time=elapsed_time, limit=LIMIT_SECONDS)
    
    logger.info("BENCHMARK PASSED: Execution time is within the 1-hour limit.")
    
    # Log success status
    status_data = {
        "status": "passed",
        "elapsed_time_seconds": elapsed_time,
        "limit_seconds": LIMIT_SECONDS,
        "timestamp": str(timedelta(seconds=int(elapsed_time)))
    }
    
    with open(STATUS_FILE, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Success status logged to {STATUS_FILE}")
    return True

def main():
    try:
        validate_benchmark_result()
    except BenchmarkFailure as e:
        # Log the failure status as requested
        failure_status = {
            "status": "failed",
            "elapsed_time_seconds": e.elapsed_time,
            "limit_seconds": e.limit,
            "message": f"Time limit exceeded. Allowed: {e.limit}s, Got: {e.elapsed_time}s",
            "timestamp": None
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        
        with open(STATUS_FILE, 'w') as f:
            json.dump(failure_status, f, indent=2)
        
        logger.error(f"Benchmark validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
