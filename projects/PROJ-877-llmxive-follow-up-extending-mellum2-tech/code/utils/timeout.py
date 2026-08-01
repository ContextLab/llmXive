import signal
import time
import threading
from functools import wraps
from typing import Callable, Any, Optional
from utils.logging import TimeoutError, get_logger

logger = get_logger("llmXive.utils.timeout")

class timeout_handler:
    """
    Context manager to enforce a fixed per-chunk duration constraint (FR-003).
    Uses SIGALRM on Unix-like systems for immediate interruption.
    Falls back to a threading-based approach on Windows or when SIGALRM is unavailable.
    
    Must raise TimeoutError on breach.
    """
    def __init__(self, seconds: int):
        if seconds <= 0:
            raise ValueError("Timeout duration must be positive")
        self.seconds = seconds
        self.old_handler: Optional[Any] = None
        self._stop_event = threading.Event()
        self._timer_thread: Optional[threading.Thread] = None

    def __enter__(self):
        if hasattr(signal, 'SIGALRM'):
            # Unix-like systems: use signal alarm
            self.old_handler = signal.signal(signal.SIGALRM, self._signal_timeout_handler)
            signal.alarm(self.seconds)
        else:
            # Windows or non-SIGALRM environment: use threading fallback
            logger.warning("SIGALRM not available. Using thread-based timeout fallback.")
            self._stop_event.clear()
            self._timer_thread = threading.Thread(
                target=self._thread_timeout_target,
                daemon=True
            )
            self._timer_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_handler is not None:
            # Cancel alarm and restore old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, self.old_handler)
            self.old_handler = None
        
        if self._timer_thread is not None:
            # Signal the thread to stop and wait briefly
            self._stop_event.set()
            self._timer_thread.join(timeout=0.1)
            self._timer_thread = None
        
        # Do not suppress exceptions
        return False

    def _signal_timeout_handler(self, signum: int, frame: Any) -> None:
        """Handler for SIGALRM that raises TimeoutError."""
        raise TimeoutError(f"Operation timed out after {self.seconds} seconds")

    def _thread_timeout_target(self) -> None:
        """Target for the fallback timeout thread."""
        # Wait for the specified duration or until stop event
        if not self._stop_event.wait(timeout=self.seconds):
            # Timeout occurred
            raise TimeoutError(f"Operation timed out after {self.seconds} seconds")

def enforce_timeout(seconds: int) -> Callable[[Callable], Callable]:
    """
    Decorator to enforce a fixed per-chunk duration constraint (FR-003).
    Raises TimeoutError if the decorated function exceeds the time limit.
    """
    if seconds <= 0:
        raise ValueError("Timeout duration must be positive")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, lambda s, f: exec('raise TimeoutError("Timeout")'))
                signal.alarm(seconds)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Fallback for Windows: run in a thread with timeout
                logger.warning(f"SIGALRM not available. Using thread-based timeout for {func.__name__}.")
                
                result_container = {'result': None, 'error': None}
                
                def target() -> None:
                    try:
                        result_container['result'] = func(*args, **kwargs)
                    except Exception as e:
                        result_container['error'] = e
                
                thread = threading.Thread(target=target, daemon=True)
                thread.start()
                thread.join(timeout=seconds)
                
                if thread.is_alive():
                    # Thread is still running, meaning timeout occurred
                    # Note: We cannot forcefully kill the thread in Python, 
                    # but we raise the exception to stop execution of the caller.
                    raise TimeoutError(f"Operation timed out after {seconds} seconds")
                
                if result_container['error'] is not None:
                    raise result_container['error']
                
                return result_container['result']
        return wrapper
    return decorator

def main() -> None:
    """
    Test the timeout functionality with real execution.
    Verifies that TimeoutError is raised on breach.
    """
    logger.info("Starting timeout functionality tests...")
    
    # Test 1: Context manager with timeout breach
    logger.info("Test 1: Context manager with timeout breach (2s limit, 5s sleep)")
    try:
        with timeout_handler(2):
            time.sleep(5)
            logger.error("FAIL: Should have raised TimeoutError")
    except TimeoutError as e:
        logger.info(f"PASS: Expected timeout caught: {e}")
    
    # Test 2: Context manager with successful completion
    logger.info("Test 2: Context manager with successful completion (5s limit, 1s sleep)")
    try:
        with timeout_handler(5):
            time.sleep(1)
            logger.info("PASS: Function completed within timeout")
    except TimeoutError as e:
        logger.error(f"FAIL: Unexpected timeout: {e}")
    
    # Test 3: Decorator with timeout breach
    logger.info("Test 3: Decorator with timeout breach (2s limit, 5s sleep)")
    
    @enforce_timeout(2)
    def slow_function():
        time.sleep(5)
        return "Done"
    
    try:
        slow_function()
        logger.error("FAIL: Should have raised TimeoutError")
    except TimeoutError as e:
        logger.info(f"PASS: Expected timeout caught: {e}")
    
    # Test 4: Decorator with successful completion
    logger.info("Test 4: Decorator with successful completion (5s limit, 1s sleep)")
    
    @enforce_timeout(5)
    def fast_function():
        time.sleep(1)
        return "Done"
    
    try:
        result = fast_function()
        logger.info(f"PASS: Function completed within timeout, result: {result}")
    except TimeoutError as e:
        logger.error(f"FAIL: Unexpected timeout: {e}")
    
    logger.info("All timeout tests completed.")

if __name__ == "__main__":
    main()