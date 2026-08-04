"""
Inference logging utilities for recording performance and resource usage.

This module provides structured logging for:
- Inference start/summary events
- Per-batch processing metrics (latency, throughput)
- Detailed resource usage (RAM, CPU)
- Constraint checking against project limits (FR-004, SC-002)
"""

import logging
import time
import json
import tracemalloc
import psutil
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Import project-specific logger setup
from utils.logger import get_logger, setup_logging
from config import get_resource_limits, get_path_config


@dataclass
class InferencePerformanceLog:
    """Dataclass representing a single inference performance log entry."""
    timestamp: str
    model_id: str
    event_type: str  # 'start', 'batch', 'summary', 'resource'
    batch_index: Optional[int] = None
    batch_size: Optional[int] = None
    latency_ms: Optional[float] = None
    throughput_samples_per_sec: Optional[float] = None
    ram_mb_current: Optional[float] = None
    ram_mb_peak: Optional[float] = None
    cpu_percent: Optional[float] = None
    constraint_pass: Optional[bool] = None
    constraint_details: Optional[str] = None
    error_message: Optional[str] = None


def get_logger_for_inference() -> logging.Logger:
    """Get a logger specifically for inference performance logging."""
    return get_logger("inference_performance")


def log_inference_start(
    logger: logging.Logger,
    model_id: str,
    total_batches: int
) -> InferencePerformanceLog:
    """
    Log the start of an inference run for a specific model.
    
    Args:
        logger: Logger instance to use
        model_id: Identifier for the model being run
        total_batches: Expected number of batches
        
    Returns:
        InferencePerformanceLog entry for the start event
    """
    log_entry = InferencePerformanceLog(
        timestamp=datetime.now().isoformat(),
        model_id=model_id,
        event_type='start',
        batch_index=0,
        batch_size=0,
        ram_mb_current=0.0,
        ram_mb_peak=0.0,
        cpu_percent=0.0
    )
    
    logger.info(f"Inference started for model: {model_id}, total_batches: {total_batches}")
    return log_entry


def log_inference_batch(
    logger: logging.Logger,
    model_id: str,
    batch_index: int,
    batch_size: int,
    latency_ms: float,
    ram_mb_current: float,
    ram_mb_peak: float
) -> InferencePerformanceLog:
    """
    Log the completion of a single inference batch.
    
    Args:
        logger: Logger instance to use
        model_id: Identifier for the model being run
        batch_index: Index of the current batch (0-based)
        batch_size: Number of samples in this batch
        latency_ms: Time taken to process this batch in milliseconds
        ram_mb_current: Current RAM usage in MB
        ram_mb_peak: Peak RAM usage so far in MB
        
    Returns:
        InferencePerformanceLog entry for the batch event
    """
    throughput = (batch_size / latency_ms * 1000) if latency_ms > 0 else 0.0
    
    log_entry = InferencePerformanceLog(
        timestamp=datetime.now().isoformat(),
        model_id=model_id,
        event_type='batch',
        batch_index=batch_index,
        batch_size=batch_size,
        latency_ms=latency_ms,
        throughput_samples_per_sec=throughput,
        ram_mb_current=ram_mb_current,
        ram_mb_peak=ram_mb_peak
    )
    
    logger.debug(
        f"Batch {batch_index} completed for {model_id}: "
        f"size={batch_size}, latency={latency_ms:.2f}ms, "
        f"ram={ram_mb_current:.1f}MB (peak={ram_mb_peak:.1f}MB), "
        f"throughput={throughput:.2f} samples/sec"
    )
    return log_entry


def log_inference_summary(
    logger: logging.Logger,
    model_id: str,
    total_batches: int,
    total_samples: int,
    total_latency_ms: float,
    peak_ram_mb: float
) -> InferencePerformanceLog:
    """
    Log the summary of a complete inference run.
    
    Args:
        logger: Logger instance to use
        model_id: Identifier for the model being run
        total_batches: Total number of batches processed
        total_samples: Total number of samples processed
        total_latency_ms: Total time taken for all batches in milliseconds
        peak_ram_mb: Peak RAM usage during the run in MB
        
    Returns:
        InferencePerformanceLog entry for the summary event
    """
    total_latency_sec = total_latency_ms / 1000.0
    avg_throughput = (total_samples / total_latency_sec) if total_latency_sec > 0 else 0.0
    
    log_entry = InferencePerformanceLog(
        timestamp=datetime.now().isoformat(),
        model_id=model_id,
        event_type='summary',
        batch_index=total_batches,
        batch_size=0,
        latency_ms=total_latency_ms,
        throughput_samples_per_sec=avg_throughput,
        ram_mb_peak=peak_ram_mb
    )
    
    logger.info(
        f"Inference summary for {model_id}: "
        f"batches={total_batches}, samples={total_samples}, "
        f"total_time={total_latency_sec:.2f}s, "
        f"peak_ram={peak_ram_mb:.1f}MB, "
        f"avg_throughput={avg_throughput:.2f} samples/sec"
    )
    return log_entry


def get_resource_usage_detailed() -> Tuple[float, float, float]:
    """
    Get detailed resource usage metrics.
    
    Returns:
        Tuple of (current_ram_mb, peak_ram_mb, cpu_percent)
    """
    process = psutil.Process(os.getpid())
    
    # Get current RAM usage in MB
    current_ram_mb = process.memory_info().rss / (1024 * 1024)
    
    # Get peak RAM usage (if tracemalloc is started)
    peak_ram_mb = 0.0
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        peak_ram_mb = peak / (1024 * 1024)
    
    # Get CPU percent
    cpu_percent = process.cpu_percent(interval=0.1)
    
    return current_ram_mb, peak_ram_mb, cpu_percent


def log_resource_usage_detailed(
    logger: logging.Logger,
    model_id: str,
    context: str = "inference"
) -> InferencePerformanceLog:
    """
    Log detailed resource usage at a specific point in time.
    
    Args:
        logger: Logger instance to use
        model_id: Identifier for the model being run
        context: Context label for the resource check (e.g., 'inference', 'preprocessing')
        
    Returns:
        InferencePerformanceLog entry for the resource usage event
    """
    current_ram_mb, peak_ram_mb, cpu_percent = get_resource_usage_detailed()
    
    log_entry = InferencePerformanceLog(
        timestamp=datetime.now().isoformat(),
        model_id=model_id,
        event_type='resource',
        batch_index=None,
        batch_size=None,
        ram_mb_current=current_ram_mb,
        ram_mb_peak=peak_ram_mb,
        cpu_percent=cpu_percent
    )
    
    logger.debug(
        f"Resource usage for {model_id} ({context}): "
        f"current_ram={current_ram_mb:.1f}MB, "
        f"peak_ram={peak_ram_mb:.1f}MB, "
        f"cpu={cpu_percent:.1f}%"
    )
    return log_entry


def log_constraint_check(
    logger: logging.Logger,
    model_id: str,
    peak_ram_mb: float,
    total_latency_ms: float,
    time_limit_seconds: float = 21600.0,  # 6 hours default
    ram_limit_gb: float = 7.0  # 7 GB default
) -> InferencePerformanceLog:
    """
    Log a check against project resource constraints (FR-004, SC-002).
    
    Args:
        logger: Logger instance to use
        model_id: Identifier for the model being run
        peak_ram_mb: Peak RAM usage in MB
        total_latency_ms: Total inference time in milliseconds
        time_limit_seconds: Allowed time limit in seconds (default: 6 hours)
        ram_limit_gb: Allowed RAM limit in GB (default: 7 GB)
        
    Returns:
        InferencePerformanceLog entry with constraint check results
    """
    ram_limit_mb = ram_limit_gb * 1024
    total_latency_seconds = total_latency_ms / 1000.0
    
    ram_ok = peak_ram_mb <= ram_limit_mb
    time_ok = total_latency_seconds <= time_limit_seconds
    constraint_pass = ram_ok and time_ok
    
    details_parts = []
    if not ram_ok:
        details_parts.append(f"RAM exceeded: {peak_ram_mb:.1f}MB > {ram_limit_mb:.1f}MB")
    if not time_ok:
        details_parts.append(f"Time exceeded: {total_latency_seconds:.1f}s > {time_limit_seconds:.1f}s")
    constraint_details = "; ".join(details_parts) if not constraint_pass else "All constraints met"
    
    log_entry = InferencePerformanceLog(
        timestamp=datetime.now().isoformat(),
        model_id=model_id,
        event_type='constraint_check',
        batch_index=None,
        batch_size=None,
        ram_mb_current=peak_ram_mb,
        ram_mb_peak=peak_ram_mb,
        latency_ms=total_latency_ms,
        constraint_pass=constraint_pass,
        constraint_details=constraint_details
    )
    
    status = "PASS" if constraint_pass else "FAIL"
    logger.info(
        f"Constraint check for {model_id}: {status} - {constraint_details}"
    )
    return log_entry


def create_performance_log_entry(
    model_id: str,
    event_type: str,
    **kwargs
) -> InferencePerformanceLog:
    """
    Create a custom performance log entry with flexible parameters.
    
    Args:
        model_id: Identifier for the model
        event_type: Type of event (start, batch, summary, resource, constraint_check)
        **kwargs: Additional fields to include in the log entry
        
    Returns:
        InferencePerformanceLog entry
    """
    return InferencePerformanceLog(
        timestamp=datetime.now().isoformat(),
        model_id=model_id,
        event_type=event_type,
        **kwargs
    )


def save_performance_log(log_entry: InferencePerformanceLog, output_path: Path) -> None:
    """
    Save a single performance log entry to a JSON file (append mode).
    
    Args:
        log_entry: The log entry to save
        output_path: Path to the JSON file
    """
    log_entry_dict = asdict(log_entry)
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to file
    file_exists = output_path.exists()
    with open(output_path, 'a', encoding='utf-8') as f:
        if file_exists and os.path.getsize(output_path) > 0:
            f.write('\n')
        json.dump(log_entry_dict, f)
        f.write('\n')


def save_performance_logs_batch(
    log_entries: List[InferencePerformanceLog],
    output_path: Path
) -> None:
    """
    Save a batch of performance log entries to a JSON Lines file.
    
    Args:
        log_entries: List of log entries to save
        output_path: Path to the JSON Lines file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'a', encoding='utf-8') as f:
        for entry in log_entries:
            json.dump(asdict(entry), f)
            f.write('\n')

def main():
    """
    Main function to demonstrate logging utilities.
    This is typically called by inference runners to log performance.
    """
    # Setup logging
    setup_logging()
    logger = get_logger_for_inference()
    
    # Get config
    path_config = get_path_config()
    resource_limits = get_resource_limits()
    
    # Example: Simulate an inference run logging
    model_id = "test_model_quant8"
    log_path = path_config.data_processed_dir / "inference_performance_logs.jsonl"
    
    # Start logging
    logger.info("Starting inference performance logging demo...")
    
    start_log = log_inference_start(logger, model_id, total_batches=3)
    save_performance_log(start_log, log_path)
    
    # Simulate batches
    for i in range(3):
        # Simulate processing time
        time.sleep(0.1)
        current_ram, peak_ram, cpu = get_resource_usage_detailed()
        latency = 100.0 + (i * 10)  # Simulated latency
        
        batch_log = log_inference_batch(
            logger, model_id, i, batch_size=32,
            latency_ms=latency,
            ram_mb_current=current_ram,
            ram_mb_peak=peak_ram
        )
        save_performance_log(batch_log, log_path)
    
    # Summary
    summary_log = log_inference_summary(
        logger, model_id, total_batches=3, total_samples=96,
        total_latency_ms=330.0, peak_ram_mb=1500.0
    )
    save_performance_log(summary_log, log_path)
    
    # Constraint check
    constraint_log = log_constraint_check(
        logger, model_id, peak_ram_mb=1500.0,
        total_latency_ms=330.0,
        time_limit_seconds=resource_limits.get('time_limit_seconds', 21600.0),
        ram_limit_gb=resource_limits.get('ram_limit_gb', 7.0)
    )
    save_performance_log(constraint_log, log_path)
    
    logger.info(f"Performance logs saved to: {log_path}")

if __name__ == "__main__":
    main()