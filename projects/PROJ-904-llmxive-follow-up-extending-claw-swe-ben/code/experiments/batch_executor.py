import os
import sys
import logging
import time
import signal
import json
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

class TimeoutGuard:
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds

    def __enter__(self):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout_seconds)

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)

class GlobalTimeBudgetEnforcer:
    def __init__(self, total_budget_seconds: int):
        self.total_budget = total_budget_seconds
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)

    def remaining_time(self) -> float:
        elapsed = time.time() - self.start_time
        return max(0, self.total_budget - elapsed)

    def is_budget_exceeded(self) -> bool:
        return self.remaining_time() <= 0

    def log_status(self):
        remaining = self.remaining_time() / 3600
        self.logger.info(f"Remaining budget: {remaining:.2f} hours")

class BatchExecutor:
    def __init__(self, max_workers: int = 4, time_budget: int = 72 * 3600):
        self.max_workers = max_workers
        self.enforcer = GlobalTimeBudgetEnforcer(time_budget)
        self.logger = logging.getLogger(__name__)

    def submit(self, func: Callable, args: List[Any]) -> List[Dict]:
        results = []
        for i, arg in enumerate(args):
            if self.enforcer.is_budget_exceeded():
                self.logger.warning("Time budget exceeded, stopping batch")
                break
            
            self.enforcer.log_status()
            
            try:
                with TimeoutGuard(3600):  # 1 hour per task
                    result = func(arg)
                    results.append({"index": i, "result": result, "status": "success"})
            except TimeoutError:
                results.append({"index": i, "status": "timeout"})
            except Exception as e:
                results.append({"index": i, "status": "error", "error": str(e)})
        
        return results

def main():
    logging.basicConfig(level=logging.INFO)
    executor = BatchExecutor()
    
    def dummy_func(x):
        return x * 2
    
    results = executor.submit(dummy_func, [1, 2, 3])
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
