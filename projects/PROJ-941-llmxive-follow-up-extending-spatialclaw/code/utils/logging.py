import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import json

def setup_logging(log_file: str = "results/logs/execution.log") -> logging.Logger:
    """
    Setup logging infrastructure to capture execution logs.
    Logs are written to a JSON lines file with seed, run_id, blocked_operation, etc.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger('llmxive')
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers = []

    # File handler for JSON lines
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Custom formatter to output JSON
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'message': record.getMessage()
            }
            # Add extra fields if present
            for key in ['seed', 'run_id', 'blocked_operation', 'blocked_time_ms', 'task_id']:
                if hasattr(record, key):
                    log_data[key] = getattr(record, key)
            return json.dumps(log_data)

    formatter = JsonFormatter()
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler for immediate feedback
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

    return logger

def log_seed_usage(logger: logging.Logger, seed: int, run_id: int) -> None:
    """Log the seed and run_id for reproducibility."""
    logger.info(f"Seed {seed} used for run {run_id}", extra={'seed': seed, 'run_id': run_id})

def log_blocked_operation(logger: logging.Logger, operation: str, time_ms: float, task_id: str) -> None:
    """Log a blocked operation with timing and task context."""
    logger.info(f"Blocked operation: {operation} took {time_ms:.2f}ms", extra={
        'blocked_operation': operation,
        'blocked_time_ms': time_ms,
        'task_id': task_id
    })

def log_execution_step(logger: logging.Logger, step: str, task_id: str) -> None:
    """Log an execution step."""
    logger.info(f"Execution step: {step} for task {task_id}", extra={'task_id': task_id})

def extract_blocked_operations(log_file: str) -> list:
    """
    Extract blocked operations from the log file.
    Returns a list of dicts with blocked_operation, blocked_time_ms, task_id.
    """
    blocked_ops = []
    if not os.path.exists(log_file):
        return blocked_ops

    with open(log_file) as f:
        for line in f:
            try:
                data = json.loads(line)
                if 'blocked_operation' in data:
                    blocked_ops.append({
                        'blocked_operation': data['blocked_operation'],
                        'blocked_time_ms': data.get('blocked_time_ms', 0),
                        'task_id': data.get('task_id', 'unknown')
                    })
            except json.JSONDecodeError:
                continue
    return blocked_ops
