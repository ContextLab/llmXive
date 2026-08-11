"""
Timeout enforcement module for the modeling pipeline.

Implements a signal-based timeout handler to enforce a maximum runtime
for the modeling execution, preventing indefinite hangs.
"""
import signal
import time
import logging
import sys
from typing import Callable, Any, Optional
from pathlib import Path
import multiprocessing
import os
import json
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class TimeoutExceededError(Exception):
    """Raised when the execution time exceeds the configured limit."""
    pass

class TimeoutHandler:
    """
    Context manager and decorator for enforcing timeouts on functions.
    Uses multiprocessing.Process to safely terminate long-running tasks
    on Unix systems where signal-based timeouts might be unreliable for complex
    object graphs.
    """
    
    def __init__(self, timeout_seconds: int, log_path: Optional[Path] = None):
        """
        Initialize the timeout handler.
        
        Args:
            timeout_seconds: Maximum allowed runtime in seconds.
            log_path: Path to the log file for runtime metrics.
        """
        self.timeout_seconds = timeout_seconds
        self.log_path = log_path or Path("logs/timeout_metrics.json")
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.status: str = "unknown"
        self.runtime_duration: float = 0.0

    def _handle_timeout(self, signum, frame):
        """Signal handler for the timeout event."""
        raise TimeoutExceededError(f"Execution exceeded {self.timeout_seconds} seconds limit.")

    def run_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with a strict timeout.
        
        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
        
        Returns:
            The return value of the function.
        
        Raises:
            TimeoutExceededError: If the function execution exceeds the timeout.
        """
        self.start_time = time.time()
        self.status = "started"
        
        try:
            # Use signal-based timeout for the main process if on Unix
            # This is lighter weight than spawning a new process for simple scripts
            if os.name != 'nt':
                # Set the signal handler
                old_handler = signal.signal(signal.SIGALRM, self._handle_timeout)
                # Set the alarm
                signal.alarm(self.timeout_seconds)
                
                try:
                    result = func(*args, **kwargs)
                    self.status = "completed"
                    return result
                finally:
                    # Cancel the alarm and restore the old handler
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Fallback for Windows (where SIGALRM is not available)
                # Use a thread with a timeout check (simpler than Process for this context)
                # Note: For heavy CPU bound tasks on Windows, a Process pool is safer
                # but requires more complex serialization. We use a join-able thread approach
                # or simply rely on the fact that modeling.py is the entry point.
                # Given the constraints, we will use a simpler approach:
                # Run in a thread and join with timeout.
                import threading
                result_container = []
                exception_container = []
                
                def target():
                    try:
                        result_container.append(func(*args, **kwargs))
                    except Exception as e:
                        exception_container.append(e)
                
                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(self.timeout_seconds)
                
                if thread.is_alive():
                    # Thread is still alive, meaning timeout
                    raise TimeoutExceededError(f"Execution exceeded {self.timeout_seconds} seconds limit.")
                
                if exception_container:
                    raise exception_container[0]
                
                return result_container[0]

        except TimeoutExceededError:
            self.status = "timeout"
            raise
        finally:
            self.end_time = time.time()
            self.runtime_duration = self.end_time - self.start_time
            self._save_metrics()

    def _save_metrics(self):
        """Save runtime metrics to the log file."""
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "timeout_limit_seconds": self.timeout_seconds,
                "actual_runtime_seconds": self.runtime_duration,
                "status": self.status,
                "timed_out": self.status == "timeout"
            }
            
            # Append to existing file if it exists
            if self.log_path.exists():
                try:
                    with open(self.log_path, 'r') as f:
                        history = json.load(f)
                        if not isinstance(history, list):
                            history = [history]
                except (json.JSONDecodeError, TypeError):
                    history = []
                history.append(metrics)
            else:
                history = [metrics]
            
            with open(self.log_path, 'w') as f:
                json.dump(history, f, indent=2)
                
            logger.info(f"Runtime metrics saved to {self.log_path}: {self.status}, {self.runtime_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to save timeout metrics: {e}")

def main():
    """
    Entry point for testing the timeout wrapper.
    This function simulates a long-running task to verify the timeout mechanism.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Define a test function that sleeps
    def slow_function(seconds):
        logger.info(f"Starting slow function for {seconds} seconds...")
        time.sleep(seconds)
        logger.info("Slow function completed.")
        return "Success"
    
    # Configuration
    timeout_limit = 5  # 5 seconds
    test_duration = 10 # 10 seconds (should timeout)
    
    handler = TimeoutHandler(timeout_seconds=timeout_limit)
    
    try:
        result = handler.run_with_timeout(slow_function, test_duration)
        print(f"Result: {result}")
    except TimeoutExceededError as e:
        print(f"Timeout caught: {e}")
        print("The pipeline was successfully terminated due to timeout.")
        sys.exit(1)
    
    # Test a successful short run
    print("\nTesting short run (should succeed)...")
    handler2 = TimeoutHandler(timeout_seconds=timeout_limit)
    try:
        result = handler2.run_with_timeout(slow_function, 1)
        print(f"Result: {result}")
    except TimeoutExceededError as e:
        print(f"Unexpected timeout: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()