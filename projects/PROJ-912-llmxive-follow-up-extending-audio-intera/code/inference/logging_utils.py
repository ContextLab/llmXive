"""
Logging utilities for inference performance tracking.

Provides structured logging for inference runs, including latency,
resource usage, and constraint checking.
"""
import logging
import time
import json
import tracemalloc
import psutil
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from config import get_resource_limits, get_evaluation_config

@dataclass
class InferencePerformanceLog:
    """Container for a single performance log entry."""
    timestamp: str
    model_id: str
    batch_id: int
    sample_count: int
    latency_ms: float
    ram_gb: float
    cpu_percent: float
    constraint_check: Dict[str, bool]

def get_logger_for_inference(name: str = "inference") -> logging.Logger:
    """Get a logger configured for inference tasks."""
    logger = get_logger(name)
    return logger

def log_inference_start(logger: logging.Logger, model_id: str, dataset_size: int):
    """Log the start of an inference run."""
    logger.info(f"Inference starting for model: {model_id}")
    logger.info(f"Dataset size: {dataset_size} samples")

def log_inference_batch(
    logger: logging.Logger,
    model_id: str,
    batch_id: int,
    sample_count: int,
    latency_ms: float,
    ram_gb: float,
    cpu_percent: float
):
    """Log the completion of an inference batch."""
    logger.debug(f"Batch {batch_id} complete: {sample_count} samples, {latency_ms:.2f}ms, {ram_gb:.2f}GB RAM")

def log_inference_summary(
    logger: logging.Logger,
    model_id: str,
    total_samples: int,
    successful: int,
    failed: int,
    avg_latency_ms: float,
    peak_ram_gb: float
):
    """Log the summary of an inference run."""
    logger.info(f"Inference summary for {model_id}:")
    logger.info(f"  Total samples: {total_samples}")
    logger.info(f"  Successful: {successful}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Avg latency: {avg_latency_ms:.2f}ms")
    logger.info(f"  Peak RAM: {peak_ram_gb:.2f}GB")

def get_resource_usage_detailed() -> Dict[str, float]:
    """Get detailed resource usage information."""
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        return {
            'ram_mb': mem_info.rss / (1024 * 1024),
            'ram_gb': mem_info.rss / (1024 * 1024 * 1024),
            'cpu_percent': process.cpu_percent(),
            'num_threads': process.num_threads()
        }
    except Exception as e:
        logger = get_logger("logging_utils")
        logger.warning(f"Failed to get resource usage: {str(e)}")
        return {
            'ram_mb': 0.0,
            'ram_gb': 0.0,
            'cpu_percent': 0.0,
            'num_threads': 0
        }

def log_resource_usage_detailed(logger: logging.Logger, prefix: str = ""):
    """Log detailed resource usage."""
    usage = get_resource_usage_detailed()
    logger.debug(f"{prefix} RAM: {usage['ram_gb']:.2f}GB, CPU: {usage['cpu_percent']:.1f}%")

def log_constraint_check(logger: logging.Logger, model_id: str) -> Dict[str, bool]:
    """
    Check and log resource constraints.
    
    Returns a dictionary of constraint check results.
    """
    limits = get_resource_limits()
    usage = get_resource_usage_detailed()
    
    constraints = {
        'ram_under_limit': usage['ram_gb'] <= limits.max_ram_gb,
        'cpu_under_limit': usage['num_threads'] <= limits.max_cores,
        'time_under_limit': True  # Time is checked differently
    }
    
    logger.info(f"Constraint check for {model_id}:")
    for constraint, passed in constraints.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"  {constraint}: {status}")
    
    return constraints

def create_performance_log_entry(
    model_id: str,
    batch_id: int,
    sample_count: int,
    latency_ms: float,
    ram_gb: float,
    cpu_percent: float
) -> InferencePerformanceLog:
    """Create a performance log entry."""
    from datetime import datetime
    
    return InferencePerformanceLog(
        timestamp=datetime.now().isoformat(),
        model_id=model_id,
        batch_id=batch_id,
        sample_count=sample_count,
        latency_ms=latency_ms,
        ram_gb=ram_gb,
        cpu_percent=cpu_percent,
        constraint_check=log_constraint_check(get_logger("inference"), model_id)
    )

def save_performance_log(log_entry: InferencePerformanceLog, output_path: Path):
    """Save a single performance log entry."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'a') as f:
        f.write(json.dumps(asdict(log_entry)) + '\n')

def save_performance_logs_batch(log_entries: List[InferencePerformanceLog], output_path: Path):
    """Save a batch of performance log entries."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for entry in log_entries:
            f.write(json.dumps(asdict(entry)) + '\n')

def main():
    """Main function for testing logging utilities."""
    logger = get_logger_for_inference("test")
    log_inference_start(logger, "test_model", 100)
    
    usage = get_resource_usage_detailed()
    log_resource_usage_detailed(logger, "Initial: ")
    
    constraints = log_constraint_check(logger, "test_model")
    
    log_inference_summary(
        logger,
        "test_model",
        100,
        95,
        5,
        15.5,
        2.3
    )
    
    logger.info("Logging utilities test complete")

if __name__ == "__main__":
    main()
