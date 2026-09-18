"""
BatchExecutor and TimeoutGuard for experiment execution.
Handles parallel batching and timeout enforcement.
"""
import os
import sys
import logging
import time
import signal
import json
from typing import Dict, Any, Callable, Optional
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

def TimeoutGuard(seconds: int):
    """
    Decorator that enforces a timeout on a function.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function timed out after {seconds} seconds")

            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)

            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel the alarm
                signal.signal(signal.SIGALRM, old_handler)
                return result
            except TimeoutError:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                raise
        return wrapper
    return decorator

class BatchExecutor:
    """
    Executor for batch processing of instances.
    Enforces timeouts and tracks durations.
    """
    def __init__(self, timeout_per_instance: float = 60.0):
        self.timeout_per_instance = timeout_per_instance

    @TimeoutGuard(60)
    def _run_single(self, instance_id: str, prompt: str, context: str, model_runner) -> Dict[str, Any]:
        """Run a single instance with timeout."""
        start = time.time()
        try:
            response, duration, success = model_runner.generate(prompt, context)
            return {
                "success": success,
                "log": response,
                "duration": duration
            }
        except Exception as e:
            return {
                "success": False,
                "log": str(e),
                "duration": time.time() - start
            }

    def submit(self, instance_id: str, prompt: str, context: str, model_runner) -> Dict[str, Any]:
        """
        Submit an instance for execution.
        """
        return self._run_single(instance_id, prompt, context, model_runner)

def main():
    """Main entry point for testing the executor."""
    print("BatchExecutor initialized")

if __name__ == "__main__":
    main()