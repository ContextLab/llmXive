import time
import threading
import concurrent.futures
import os
import logging
from typing import Callable, List, Any, Optional, TypeVar, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from config import set_global_seed

logger = logging.getLogger(__name__)

T = TypeVar('T')

class GlobalSchedulerError(Exception):
    """Raised when the global scheduler constraints are violated."""
    pass

@dataclass
class BatchExecutionStats:
    """Aggregated statistics for a batch execution run."""
    total_instances: int = 0
    successful: int = 0
    failed: int = 0
    timed_out: int = 0
    resource_constrained: int = 0
    total_wall_time_seconds: float = 0.0
    avg_instance_time_seconds: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    active_workers: int = 0
    max_workers_used: int = 0

    def to_dict(self) -> dict:
        return {
            "total_instances": self.total_instances,
            "successful": self.successful,
            "failed": self.failed,
            "timed_out": self.timed_out,
            "resource_constrained": self.resource_constrained,
            "total_wall_time_seconds": self.total_wall_time_seconds,
            "avg_instance_time_seconds": self.avg_instance_time_seconds,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "max_workers_used": self.max_workers_used
        }

class GlobalScheduler:
    """
    Enforces the global 72-hour wall-clock budget for the entire experiment.
    This runs in a separate thread to monitor elapsed time and signal cancellation.
    """
    MAX_WALL_CELLS_SECONDS = 72 * 60 * 60  # 72 hours

    def __init__(self, start_time: Optional[datetime] = None):
        self.start_time = start_time or datetime.now()
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._elapsed_at_stop = 0.0

    def start(self):
        """Start the monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"GlobalScheduler started. Budget: {self.MAX_WALL_CELLS_SECONDS / 3600:.1f} hours.")

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed >= self.MAX_WALL_CELLS_SECONDS:
                self._elapsed_at_stop = elapsed
                logger.error(f"GlobalScheduler: 72h budget exceeded! Elapsed: {elapsed:.2f}s. Signaling stop.")
                self._stop_event.set()
                return
            time.sleep(60)  # Check every minute

    def stop(self):
        """Signal the monitor to stop."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def is_budget_exceeded(self) -> bool:
        """Check if the global budget has been exceeded."""
        return self._stop_event.is_set()

    def time_remaining(self) -> float:
        """Calculate remaining time in seconds."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return max(0.0, self.MAX_WALL_CELLS_SECONDS - elapsed)

class BatchExecutor:
    """
    Executes a batch of tasks with parallelism, respecting per-instance timeouts
    and the global 72-hour wall-clock budget.
    """
    def __init__(
        self,
        max_workers: int = 4,
        instance_timeout_seconds: int = 3600,
        global_scheduler: Optional[GlobalScheduler] = None
    ):
        self.max_workers = max_workers
        self.instance_timeout_seconds = instance_timeout_seconds
        self.global_scheduler = global_scheduler or GlobalScheduler()
        self.stats = BatchExecutionStats()
        self._lock = threading.Lock()

    def execute_batch(
        self,
        tasks: List[Tuple[Any, ...]],
        worker_func: Callable[..., Any]
    ) -> List[Any]:
        """
        Execute a list of tasks using a ThreadPoolExecutor.
        
        Args:
            tasks: List of argument tuples to pass to worker_func.
            worker_func: The function to execute for each task.
        
        Returns:
            List of results in the same order as tasks.
        """
        self.stats.start_time = datetime.now()
        self.global_scheduler.start()
        results = [None] * len(tasks)
        
        logger.info(f"Starting batch execution with {self.max_workers} workers. "
                    f"Total tasks: {len(tasks)}. Timeout: {self.instance_timeout_seconds}s.")

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_idx = {}
                
                # Submit all tasks
                for idx, args in enumerate(tasks):
                    if self.global_scheduler.is_budget_exceeded():
                        logger.warning("Global budget exceeded before all tasks submitted.")
                        break
                    
                    future = executor.submit(self._run_with_timeout, worker_func, args)
                    future_to_idx[future] = idx
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        result = future.result()
                        with self._lock:
                            self.stats.successful += 1
                        results[idx] = result
                    except concurrent.futures.TimeoutError:
                        with self._lock:
                            self.stats.timed_out += 1
                        results[idx] = {"status": "timeout", "error": "Instance execution timed out"}
                    except GlobalSchedulerError:
                        with self._lock:
                            self.stats.failed += 1
                        results[idx] = {"status": "cancelled", "error": "Global budget exceeded"}
                    except Exception as e:
                        with self._lock:
                            self.stats.failed += 1
                        results[idx] = {"status": "failed", "error": str(e)}
                        logger.exception(f"Task {idx} failed unexpectedly: {e}")
                    
                    # Update active workers count
                    with self._lock:
                        active = sum(1 for f in future_to_idx if not f.done())
                        self.stats.max_workers_used = max(self.stats.max_workers_used, active)

        finally:
            self.global_scheduler.stop()
            self.stats.end_time = datetime.now()
            self.stats.total_instances = len(tasks)
            if self.stats.start_time and self.stats.end_time:
                self.stats.total_wall_time_seconds = (self.stats.end_time - self.stats.start_time).total_seconds()
                if self.stats.successful > 0:
                    self.stats.avg_instance_time_seconds = self.stats.total_wall_time_seconds / self.stats.successful
            
            logger.info(f"Batch execution complete. Stats: {self.stats.to_dict()}")

        return results

    def _run_with_timeout(self, func: Callable, args: Tuple) -> Any:
        """
        Wrapper to enforce per-instance timeout and check global scheduler.
        """
        if self.global_scheduler.is_budget_exceeded():
            raise GlobalSchedulerError("Global budget exceeded")
        
        start = time.time()
        try:
            # We use a future with timeout to enforce per-instance limit
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as single_executor:
                future = single_executor.submit(func, *args)
                result = future.result(timeout=self.instance_timeout_seconds)
            return result
        except concurrent.futures.TimeoutError:
            raise concurrent.futures.TimeoutError(f"Task exceeded {self.instance_timeout_seconds}s limit")

def main():
    """
    Demo/Verification script for BatchExecutor performance optimization.
    Simulates a workload to verify the 72h budget enforcement and parallel efficiency.
    """
    import argparse
    import random

    parser = argparse.ArgumentParser(description="Test BatchExecutor performance")
    parser.add_argument("--tasks", type=int, default=100, help="Number of simulated tasks")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--task-time", type=float, default=1.0, help="Simulated task duration in seconds")
    args = parser.parse_args()

    set_global_seed(42)

    def simulated_work(task_id: int, duration: float):
        """Simulates a model inference or analysis step."""
        time.sleep(duration)
        return {"task_id": task_id, "duration": duration, "status": "ok"}

    tasks = [(i, args.task_time) for i in range(args.tasks)]
    
    executor = BatchExecutor(
        max_workers=args.workers,
        instance_timeout_seconds=3600,
        global_scheduler=GlobalScheduler()
    )

    results = executor.execute_batch(tasks, simulated_work)
    
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "ok")
    print(f"Executed {len(results)} tasks. Successes: {success_count}.")
    print(f"Total wall time: {executor.stats.total_wall_time_seconds:.2f}s")
    print(f"Max workers used: {executor.stats.max_workers_used}")
    
    # Verify budget logic (this would trigger if we ran for 72h, but we simulate)
    if executor.stats.total_wall_time_seconds > args.tasks * args.task_time / args.workers * 2:
        logger.warning("Efficiency lower than expected, check overhead.")

if __name__ == "__main__":
    main()