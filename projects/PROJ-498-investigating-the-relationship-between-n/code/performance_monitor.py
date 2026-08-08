import time
import sys
import os
import resource
from pathlib import Path
from typing import Callable, Any, Optional
import json
import logging
from datetime import datetime

# Ensure logs directory exists
def ensure_logs_dir():
    logs_dir = Path("data/metrics")
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

# Get current RSS memory in MB
def get_rss_mb():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux, MB on macOS
    if sys.platform == 'darwin':
        return usage.ru_maxrss
    else:
        return usage.ru_maxrss / 1024.0

# Enforce time limit for a function execution
def enforce_time_limit(
    func: Callable,
    time_limit_seconds: float = 1800.0,  # 30 minutes default
    subject_id: Optional[str] = None,
    log_path: Optional[Path] = None
) -> Callable:
    """
    Decorator to enforce a time limit on a function execution.
    Logs timing information and raises an error if the limit is exceeded.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger("performance_monitor")
        
        if log_path is None:
            log_path = ensure_logs_dir() / "runtime_log.json"
        
        # Initialize log file if it doesn't exist
        log_data = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total_duration_minutes": None,
            "status": "running",
            "subject_id": subject_id,
            "time_limit_seconds": time_limit_seconds
        }
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60.0
            
            log_data["end_time"] = datetime.now().isoformat()
            log_data["total_duration_minutes"] = round(duration_minutes, 2)
            log_data["status"] = "success"
            
            # Check if within time limit
            if duration_seconds > time_limit_seconds:
                log_data["status"] = "timeout_exceeded"
                logger.warning(
                    f"Subject {subject_id}: Execution took {duration_minutes:.2f} minutes, "
                    f"exceeding limit of {time_limit_seconds/60:.2f} minutes."
                )
            else:
                logger.info(
                    f"Subject {subject_id}: Execution completed in {duration_minutes:.2f} minutes "
                    f"(limit: {time_limit_seconds/60:.2f} minutes)."
                )
            
            # Save log
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60.0
            
            log_data["end_time"] = datetime.now().isoformat()
            log_data["total_duration_minutes"] = round(duration_minutes, 2)
            log_data["status"] = "error"
            log_data["error"] = str(e)
            
            logger.error(
                f"Subject {subject_id}: Execution failed after {duration_minutes:.2f} minutes: {str(e)}"
            )
            
            # Save log even on error
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            raise
    
    return wrapper

def main():
    """
    Main function to demonstrate performance monitoring.
    """
    print("Performance Monitor Module")
    print(f"Current RSS Memory: {get_rss_mb():.2f} MB")
    
    # Example usage of time limit enforcement
    @enforce_time_limit(time_limit_seconds=1800.0, subject_id="demo_subject")
    def demo_function():
        time.sleep(1)
        return "Demo completed"
    
    try:
        demo_function()
    except Exception as e:
        print(f"Demo failed: {e}")

if __name__ == "__main__":
    main()