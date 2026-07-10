"""
Orchestrator module for the network topology heat transport pipeline.

Implements global runtime monitoring to enforce the 6-hour temporal limit (SC-002).
Tracks total wall-clock time across ensemble execution and logs warnings if
the limit is exceeded, flagging sample size as potentially insufficient.
"""
import logging
import time
from pathlib import Path
from typing import Optional

# Configure logger for the module
logger = logging.getLogger(__name__)

# Temporal limit in seconds (6 hours)
WALL_CLOCK_LIMIT_SECONDS = 6 * 60 * 60

# File to store the start time of the pipeline execution
START_TIME_FILE = Path("state/pipeline_start_time.txt")
# File to store the final runtime status
RUNTIME_STATUS_FILE = Path("state/pipeline_runtime_status.json")


def get_elapsed_time() -> float:
    """
    Calculate the elapsed wall-clock time since the pipeline started.
    
    Reads the start time from the state file. If the file doesn't exist,
    assumes the pipeline just started (returns 0.0).
    
    Returns:
        float: Elapsed time in seconds.
    """
    if not START_TIME_FILE.exists():
        return 0.0
    
    try:
        with open(START_TIME_FILE, 'r') as f:
            start_timestamp = float(f.read().strip())
        current_timestamp = time.time()
        return current_timestamp - start_timestamp
    except (ValueError, IOError) as e:
        logger.warning(f"Failed to read start time from {START_TIME_FILE}: {e}. Assuming 0 elapsed time.")
        return 0.0


def initialize_pipeline_timing() -> None:
    """
    Initialize the pipeline timing by recording the current timestamp.
    
    This should be called once at the very beginning of the pipeline execution.
    """
    START_TIME_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(START_TIME_FILE, 'w') as f:
        f.write(str(time.time()))
    logger.info("Pipeline timing initialized.")


def check_runtime_limit() -> dict:
    """
    Check if the total runtime has exceeded the predefined temporal limit.
    
    If the limit is exceeded, logs a warning and returns a status indicating
    the sample size might be insufficient. The pipeline is NOT aborted.
    
    Returns:
        dict: A dictionary containing:
            - 'exceeded': bool, True if limit exceeded
            - 'elapsed_seconds': float, total elapsed time
            - 'limit_seconds': float, the configured limit
            - 'warning_flag': bool, True if a warning should be logged
            - 'message': str, descriptive message
    """
    elapsed = get_elapsed_time()
    exceeded = elapsed > WALL_CLOCK_LIMIT_SECONDS
    
    status = {
        "exceeded": exceeded,
        "elapsed_seconds": elapsed,
        "limit_seconds": WALL_CLOCK_LIMIT_SECONDS,
        "warning_flag": False,
        "message": "Runtime within limits."
    }
    
    if exceeded:
        status["warning_flag"] = True
        status["message"] = (
            f"WARNING: Total runtime ({elapsed:.2f}s) exceeded the limit "
            f"({WALL_CLOCK_LIMIT_SECONDS}s). Sample size may be insufficient for "
            f"the defined temporal budget. Pipeline continues but results may be "
            f"incomplete."
        )
        logger.warning(status["message"])
    else:
        logger.debug(f"Runtime check passed. Elapsed: {elapsed:.2f}s / Limit: {WALL_CLOCK_LIMIT_SECONDS}s")
        
    return status


def record_final_status(status: dict) -> None:
    """
    Record the final runtime status to a state file for CI/CD verification.
    
    Args:
        status: The dictionary returned by check_runtime_limit().
    """
    import json
    RUNTIME_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RUNTIME_STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)
    logger.info(f"Final runtime status recorded to {RUNTIME_STATUS_FILE}")


def main() -> None:
    """
    Main entry point for the orchestrator runtime monitor.
    
    This function simulates a check at the end of a pipeline run.
    In a real execution, this would be called by the main pipeline script.
    """
    # In a real scenario, initialize_pipeline_timing() would be called at the start.
    # For this standalone script, we just check the current state.
    # If the start time file doesn't exist, it assumes 0 elapsed time.
    
    logger.info("Running orchestrator runtime check...")
    status = check_runtime_limit()
    record_final_status(status)
    
    print(f"Runtime Status: {status['message']}")
    if status['exceeded']:
        print(f"  Elapsed: {status['elapsed_seconds']:.2f}s")
        print(f"  Limit: {status['limit_seconds']}s")


if __name__ == "__main__":
    # Ensure logging is configured if run directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()