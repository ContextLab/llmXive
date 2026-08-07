"""
Batch Executor for enforcing runtime budgets and timeouts.

Implements T016b requirements:
1. Hard timeout per instance.
2. Hard total wall-clock duration limit (optional, configurable).
"""
import os
import sys
import logging
import time
import signal
from typing import Callable, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import ExecutionResult

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    CANCELLED = "cancelled"

@dataclass
class BatchExecutionResult:
    instance_id: str
    status: ExecutionStatus
    result: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: dict = None

    def to_dict(self):
        return {
            "instance_id": self.instance_id,
            "status": self.status.value,
            "result": self.result,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "metadata": self.metadata or {}
        }

class BatchExecutor:
    """
    Executes tasks with strict timeout enforcement.
    
    Note: For CPU-bound tasks or non-fork-safe environments,
    multiprocessing is safer than threading for timeouts.
    However, for model inference (often GIL-releasing or blocking IO),
    a process-based approach is robust against hangs.
    """

    def __init__(
        self,
        timeout_per_instance: int = 3600,
        total_wall_clock_limit_seconds: Optional[int] = None,
        use_multiprocessing: bool = True
    ):
        self.timeout_per_instance = timeout_per_instance
        self.total_wall_clock_limit = total_wall_clock_limit_seconds
        self.use_multiprocessing = use_multiprocessing
        self.start_time = time.time()

    def _execute_with_timeout(
        self,
        func: Callable,
        args: Tuple,
        timeout: int
    ) -> BatchExecutionResult:
        """
        Internal method to execute a function with a timeout.
        Uses multiprocessing for robustness.
        """
        import multiprocessing as mp
        from multiprocessing import Process, Queue

        result_queue = Queue()
        process_args = (func, args, result_queue)

        def worker(f, a, q):
            try:
                res = f(*a)
                q.put(("success", res))
            except Exception as e:
                q.put(("error", str(e)))

        p = Process(target=worker, args=process_args)
        p.start()
        p.join(timeout=timeout)

        if p.is_alive():
            p.terminate()
            p.join()
            instance_id = args[0].get("instance_id", "unknown") if isinstance(args[0], dict) else "unknown"
            return BatchExecutionResult(
                instance_id=instance_id,
                status=ExecutionStatus.TIMEOUT,
                error_message=f"Execution timed out after {timeout} seconds",
                execution_time=float(timeout)
            )

        try:
            status, payload = result_queue.get(timeout=1)
            if status == "success":
                instance_id = args[0].get("instance_id", "unknown") if isinstance(args[0], dict) else "unknown"
                # If the result is an ExecutionResult, extract instance_id if not set
                if isinstance(payload, ExecutionResult) and not payload.instance_id:
                    payload.instance_id = instance_id
                return BatchExecutionResult(
                    instance_id=instance_id,
                    status=ExecutionStatus.SUCCESS,
                    result=payload,
                    execution_time=time.time() - (time.time() - timeout) # Approximate
                )
            else:
                instance_id = args[0].get("instance_id", "unknown") if isinstance(args[0], dict) else "unknown"
                return BatchExecutionResult(
                    instance_id=instance_id,
                    status=ExecutionStatus.ERROR,
                    error_message=payload,
                    execution_time=float(timeout)
                )
        except Exception as e:
            instance_id = args[0].get("instance_id", "unknown") if isinstance(args[0], dict) else "unknown"
            return BatchExecutionResult(
                instance_id=instance_id,
                status=ExecutionStatus.ERROR,
                error_message=f"Failed to retrieve result from queue: {e}",
                execution_time=float(timeout)
            )

    def execute(
        self,
        func: Callable,
        args: Tuple
    ) -> BatchExecutionResult:
        """
        Execute a single task with timeout enforcement.
        
        Args:
            func: The function to execute.
            args: Arguments tuple for the function.
        
        Returns:
            BatchExecutionResult containing the outcome.
        """
        # Check total wall clock limit
        if self.total_wall_clock_limit:
            elapsed = time.time() - self.start_time
            if elapsed >= self.total_wall_clock_limit:
                logger.error("Total wall-clock budget exceeded. Aborting execution.")
                return BatchExecutionResult(
                    instance_id="global",
                    status=ExecutionStatus.CANCELLED,
                    error_message="Total wall-clock budget exceeded"
                )

        logger.debug(f"Executing task with timeout {self.timeout_per_instance}s")
        start = time.time()
        result = self._execute_with_timeout(func, args, self.timeout_per_instance)
        result.execution_time = time.time() - start
        
        # Update instance_id if it was unknown in the timeout path
        if result.instance_id == "unknown" and isinstance(args[0], dict):
            result.instance_id = args[0].get("instance_id", "unknown")

        return result

def main():
    """
    Simple test for BatchExecutor.
    """
    def slow_func(x, y):
        time.sleep(5)
        return x + y

    def fail_func(x):
        raise ValueError("Intentional failure")

    executor = BatchExecutor(timeout_per_instance=2) # 2s timeout for test

    # Test success
    print("Testing success...")
    res1 = executor.execute(slow_func, (1, 2)) # Should timeout
    print(f"Result 1: {res1.status}, {res1.error_message}")

    # Test failure
    print("Testing failure...")
    res2 = executor.execute(fail_func, (1,))
    print(f"Result 2: {res2.status}, {res2.error_message}")

if __name__ == "__main__":
    main()