import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from memory_profiler import profile
import psutil
import traceback

from config import get_config_dict

def setup_query_logger(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Sets up a dedicated logger for query execution logs.
    Logs are written to data/logs/query_performance.log.
    """
    config = get_config_dict()
    if log_dir is None:
        log_dir = Path(config.get('paths', {}).get('logs', 'data/logs'))
    
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "query_performance.log"

    logger = logging.getLogger("query_performance")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates in repeated calls
    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def get_memory_usage_mb() -> float:
    """
    Returns current memory usage of the process in MB.
    Uses psutil for cross-platform compatibility.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def log_query_execution(
    query_id: str,
    duration_seconds: float,
    memory_start_mb: float,
    memory_end_mb: float,
    status: str,
    error_msg: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Logs runtime and memory metrics for a single query execution.
    
    Args:
        query_id: Unique identifier for the query
        duration_seconds: Total time taken in seconds
        memory_start_mb: Memory at start of query
        memory_end_mb: Memory at end of query
        status: 'success' or 'failure'
        error_msg: Error message if status is failure
        logger: Logger instance (creates one if None)
    
    Returns:
        Dictionary containing the logged metrics
    """
    if logger is None:
        logger = setup_query_logger()

    memory_delta = memory_end_mb - memory_start_mb
    
    log_entry = {
        "query_id": query_id,
        "duration_seconds": round(duration_seconds, 4),
        "memory_start_mb": round(memory_start_mb, 2),
        "memory_end_mb": round(memory_end_mb, 2),
        "memory_delta_mb": round(memory_delta, 2),
        "status": status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if status == "failure" and error_msg:
        log_entry["error"] = error_msg
        logger.error(f"Query {query_id} failed: {error_msg}")
    else:
        logger.info(f"Query {query_id} completed in {duration_seconds:.2f}s "
                  f"(Mem: {memory_start_mb:.1f}MB -> {memory_end_mb:.1f}MB)")

    return log_entry

def log_batch_summary(
    total_queries: int,
    successful_queries: int,
    failed_queries: int,
    avg_duration: float,
    avg_memory_start: float,
    avg_memory_end: float,
    max_memory_observed: float,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Logs a summary of batch execution performance.
    """
    if logger is None:
        logger = setup_query_logger()

    summary = {
        "total_queries": total_queries,
        "successful_queries": successful_queries,
        "failed_queries": failed_queries,
        "success_rate": round(successful_queries / total_queries, 4) if total_queries > 0 else 0,
        "avg_duration_seconds": round(avg_duration, 4),
        "avg_memory_start_mb": round(avg_memory_start, 2),
        "avg_memory_end_mb": round(avg_memory_end, 2),
        "max_memory_observed_mb": round(max_memory_observed, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    logger.info(f"BATCH SUMMARY: {total_queries} queries, "
              f"Success: {summary['success_rate']*100:.1f}%, "
              f"Avg Duration: {summary['avg_duration_seconds']:.2f}s, "
              f"Max Mem: {summary['max_memory_observed_mb']:.1f}MB")

    return summary

def profile_and_log_query(
    query_id: str,
    query_func,
    *args,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> tuple:
    """
    Decorator-like wrapper to profile a query function and log results.
    
    Args:
        query_id: Unique identifier for the query
        query_func: The function to execute and profile
        *args, **kwargs: Arguments to pass to query_func
        logger: Optional logger instance
    
    Returns:
        Tuple of (result, log_entry_dict)
    """
    if logger is None:
        logger = setup_query_logger()

    memory_start = get_memory_usage_mb()
    start_time = time.time()
    
    try:
        result = query_func(*args, **kwargs)
        duration = time.time() - start_time
        memory_end = get_memory_usage_mb()
        
        log_entry = log_query_execution(
            query_id=query_id,
            duration_seconds=duration,
            memory_start_mb=memory_start,
            memory_end_mb=memory_end,
            status="success",
            logger=logger
        )
        
        return result, log_entry
        
    except Exception as e:
        duration = time.time() - start_time
        memory_end = get_memory_usage_mb()
        
        log_entry = log_query_execution(
            query_id=query_id,
            duration_seconds=duration,
            memory_start_mb=memory_start,
            memory_end_mb=memory_end,
            status="failure",
            error_msg=str(e),
            logger=logger
        )
        
        raise e
