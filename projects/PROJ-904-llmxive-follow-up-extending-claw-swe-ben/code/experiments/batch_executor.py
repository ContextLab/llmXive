"""
Batch execution infrastructure for running LLM experiments with timeout and error handling.
"""
import os
import sys
import logging
import time
import signal
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Callable, List, Dict, Any, Optional, TypeVar, Generic
from functools import wraps
from contextlib import contextmanager

# Project imports
from models.task_instance import TaskInstance
from models.context_config import ContextConfiguration
from models.execution_result import ExecutionResult, ExecutionStatus
from utils.logger import setup_logger, log_error

logger = setup_logger(__name__)

# Type variables for generic decorator
F = TypeVar('F', bound=Callable)

class TimeoutGuard:
    """
    A decorator that enforces a hard timeout on function execution.
    If the function exceeds the timeout, it raises a TimeoutError.
    
    This implementation uses threading to monitor execution time,
    making it compatible with multi-threaded environments.
    """
    def __init__(self, timeout_seconds: int):
        if timeout_seconds <= 0:
            raise ValueError("Timeout must be a positive integer")
        self.timeout_seconds = timeout_seconds
        self.logger = setup_logger(__name__)

    def __call__(self, func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_container = {'value': None, 'exception': None, 'done': False}
            
            def target():
                try:
                    result_container['value'] = func(*args, **kwargs)
                except Exception as e:
                    result_container['exception'] = e
                finally:
                    result_container['done'] = True

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            
            thread.join(timeout=self.timeout_seconds)
            
            if not result_container['done']:
                # Thread is still running, raise timeout
                self.logger.warning(
                    f"Function {func.__name__} exceeded timeout of {self.timeout_seconds}s. "
                    f"Raising TimeoutError."
                )
                raise TimeoutError(
                    f"Execution of {func.__name__} exceeded the limit of {self.timeout_seconds} seconds."
                )
            
            if result_container['exception']:
                raise result_container['exception']
            
            return result_container['value']

        return wrapper  # type: ignore


class BatchExecutor:
    """
    Manages the execution of multiple task instances with configurable parallelism
    and per-instance timeout constraints.
    """
    def __init__(
        self, 
        max_workers: int = 4, 
        instance_timeout_seconds: int = 300,
        total_wall_clock_seconds: Optional[int] = None
    ):
        self.max_workers = max_workers
        self.instance_timeout_seconds = instance_timeout_seconds
        self.total_wall_clock_seconds = total_wall_clock_seconds
        self.executor: Optional[ThreadPoolExecutor] = None
        self.logger = setup_logger(__name__)
        
        if self.total_wall_clock_seconds:
            self.logger.info(
                f"BatchExecutor initialized with total wall-clock limit: "
                f"{self.total_wall_clock_seconds}s"
            )

    def submit(
        self, 
        task: TaskInstance, 
        execution_func: Callable[[TaskInstance, ContextConfiguration], ExecutionResult],
        config: Optional[ContextConfiguration] = None
    ) -> ExecutionResult:
        """
        Submits a single task for execution with timeout enforcement.
        
        Args:
            task: The task instance to execute.
            execution_func: The function to run the task.
            config: Optional context configuration. Defaults to None.
        
        Returns:
            ExecutionResult containing status, output, and metadata.
        """
        if config is None:
            config = ContextConfiguration(strategy_type="baseline")

        start_time = time.time()
        
        try:
            # Wrap the execution function with TimeoutGuard
            guarded_func = TimeoutGuard(self.instance_timeout_seconds)(execution_func)
            result = guarded_func(task, config)
            
            # Ensure result has duration
            if not hasattr(result, 'duration_seconds'):
                result.duration_seconds = time.time() - start_time
                
            return result

        except TimeoutError as e:
            self.logger.error(f"Task {task.task_id} timed out: {str(e)}")
            return ExecutionResult(
                task_id=task.task_id,
                status=ExecutionStatus.TIMEOUT,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            self.logger.error(f"Task {task.task_id} failed with exception: {str(e)}", exc_info=True)
            return ExecutionResult(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )

    def submit_batch(
        self, 
        tasks: List[TaskInstance], 
        execution_func: Callable[[TaskInstance, ContextConfiguration], ExecutionResult],
        config: Optional[ContextConfiguration] = None
    ) -> List[ExecutionResult]:
        """
        Submits a batch of tasks for parallel execution.
        
        Args:
            tasks: List of task instances.
            execution_func: The function to run each task.
            config: Optional context configuration.
        
        Returns:
            List of ExecutionResults.
        """
        if config is None:
            config = ContextConfiguration(strategy_type="baseline")

        if self.total_wall_clock_seconds:
            wall_start = time.time()

        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self.submit, task, execution_func, config): task 
                for task in tasks
            }

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if self.total_wall_clock_seconds:
                        elapsed = time.time() - wall_start
                        if elapsed > self.total_wall_clock_seconds:
                            self.logger.critical(
                                f"Total wall-clock time {elapsed:.2f}s exceeded limit. "
                                f"Cancelling remaining tasks."
                            )
                            executor.shutdown(wait=False)
                            break
                except Exception as e:
                    self.logger.error(f"Unexpected error processing task {task.task_id}: {e}")
                    results.append(ExecutionResult(
                        task_id=task.task_id,
                        status=ExecutionStatus.FAILED,
                        error_message=f"Unexpected batch error: {str(e)}"
                    ))

        return results

    def shutdown(self, wait: bool = True):
        """Shuts down the executor."""
        if self.executor:
            self.executor.shutdown(wait=wait)
            self.logger.info("BatchExecutor shutdown complete.")

def main():
    """
    Main entry point for testing the batch executor.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create a mock execution function
    def mock_run(task: TaskInstance, config: ContextConfiguration) -> ExecutionResult:
        time.sleep(1)
        return ExecutionResult(
            task_id=task.task_id,
            status=ExecutionStatus.COMPLETED,
            output=f"Processed {task.task_id}"
        )

    executor = BatchExecutor(max_workers=2, instance_timeout_seconds=5)
    
    tasks = [
        TaskInstance(task_id=f"test_{i}", problem_statement=f"Problem {i}")
        for i in range(3)
    ]

    logger.info("Starting batch execution...")
    results = executor.submit_batch(tasks, mock_run)
    
    for r in results:
        logger.info(f"Task {r.task_id}: {r.status} ({r.duration_seconds:.2f}s)")
        
    executor.shutdown()

if __name__ == "__main__":
    main()
