"""
Batch Executor for llmXive experiments.

Enforces:
1. Hard timeout per instance (FR-007).
2. Hard total wall-clock duration limit of <= 72 hours for the full experiment (FR-007).
"""

import os
import sys
import logging
import time
import signal
import json
from datetime import datetime, timedelta
from typing import Callable, Any, Tuple, Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Add project root to path for imports if running as script
if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_output_dir, get_log_level

# Configure logging
logging.basicConfig(
    level=get_log_level(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
MAX_WALL_CLOCK_HOURS = 72
MAX_WALL_CLOCK_SECONDS = MAX_WALL_CLOCK_HOURS * 3600

class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    SKIPPED = "skipped"

@dataclass
class BatchExecutionResult:
    instance_id: str
    status: ExecutionStatus
    start_time: float
    end_time: float
    duration: float
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "error_message": self.error_message,
            "result_data": self.result_data
        }

class BatchExecutor:
    """
    Manages execution of a batch of tasks with hard timeouts and global budget limits.
    """

    def __init__(
        self,
        instance_timeout_seconds: int = 3600,
        output_dir: Optional[Path] = None
    ):
        """
        Args:
            instance_timeout_seconds: Max time allowed for a single instance execution.
            output_dir: Directory to write execution logs/results.
        """
        self.instance_timeout = instance_timeout_seconds
        self.start_time_global: Optional[float] = None
        self.output_dir = output_dir or get_output_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_log_path = self.output_dir / "batch_execution_log.jsonl"

        logger.info(f"BatchExecutor initialized. Instance timeout: {self.instance_timeout}s, Max wall-clock: {MAX_WALL_CLOCK_HOURS}h")

    def _check_global_budget(self) -> bool:
        """
        Checks if the total wall-clock time has exceeded the limit.
        Returns True if execution should continue, False if budget exhausted.
        """
        if self.start_time_global is None:
            return True

        elapsed = time.time() - self.start_time_global
        if elapsed > MAX_WALL_CLOCK_SECONDS:
            logger.error(f"Global wall-clock budget exhausted. Elapsed: {elapsed:.2f}s / {MAX_WALL_CLOCK_SECONDS}s")
            return False
        return True

    def _run_with_timeout(
        self,
        func: Callable,
        instance_id: str,
        *args,
        **kwargs
    ) -> BatchExecutionResult:
        """
        Executes a function with a hard timeout per instance.
        Uses signal.SIGALRM for Unix-based timeout enforcement.
        """
        start_time = time.time()
        result_data = None
        error_message = None
        status = ExecutionStatus.ERROR

        # Define the handler for the alarm signal
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Instance {instance_id} exceeded timeout of {self.instance_timeout}s")

        # Set the alarm
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.instance_timeout)

        try:
            # Attempt to run the function
            result_data = func(*args, **kwargs)
            status = ExecutionStatus.SUCCESS
        except TimeoutError as e:
            error_message = str(e)
            status = ExecutionStatus.TIMEOUT
            logger.warning(error_message)
        except Exception as e:
            error_message = str(e)
            status = ExecutionStatus.ERROR
            logger.error(f"Instance {instance_id} failed with error: {error_message}", exc_info=True)
        finally:
            # Cancel the alarm and restore old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

        end_time = time.time()
        duration = end_time - start_time

        return BatchExecutionResult(
            instance_id=instance_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            error_message=error_message,
            result_data=result_data
        )

    def execute_batch(
        self,
        instances: List[Dict[str, Any]],
        process_func: Callable[[Dict[str, Any]], Any],
        resume: bool = False
    ) -> List[BatchExecutionResult]:
        """
        Executes a list of instances using process_func.
        Enforces per-instance timeout and global wall-clock limit.

        Args:
            instances: List of instance dictionaries.
            process_func: Function to execute for each instance.
            resume: If True, skips instances already present in the results log.

        Returns:
            List of BatchExecutionResult objects.
        """
        self.start_time_global = time.time()
        results = []
        processed_ids = set()

        # Load existing results if resuming
        if resume and self.results_log_path.exists():
            with open(self.results_log_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get("status") == ExecutionStatus.SUCCESS.value:
                            processed_ids.add(data.get("instance_id"))
                    except json.JSONDecodeError:
                        continue
            logger.info(f"Resuming from log. Skipping {len(processed_ids)} already processed instances.")

        for idx, instance in enumerate(instances):
            instance_id = instance.get("instance_id", f"instance_{idx}")

            # Check global budget before starting
            if not self._check_global_budget():
                logger.error("Stopping batch execution due to global budget limit.")
                break

            # Skip if already processed (resume mode)
            if resume and instance_id in processed_ids:
                logger.info(f"Skipping already processed instance: {instance_id}")
                results.append(BatchExecutionResult(
                    instance_id=instance_id,
                    status=ExecutionStatus.SKIPPED,
                    start_time=time.time(),
                    end_time=time.time(),
                    duration=0.0
                ))
                continue

            logger.info(f"Starting execution for instance {instance_id} ({idx+1}/{len(instances)})")
            result = self._run_with_timeout(process_func, instance_id, instance)
            results.append(result)

            # Write result immediately to log for robustness
            with open(self.results_log_path, 'a') as f:
                f.write(json.dumps(result.to_dict()) + "\n")

            if result.status == ExecutionStatus.TIMEOUT:
                # Optional: Break on first timeout or continue?
                # Based on FR-007, we enforce limits. Usually we continue to next instance
                # unless the budget is strictly for successful completions.
                # We continue but log heavily.
                pass

        elapsed_total = time.time() - self.start_time_global
        logger.info(f"Batch execution finished. Total time: {elapsed_total:.2f}s. Processed: {len(results)}.")
        return results

def main():
    """
    Example entry point for testing the BatchExecutor.
    In a real scenario, this would be called by run_baseline.py or run_high_fidelity.py.
    """
    # Mock data for demonstration
    mock_instances = [
        {"instance_id": "test_1", "data": "sample_1"},
        {"instance_id": "test_2", "data": "sample_2"},
        {"instance_id": "test_3", "data": "sample_3"},
    ]

    def mock_process(instance):
        """Simulates processing an instance."""
        # Simulate work
        time.sleep(0.5)
        return {"processed": True, "input": instance}

    # Create executor with short timeout for testing
    executor = BatchExecutor(instance_timeout_seconds=5)

    # Execute
    results = executor.execute_batch(mock_instances, mock_process)

    # Print summary
    success_count = sum(1 for r in results if r.status == ExecutionStatus.SUCCESS)
    timeout_count = sum(1 for r in results if r.status == ExecutionStatus.TIMEOUT)
    error_count = sum(1 for r in results if r.status == ExecutionStatus.ERROR)

    print(f"Execution Summary:")
    print(f"  Total: {len(results)}")
    print(f"  Success: {success_count}")
    print(f"  Timeout: {timeout_count}")
    print(f"  Error: {error_count}")

    return results

if __name__ == "__main__":
    main()