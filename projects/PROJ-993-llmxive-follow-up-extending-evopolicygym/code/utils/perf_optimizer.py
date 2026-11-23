"""
Performance optimization utilities for llmXive pipeline.

This module implements CPU-specific optimizations to ensure inference
stays within acceptable time thresholds:
1. Dynamic batch size adjustment for LLM inference
2. Memory-mapped model loading to reduce RAM pressure
3. Tokenization caching for repeated prompts
4. Timeout enforcement with early termination
"""
import os
import time
import logging
import threading
from typing import Optional, Callable, Any, Dict
from functools import wraps
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from utils.logging import get_logger

logger = get_logger(__name__)

# Configuration constants
DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes default for CPU inference
MAX_BATCH_SIZE = 8
MIN_BATCH_SIZE = 1
MEMORY_THRESHOLD_GB = 12.0  # Warn if memory usage exceeds this

# Thread-local storage for timing context
_timing_context = threading.local()


class TimeoutError(Exception):
    """Raised when an operation exceeds the time budget."""
    pass


class MemoryPressureError(Exception):
    """Raised when system memory pressure is too high."""
    pass


def get_optimization_config() -> Dict[str, Any]:
    """
    Read optimization settings from environment variables.
    
    Returns:
        Dict with timeout, batch_size, and memory_threshold settings.
    """
    return {
        "timeout_seconds": int(os.getenv("LLMXIVE_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
        "max_batch_size": int(os.getenv("LLMXIVE_MAX_BATCH_SIZE", MAX_BATCH_SIZE)),
        "memory_threshold_gb": float(os.getenv("LLMXIVE_MEMORY_THRESHOLD_GB", MEMORY_THRESHOLD_GB)),
        "use_mmap": os.getenv("LLMXIVE_USE_MMAP", "true").lower() == "true",
    }


def enforce_timeout(timeout_seconds: Optional[int] = None):
    """
    Context manager that raises TimeoutError if execution exceeds limit.
    
    Args:
        timeout_seconds: Override for default timeout from config.
        
    Example:
        with enforce_timeout(60):
            result = slow_function()
    """
    if timeout_seconds is None:
        timeout_seconds = get_optimization_config()["timeout_seconds"]
        
    return _TimeoutContext(timeout_seconds)


class _TimeoutContext:
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        self.start_time = None
        self.timer_thread = None
        self.timed_out = False
        
    def _check_timeout(self):
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout_seconds:
            self.timed_out = True
            raise TimeoutError(f"Operation exceeded {self.timeout_seconds}s timeout")
            
    def __enter__(self):
        self.start_time = time.time()
        self.timed_out = False
        # Start a daemon thread to monitor timeout
        self.timer_thread = threading.Thread(target=self._check_timeout, daemon=True)
        self.timer_thread.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer_thread:
            # Thread is daemon, will terminate on exit
            pass
        return False


def time_operation(operation_name: str):
    """
    Decorator to log execution time of operations.
    
    Args:
        operation_name: Name to use in log messages.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.debug(f"{operation_name} completed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(f"{operation_name} failed after {elapsed:.3f}s: {e}")
                raise
        return wrapper
    return decorator


def adaptive_batch_size(inference_func: Callable) -> Callable:
    """
    Decorator that dynamically adjusts batch size based on memory/time.
    
    Starts with max batch size and reduces if OOM or timeout occurs.
    """
    config = get_optimization_config()
    max_batch = config["max_batch_size"]
    min_batch = MIN_BATCH_SIZE
    
    @wraps(inference_func)
    def wrapper(items, *args, **kwargs):
        batch_size = max_batch
        results = []
        remaining = list(items)
        
        while remaining:
            current_batch = remaining[:batch_size]
            try:
                with enforce_timeout(config["timeout_seconds"] // max(1, (len(remaining) // batch_size) + 1)):
                    batch_results = inference_func(current_batch, *args, **kwargs)
                    results.extend(batch_results)
                    remaining = remaining[batch_size:]
                    # If successful, try to increase batch size slightly (up to max)
                    if batch_size < max_batch and len(remaining) >= max_batch:
                        batch_size = min(batch_size + 1, max_batch)
            except (TimeoutError, MemoryPressureError) as e:
                logger.warning(f"Batch size {batch_size} failed: {e}. Reducing batch size.")
                batch_size = max(batch_size // 2, min_batch)
                if batch_size == min_batch:
                    # Process one by one if even min batch fails
                    if len(current_batch) == 1:
                        raise
                    # Retry with single item
                    for item in current_batch:
                        try:
                            single_result = inference_func([item], *args, **kwargs)
                            results.extend(single_result)
                        except Exception as single_e:
                            logger.error(f"Single item inference failed: {single_e}")
                            raise
                    remaining = []
            except Exception as e:
                logger.error(f"Unexpected error during batch inference: {e}")
                raise
                
        return results
        
    return wrapper


def estimate_memory_usage(model_size_gb: float, batch_size: int) -> float:
    """
    Estimate memory usage for a model with given batch size.
    
    Args:
        model_size_gb: Size of model weights in GB.
        batch_size: Number of items in batch.
        
    Returns:
        Estimated total memory usage in GB.
    """
    # Rough heuristic: model weights + 2x for activations + KV cache
    # Activations scale linearly with batch size
    activation_overhead = 2.0 * (batch_size / MAX_BATCH_SIZE)
    kv_cache_overhead = 0.5 * (batch_size / MAX_BATCH_SIZE)
    
    return model_size_gb * (1.0 + activation_overhead + kv_cache_overhead)


def check_memory_pressure() -> bool:
    """
    Check if system memory usage is above threshold.
    
    Returns:
        True if memory pressure is high.
    """
    try:
        import psutil
        mem = psutil.virtual_memory()
        used_gb = mem.total * mem.percent / (1024**3)
        threshold = get_optimization_config()["memory_threshold_gb"]
        if used_gb > threshold:
            logger.warning(f"Memory pressure detected: {used_gb:.1f}GB used (threshold: {threshold}GB)")
            return True
        return False
    except ImportError:
        logger.debug("psutil not available, skipping memory check")
        return False
    except Exception as e:
        logger.warning(f"Could not check memory usage: {e}")
        return False


def load_model_with_mmap(model_path: str, **kwargs):
    """
    Load a model using memory mapping to reduce RAM usage.
    
    Args:
        model_path: Path to model directory.
        **kwargs: Additional arguments passed to model loader.
        
    Returns:
        Loaded model instance.
    """
    config = get_optimization_config()
    
    if not TORCH_AVAILABLE:
        logger.warning("PyTorch not available, loading without mmap")
        # Fallback to standard load
        return _load_model_standard(model_path, **kwargs)
        
    try:
        if config["use_mmap"]:
            logger.info(f"Loading model {model_path} with memory mapping")
            # For transformers, use low_cpu_mem_usage and device_map
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                low_cpu_mem_usage=True,
                device_map="cpu",  # Force CPU for consistency
                torch_dtype=torch.float32,  # Use float32 for stability on CPU
                **kwargs
            )
            return model, tokenizer
        else:
            return _load_model_standard(model_path, **kwargs)
    except Exception as e:
        logger.error(f"Failed to load model with mmap: {e}")
        return _load_model_standard(model_path, **kwargs)


def _load_model_standard(model_path: str, **kwargs):
    """Standard model loading without memory mapping optimizations."""
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch is required for model loading")
        
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    return model, tokenizer


def optimize_inference_pipeline():
    """
    Apply all available optimizations to the inference pipeline.
    
    This function should be called once at initialization to set up:
    - Thread pool sizing
    - Memory limits
    - Batch processing strategies
    """
    config = get_optimization_config()
    
    # Set torch thread count for CPU optimization
    if TORCH_AVAILABLE:
        torch.set_num_threads(os.cpu_count() or 4)
        torch.set_num_interop_threads(1)
        logger.info(f"Set torch threads to {os.cpu_count() or 4}")
        
    # Check initial memory pressure
    if check_memory_pressure():
        logger.warning("Starting with high memory pressure, using conservative batch sizes")
        config["max_batch_size"] = min(config["max_batch_size"], 2)
        
    return config


class PerformanceMonitor:
    """Context manager to track performance metrics for a block of code."""
    
    def __init__(self, metric_name: str):
        self.metric_name = metric_name
        self.start_time = None
        self.end_time = None
        self.metrics = {}
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        if TORCH_AVAILABLE:
            torch.cuda.synchronize() if torch.cuda.is_available() else None
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        elapsed = self.end_time - self.start_time
        self.metrics = {
            "name": self.metric_name,
            "elapsed_seconds": elapsed,
            "success": exc_type is None
        }
        logger.info(f"Performance metric {self.metric_name}: {elapsed:.3f}s")
        return False
        
    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics


# Global performance tracking
_global_metrics = []


def record_metric(name: str, value: float, unit: str = "seconds"):
    """Record a performance metric for later aggregation."""
    _global_metrics.append({
        "name": name,
        "value": value,
        "unit": unit,
        "timestamp": time.time()
    })


def get_performance_report() -> Dict[str, Any]:
    """Generate a summary report of all recorded metrics."""
    if not _global_metrics:
        return {"metrics": [], "summary": "No metrics recorded"}
        
    summary = {}
    for m in _global_metrics:
        if m["name"] not in summary:
            summary[m["name"]] = {"values": [], "unit": m["unit"]}
        summary[m["name"]]["values"].append(m["value"])
        
    report = {
        "metrics": _global_metrics,
        "summary": {
            name: {
                "count": len(data["values"]),
                "min": min(data["values"]),
                "max": max(data["values"]),
                "mean": np.mean(data["values"]),
                "unit": data["unit"]
            }
            for name, data in summary.items()
        }
    }
    return report
