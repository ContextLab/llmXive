"""
Timeout handling module for symbolic solver steps.

Implements configurable timeout enforcement per solver step, recording
timeout events to the trial log as specified in T017.
"""
import logging
import signal
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, Any, Tuple
import os
import csv

from config import load_config, ExperimentConfig
from trial_log_schema import TrialLogger, TrialLogEntry


@dataclass
class TimeoutResult:
    """Result of a timed solver step execution."""
    success: bool
    result: Optional[Any] = None
    timeout_triggered: bool = False
    elapsed_seconds: float = 0.0
    error_message: Optional[str] = None


class TimeoutError(Exception):
    """Raised when a solver step exceeds the configured timeout."""
    pass


class TimeoutHandler:
    """
    Handles timeout enforcement for solver steps.
    
    Uses a thread-based timeout mechanism to interrupt long-running
    solver operations and record timeout events to the trial log.
    """
    
    def __init__(self, config: ExperimentConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the timeout handler.
        
        Args:
            config: Experiment configuration containing timeout_limits
            logger: Optional logger instance
        """
        self.config = config
        self.timeout_seconds = config.timeout_limits.solver_step_seconds
        self.logger = logger or logging.getLogger(__name__)
        self._cancel_event = threading.Event()
        self._result_container = [None]
        self._exception_container = [None]
    
    def _execute_with_timeout(
        self,
        func: Callable,
        args: Tuple = (),
        kwargs: Optional[dict] = None
    ) -> Tuple[Optional[Any], Optional[Exception]]:
        """
        Execute a function with timeout enforcement.
        
        Args:
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            
        Returns:
            Tuple of (result, exception) - one will be None
        """
        kwargs = kwargs or {}
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout_seconds)
        
        if thread.is_alive():
            # Thread is still running - timeout occurred
            # Note: We cannot truly kill the thread in Python, but we can
            # signal cancellation and treat it as a timeout
            self._cancel_event.set()
            return None, TimeoutError(
                f"Solver step exceeded timeout of {self.timeout_seconds} seconds"
            )
        
        if exception[0] is not None:
            return None, exception[0]
        
        return result[0], None
    
    def execute_step(
        self,
        solver_func: Callable,
        trial_id: int,
        step: int,
        logger: Optional[TrialLogger] = None,
        *args,
        **kwargs
    ) -> TimeoutResult:
        """
        Execute a solver step with timeout enforcement.
        
        Args:
            solver_func: The solver function to execute
            trial_id: Current trial identifier
            step: Current step number within the trial
            logger: Optional TrialLogger instance to record timeout events
            *args: Positional arguments for solver_func
            **kwargs: Keyword arguments for solver_func
            
        Returns:
            TimeoutResult containing execution outcome
        """
        start_time = time.time()
        self._cancel_event.clear()
        
        self.logger.info(
            f"Executing solver step {step} for trial {trial_id} "
            f"(timeout: {self.timeout_seconds}s)"
        )
        
        result, exception = self._execute_with_timeout(
            solver_func,
            args=args,
            kwargs=kwargs
        )
        
        elapsed = time.time() - start_time
        
        if exception is not None:
            if isinstance(exception, TimeoutError):
                # Timeout occurred - record to trial log
                if logger:
                    log_entry = TrialLogEntry(
                        trial_id=trial_id,
                        step=step,
                        success=False,
                        infeasible=False,
                        timeout=True,
                        timeout_reason="step_limit",
                        latency_ms=round(elapsed * 1000, 2)
                    )
                    logger.log_entry(log_entry)
                    self.logger.warning(
                        f"Trial {trial_id}, step {step}: TIMEOUT after {elapsed:.2f}s"
                    )
                
                return TimeoutResult(
                    success=False,
                    timeout_triggered=True,
                    elapsed_seconds=elapsed,
                    error_message=str(exception)
                )
            else:
                # Other exception
                self.logger.error(
                    f"Trial {trial_id}, step {step}: Exception - {str(exception)}"
                )
                if logger:
                    log_entry = TrialLogEntry(
                        trial_id=trial_id,
                        step=step,
                        success=False,
                        infeasible=True,
                        timeout=False,
                        latency_ms=round(elapsed * 1000, 2)
                    )
                    logger.log_entry(log_entry)
                
                return TimeoutResult(
                    success=False,
                    elapsed_seconds=elapsed,
                    error_message=str(exception)
                )
        
        # Success
        self.logger.info(
            f"Trial {trial_id}, step {step}: Completed in {elapsed:.2f}s"
        )
        if logger:
            log_entry = TrialLogEntry(
                trial_id=trial_id,
                step=step,
                success=True,
                infeasible=False,
                timeout=False,
                latency_ms=round(elapsed * 1000, 2)
            )
            logger.log_entry(log_entry)
        
        return TimeoutResult(
            success=True,
            result=result,
            elapsed_seconds=elapsed
        )
    
    def get_timeout_limit(self) -> float:
        """Return the configured timeout limit in seconds."""
        return self.timeout_seconds


def main():
    """
    Demonstrate timeout handler functionality with a mock solver.
    
    This function runs a quick test to verify timeout enforcement works
    correctly and logs events to the trial log.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = load_config()
    timeout_handler = TimeoutHandler(config, logger)
    
    # Ensure results directory exists
    results_dir = config.paths.results
    os.makedirs(results_dir, exist_ok=True)
    
    # Create trial logger
    trial_log_path = os.path.join(results_dir, "trial_log.csv")
    trial_logger = TrialLogger(log_file=trial_log_path)
    
    # Define a mock solver that sometimes times out
    def mock_solver(trial_id, step, should_timeout=False):
        """Mock solver function for testing."""
        if should_timeout:
            # Simulate a long-running operation
            time.sleep(timeout_handler.get_timeout_limit() + 5)
            return {"status": "completed"}
        else:
            time.sleep(0.1)  # Quick completion
            return {"status": "completed", "step": step}
    
    # Test 1: Normal execution (no timeout)
    logger.info("=== Test 1: Normal execution ===")
    result = timeout_handler.execute_step(
        mock_solver,
        trial_id=1,
        step=1,
        logger=trial_logger,
        should_timeout=False
    )
    assert result.success, "Normal execution should succeed"
    assert not result.timeout_triggered, "Timeout should not be triggered"
    
    # Test 2: Timeout scenario
    logger.info("=== Test 2: Timeout scenario ===")
    result = timeout_handler.execute_step(
        mock_solver,
        trial_id=2,
        step=1,
        logger=trial_logger,
        should_timeout=True
    )
    assert not result.success, "Timeout execution should fail"
    assert result.timeout_triggered, "Timeout should be triggered"
    
    # Verify trial log contains timeout entry
    logger.info("=== Verifying trial log ===")
    with open(trial_log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2, f"Expected 2 log entries, got {len(rows)}"
        
        # Check timeout entry
        timeout_entry = next(
            (r for r in rows if int(r['trial_id']) == 2),
            None
        )
        assert timeout_entry is not None, "Timeout entry not found"
        assert timeout_entry['timeout'] == 'True', "Timeout flag should be True"
        assert timeout_entry['timeout_reason'] == 'step_limit', "Timeout reason should be step_limit"
    
    logger.info("=== All timeout handler tests passed ===")
    print(f"Trial log written to: {trial_log_path}")


if __name__ == "__main__":
    main()