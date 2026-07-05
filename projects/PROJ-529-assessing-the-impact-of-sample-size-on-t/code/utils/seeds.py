"""
Seed management and logging utility.
Implements T005: Deterministic random seed management and logging.
"""
import os
import json
import random
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)

LOG_DIR = "data/processed/logs"
LOG_FILE = "iteration_log.jsonl"

def ensure_log_directory():
    """Ensure the log directory exists."""
    os.makedirs(LOG_DIR, exist_ok=True)

def set_seed(seed: int):
    """Set the random seed for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_seed_sequence(base_seed: int = 42, count: int = 100) -> List[int]:
    """
    Generate a sequence of deterministic seeds based on a base seed.
    """
    seeds = []
    for i in range(count):
        # Simple deterministic generation
        s = base_seed + i * 13 + 7
        seeds.append(s)
    return seeds

def log_iteration(
    iteration_id: str,
    k: int,
    seed: int,
    estimator_type: str,
    status: str,
    error: Optional[str] = None
):
    """
    Log a single subsample iteration to the JSONL file.
    """
    ensure_log_directory()
    log_path = os.path.join(LOG_DIR, LOG_FILE)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "iteration_id": iteration_id,
        "k": k,
        "seed": seed,
        "estimator_type": estimator_type,
        "status": status,
        "error": error
    }
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    
    logger.debug(f"Logged iteration: {iteration_id}")

def read_iteration_logs() -> List[Dict[str, Any]]:
    """
    Read all iteration logs from the log file.
    """
    log_path = os.path.join(LOG_DIR, LOG_FILE)
    if not os.path.exists(log_path):
        return []
    
    logs = []
    with open(log_path, 'r') as f:
        for line in f:
            logs.append(json.loads(line.strip()))
    return logs
