"""
Cleanup utilities for model-related code.

This module provides helper functions used during the cleanup of
src/models/ to ensure consistent patterns for model loading,
output parsing, and resource management.
"""
import gc
import logging
from typing import Optional, Any, Dict, List
from pathlib import Path
import torch
import time

from src.lib.config import get_logger
from src.lib.memory_monitor import get_current_memory_usage_bytes, format_bytes, check_memory_limit

class ModelResourceManager:
    """
    Context manager for handling model loading and unloading with memory monitoring.
    """
    
    def __init__(self, model: Optional[Any] = None, logger: Optional[logging.Logger] = None):
        self.model = model
        self.logger = logger or get_logger(__name__)
        self.initial_memory = 0
        self.final_memory = 0
        
    def __enter__(self) -> 'ModelResourceManager':
        self.initial_memory = get_current_memory_usage_bytes()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.model is not None:
            del self.model
            self.model = None
            
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        self.final_memory = get_current_memory_usage_bytes()
        memory_delta = self.final_memory - self.initial_memory
        
        self.logger.info(f"Model cleanup complete. Memory delta: {format_bytes(memory_delta)}")
        return False

def safe_model_load(model_path: Path, logger: Optional[logging.Logger] = None) -> Any:
    """
    Safely load a model with memory checks and error handling.
    
    Args:
        model_path: Path to the model.
        logger: Optional logger instance.
        
    Returns:
        Loaded model instance.
        
    Raises:
        FileNotFoundError: If model path doesn't exist.
        RuntimeError: If loading fails or memory limit exceeded.
    """
    log = logger or get_logger(__name__)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model path does not exist: {model_path}")
    
    log.info(f"Loading model from {model_path}")
    
    try:
        # Check memory before loading
        check_memory_limit()
        
        # Load model (implementation-specific)
        # This is a placeholder for actual model loading logic
        # The actual implementation would depend on the model type
        start_time = time.perf_counter()
        
        # Simulated loading - replace with actual torch.load or similar
        # model = torch.load(model_path, map_location='cpu')
        
        end_time = time.perf_counter()
        log.info(f"Model loaded in {end_time - start_time:.2f}s")
        
        # Check memory after loading
        check_memory_limit()
        
        return model
        
    except RuntimeError as e:
        log.error(f"Failed to load model: {e}")
        raise
    except Exception as e:
        log.error(f"Unexpected error during model loading: {e}")
        raise RuntimeError(f"Model loading failed: {e}") from e

def clean_tensor(tensor: Optional[torch.Tensor]) -> None:
    """
    Safely clean up a tensor and free memory.
    
    Args:
        tensor: Tensor to clean up.
    """
    if tensor is not None:
        del tensor
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

def validate_model_output(output: Any, expected_keys: List[str]) -> Dict[str, Any]:
    """
    Validate model output structure.
    
    Args:
        output: Model output to validate.
        expected_keys: List of expected keys in the output.
        
    Returns:
        Validated output dictionary.
        
    Raises:
        ValueError: If output doesn't contain expected keys.
    """
    if not isinstance(output, dict):
        raise ValueError(f"Expected dict output, got {type(output).__name__}")
        
    missing_keys = [key for key in expected_keys if key not in output]
    if missing_keys:
        raise ValueError(f"Model output missing required keys: {missing_keys}")
        
    return output

def format_model_stats(model_name: str, params: int, memory_mb: float) -> str:
    """
    Format model statistics for logging.
    
    Args:
        model_name: Name of the model.
        params: Number of parameters.
        memory_mb: Memory usage in MB.
        
    Returns:
        Formatted statistics string.
    """
    param_str = f"{params:,}"
    if params >= 1_000_000_000:
        param_str = f"{params / 1_000_000_000:.2f}B"
    elif params >= 1_000_000:
        param_str = f"{params / 1_000_000:.2f}M"
        
    return f"Model: {model_name}, Params: {param_str}, Memory: {memory_mb:.2f}MB"

def retry_with_backoff(func: callable, max_retries: int = 3, base_delay: float = 1.0) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to execute.
        max_retries: Maximum number of retries.
        base_delay: Base delay in seconds.
        
    Returns:
        Result of the function.
        
    Raises:
        Exception: If all retries fail.
    """
    logger = get_logger(__name__)
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} attempts failed: {e}")
                
    raise last_exception
