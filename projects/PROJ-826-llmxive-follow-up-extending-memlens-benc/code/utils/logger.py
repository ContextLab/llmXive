"""
Logging infrastructure for the MemLens benchmark pipeline.

Configures structured logging to track detection_status, fallback events,
and resource usage across the pipeline.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure the utils directory is treated as a package if imported directly
# though typically this will be imported via code.utils.logger
try:
    from code.utils import __init__ as utils_init
except ImportError:
    pass

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file paths
LOG_DIR = Path("projects/PROJ-826-llmxive-follow-up-extending-memlens-benc/logs")
LOG_FILE = LOG_DIR / "pipeline.log"
DETECTION_LOG_FILE = LOG_DIR / "detection_events.log"

# Global logger instance
_pipeline_logger: Optional[logging.Logger] = None
_detection_logger: Optional[logging.Logger] = None

def _ensure_log_dirs() -> None:
    """Create log directories if they do not exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "memlens_pipeline") -> logging.Logger:
    """
    Retrieve or create the main pipeline logger.
    
    Args:
        name: The name for the logger (default: 'memlens_pipeline')
    
    Returns:
        Configured logging.Logger instance
    """
    global _pipeline_logger
    if _pipeline_logger is None:
        _ensure_log_dirs()
        _pipeline_logger = logging.getLogger(name)
        _pipeline_logger.setLevel(DEFAULT_LOG_LEVEL)
        
        if not _pipeline_logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(DEFAULT_LOG_LEVEL)
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            _pipeline_logger.addHandler(console_handler)
            
            # File handler
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            _pipeline_logger.addHandler(file_handler)
    
    return _pipeline_logger

def get_detection_logger() -> logging.Logger:
    """
    Retrieve or create the dedicated detection logger.
    
    This logger specifically tracks YOLO detection events, including
    success, zero_detection, and fallback statuses.
    
    Returns:
        Configured logging.Logger instance for detection events
    """
    global _detection_logger
    if _detection_logger is None:
        _ensure_log_dirs()
        _detection_logger = logging.getLogger("memlens_detection")
        _detection_logger.setLevel(logging.INFO)
        
        if not _detection_logger.handlers:
            # File handler for detection events only
            file_handler = logging.FileHandler(DETECTION_LOG_FILE)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s", DATE_FORMAT
            ))
            _detection_logger.addHandler(file_handler)
            
            # Also log to main pipeline log
            main_logger = get_logger()
            _detection_logger.addHandler(main_logger.handlers[0])  # Console handler
    
    return _detection_logger

def log_detection_status(
    sample_id: str,
    status: str,
    object_count: int = 0,
    fallback_reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a detection event with structured details.
    
    Args:
        sample_id: Unique identifier for the dataset sample
        status: One of 'success', 'zero_detection', 'fallback'
        object_count: Number of objects detected (0 if none)
        fallback_reason: Reason for fallback if status is 'fallback'
        metadata: Additional key-value pairs for context
    """
    logger = get_detection_logger()
    
    base_msg = f"Sample {sample_id}: status={status}, objects={object_count}"
    if fallback_reason:
        base_msg += f", reason={fallback_reason}"
    
    if metadata:
        meta_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
        base_msg += f", meta={{{meta_str}}}"
    
    if status == "fallback":
        logger.warning(base_msg)
    elif status == "zero_detection":
        logger.info(base_msg)
    else:
        logger.info(base_msg)

def log_fallback_event(
    sample_id: str,
    component: str,
    reason: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a fallback event for any pipeline component.
    
    Args:
        sample_id: Unique identifier for the dataset sample
        component: Name of the component failing (e.g., 'YOLOv8', 'LLM')
        reason: Human-readable reason for the fallback
        details: Additional technical details
    """
    logger = get_logger()
    msg = f"FALLBACK: Sample {sample_id} - Component: {component}, Reason: {reason}"
    if details:
        msg += f" | Details: {details}"
    logger.warning(msg)

def log_resource_usage(
    sample_id: str,
    component: str,
    peak_ram_mb: Optional[float] = None,
    cpu_time_sec: Optional[float] = None,
    latency_sec: Optional[float] = None
) -> None:
    """
    Log resource usage metrics for a specific component.
    
    Args:
        sample_id: Unique identifier for the dataset sample
        component: Name of the component (e.g., 'YOLOv8', 'Phi-3')
        peak_ram_mb: Peak RAM usage in MB
        cpu_time_sec: CPU time consumed in seconds
        latency_sec: Total latency in seconds
    """
    logger = get_logger()
    parts = [f"Resource: Sample {sample_id} - Component: {component}"]
    if peak_ram_mb is not None:
        parts.append(f"RAM: {peak_ram_mb:.2f}MB")
    if cpu_time_sec is not None:
        parts.append(f"CPU Time: {cpu_time_sec:.2f}s")
    if latency_sec is not None:
        parts.append(f"Latency: {latency_sec:.2f}s")
    logger.debug(" | ".join(parts))

def log_preprocessing_step(
    step_name: str,
    sample_count: int,
    details: Optional[str] = None
) -> None:
    """
    Log progress of preprocessing steps.
    
    Args:
        step_name: Name of the preprocessing step
        sample_count: Number of samples processed
        details: Optional additional details
    """
    logger = get_logger()
    msg = f"Preprocessing: {step_name} - Processed {sample_count} samples"
    if details:
        msg += f" | {details}"
    logger.info(msg)

def log_retrieval_results(
    query_id: str,
    strategy: str,
    top_k: int,
    retrieved_ids: list,
    avg_similarity: float
) -> None:
    """
    Log retrieval results for a query.
    
    Args:
        query_id: Unique identifier for the query
        strategy: Retrieval strategy used (Coarse, Medium, Fine)
        top_k: Number of items retrieved
        retrieved_ids: List of retrieved sample IDs
        avg_similarity: Average similarity score of retrieved items
    """
    logger = get_logger()
    ids_str = ", ".join(retrieved_ids[:3]) + "..." if len(retrieved_ids) > 3 else ", ".join(retrieved_ids)
    msg = (
        f"Retrieval: Query {query_id} - Strategy: {strategy}, "
        f"K={top_k}, AvgSim={avg_similarity:.4f}, IDs=[{ids_str}]"
    )
    logger.debug(msg)

def log_inference_start(
    sample_id: str,
    model_name: str,
    strategy: str
) -> None:
    """
    Log the start of an inference step.
    
    Args:
        sample_id: Unique identifier for the sample
        model_name: Name of the model being used
        strategy: Memory strategy (Coarse, Medium, Fine)
    """
    logger = get_logger()
    logger.info(f"Inference Start: Sample {sample_id} - Model: {model_name}, Strategy: {strategy}")

def log_inference_end(
    sample_id: str,
    success: bool,
    error_message: Optional[str] = None
) -> None:
    """
    Log the end of an inference step.
    
    Args:
        sample_id: Unique identifier for the sample
        success: Whether inference completed successfully
        error_message: Error message if failed
    """
    logger = get_logger()
    if success:
        logger.info(f"Inference End: Sample {sample_id} - Success")
    else:
        logger.error(f"Inference End: Sample {sample_id} - Failed: {error_message}")

# Convenience function to get all log file paths
def get_log_paths() -> Dict[str, str]:
    """
    Return paths to all log files generated by this module.
    
    Returns:
        Dictionary mapping log type to file path
    """
    _ensure_log_dirs()
    return {
        "pipeline": str(LOG_FILE),
        "detection": str(DETECTION_LOG_FILE)
    }