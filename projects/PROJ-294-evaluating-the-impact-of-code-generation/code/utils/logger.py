import logging
import os
from datetime import datetime
from utils import setup_logging, get_logger, set_task_id, get_task_id

def setup_logging_infrastructure():
    """
    T004: Setup logging infrastructure with timestamp and task ID tracking.
    """
    logger = setup_logging(task_id="T004")
    logger.info("Logging infrastructure initialized.")
    return logger

def log_performance_metrics(task_id: str, generation_duration_ms: float, tasks_per_minute: float):
    """
    T004b: Log performance hooks.
    Emits structured log events.
    """
    logger = setup_logging(task_id=task_id)
    logger.info(f"PERF_METRICS | duration_ms={generation_duration_ms} | tasks_per_minute={tasks_per_minute}")

def aggregate_performance_metrics(logs: list) -> dict:
    """
    T004c: Aggregate metrics from logs.
    Returns aggregated stats.
    """
    if not logs:
        return {"avg_duration_ms": 0, "avg_tasks_per_minute": 0}
    
    total_duration = sum(log.get("duration_ms", 0) for log in logs)
    total_rate = sum(log.get("tasks_per_minute", 0) for log in logs)
    count = len(logs)
    
    return {
        "avg_duration_ms": total_duration / count,
        "avg_tasks_per_minute": total_rate / count,
        "sample_count": count
    }

def main():
    setup_logging_infrastructure()

if __name__ == "__main__":
    main()
