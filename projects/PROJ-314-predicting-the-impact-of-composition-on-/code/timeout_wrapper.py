"""
Timeout enforcement module for the llmXive pipeline.
Implements a 6-hour execution limit for the full modeling pipeline.
"""
import signal
import time
import logging
import sys
import json
from pathlib import Path
from typing import Callable, Any, Optional, Dict
from multiprocessing import Process, Queue, Event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline_timing.log')
    ]
)
logger = logging.getLogger(__name__)

class TimeoutExceededError(Exception):
    """Raised when the pipeline execution exceeds the allowed time limit."""
    pass

class TimeoutHandler:
    """
    Context manager and utility for enforcing execution timeouts.
    Uses multiprocessing to ensure a hard kill on timeout.
    """
    def __init__(self, timeout_seconds: int = 21600):
        """
        Initialize the timeout handler.
        
        Args:
            timeout_seconds: Maximum allowed execution time in seconds.
                             Default is 6 hours (21600 seconds).
        """
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(__name__)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        self.logger.info(f"Pipeline execution completed in {duration:.2f} seconds.")
        
        if exc_type is TimeoutExceededError:
            self.logger.error(f"TIMEOUT: Execution exceeded {self.timeout_seconds} seconds limit.")
            return False  # Re-raise the exception
        return True

    def check_timeout(self):
        """Check if the timeout has been exceeded."""
        if self.start_time is None:
            return False
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout_seconds:
            raise TimeoutExceededError(
                f"Execution timeout exceeded: {elapsed:.2f}s > {self.timeout_seconds}s"
            )
        return False

    def run_with_timeout(self, func: Callable, args: tuple = (), kwargs: dict = None) -> Any:
        """
        Run a function with a timeout using multiprocessing.
        
        Args:
            func: The function to execute.
            args: Positional arguments for the function.
            kwargs: Keyword arguments for the function.
            
        Returns:
            The result of the function execution.
            
        Raises:
            TimeoutExceededError: If the function execution exceeds the timeout.
        """
        if kwargs is None:
            kwargs = {}

        result_queue = Queue()
        error_queue = Queue()
        process = Process(target=self._run_func, args=(func, args, kwargs, result_queue, error_queue))
        
        process.start()
        process.join(timeout=self.timeout_seconds)

        if process.is_alive():
            process.terminate()
            process.join()
            raise TimeoutExceededError(
                f"Execution timeout exceeded: {self.timeout_seconds}s"
            )

        if not result_queue.empty():
            return result_queue.get()
        
        if not error_queue.empty():
            raise error_queue.get()

        raise RuntimeError("Function execution failed without returning a result or error.")

    @staticmethod
    def _run_func(func: Callable, args: tuple, kwargs: dict, result_queue: Queue, error_queue: Queue):
        """Helper method to run the function in a separate process."""
        try:
            result = func(*args, **kwargs)
            result_queue.put(result)
        except Exception as e:
            error_queue.put(e)

def ensure_output_dir(output_dir: str = "data/results"):
    """Ensure the output directory exists."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

def save_runtime_metrics(duration: float, status: str = "completed"):
    """
    Save runtime metrics to a JSON file.
    
    Args:
        duration: Execution duration in seconds.
        status: Execution status (completed, timeout, error).
    """
    ensure_output_dir()
    metrics = {
        "duration_seconds": duration,
        "status": status,
        "timeout_limit_seconds": 21600
    }
    
    output_path = Path("data/results/runtime_metrics.json")
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Runtime metrics saved to {output_path}")

def run_full_pipeline():
    """
    Main pipeline execution function wrapped with timeout enforcement.
    This function orchestrates the full modeling pipeline.
    """
    logger.info("Starting full pipeline execution with 6-hour timeout limit.")
    
    start_time = time.time()
    
    try:
        with TimeoutHandler(timeout_seconds=21600) as handler:
            # Import here to avoid circular imports if this file is imported elsewhere
            from ingestion import main as run_ingestion
            from modeling import main as run_modeling
            from report import main as run_report
            
            # Execute pipeline stages
            logger.info("Stage 1: Data Ingestion")
            run_ingestion()
            handler.check_timeout()
            
            logger.info("Stage 2: Modeling and Training")
            run_modeling()
            handler.check_timeout()
            
            logger.info("Stage 3: Reporting and Interpretation")
            run_report()
            handler.check_timeout()
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
            save_runtime_metrics(duration, "completed")
            
    except TimeoutExceededError as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"Pipeline timed out: {e}")
        save_runtime_metrics(duration, "timeout")
        raise
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"Pipeline failed with error: {e}")
        save_runtime_metrics(duration, "error")
        raise

def main():
    """Main entry point for the timeout wrapper script."""
    try:
        run_full_pipeline()
    except TimeoutExceededError:
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()