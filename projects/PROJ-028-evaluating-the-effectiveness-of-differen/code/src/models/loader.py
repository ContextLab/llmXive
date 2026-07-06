"""
Model loader with RAM monitoring and automatic precision switching.
Implements FR-002: FP32 default, automatic reload to FP16 if RAM > 6.5GB.
"""

import gc
import psutil
import os
from typing import Optional, Dict, Any
from pathlib import Path

from src.utils.logging import ResourceLogger

# Global state for model
_current_model = None
_current_precision = "fp32"
_model_path = None

def get_current_ram_usage_gb() -> float:
    """
    Returns the current RAM usage of the process in GB.
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / (1024 ** 3)

def load_model(model_path: Optional[str] = None, precision: str = "fp32") -> Any:
    """
    Loads the model with the specified precision.
    If RAM is high, it may automatically switch to FP16 if requested or allowed.
    
    Args:
        model_path: Path to the model. If None, uses a default or cached model.
        precision: "fp32" or "fp16".
    
    Returns:
        The loaded model object (or a mock for this implementation).
    """
    global _current_model, _current_precision, _model_path
    
    logger = ResourceLogger()
    current_ram = get_current_ram_usage_gb()
    
    if current_ram > 6.5:
        logger.log_resource("RAM_HIGH_BEFORE_LOAD", {
            "current_ram_gb": current_ram,
            "requested_precision": precision
        })
        
        # If we are asked for FP32 but RAM is high, try FP16
        if precision == "fp32":
            logger.log_resource("AUTO_SWITCH_TO_FP16", {
                "reason": "RAM exceeded 6.5GB threshold"
            })
            precision = "fp16"
        else:
            # If already FP16 and RAM is high, we might need to unload others or fail
            logger.log_resource("RAM_CRITICAL", {
                "current_ram_gb": current_ram
            })
            # In a real scenario, we might raise an error or force GC
            gc.collect()
            if get_current_ram_usage_gb() > 6.5:
                raise MemoryError(f"Cannot load model. RAM usage {get_current_ram_usage_gb():.2f}GB exceeds limit.")
    
    _current_precision = precision
    _model_path = model_path or "default_model_path"
    
    # Simulate model loading
    # In a real implementation, this would be:
    # from transformers import AutoModelForCausalLM
    # model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16 if precision == "fp16" else torch.float32)
    
    _current_model = {
        "path": _model_path,
        "precision": precision,
        "status": "loaded"
    }
    
    logger.log_resource("MODEL_LOADED", {
        "path": _model_path,
        "precision": precision,
        "ram_after_load_gb": get_current_ram_usage_gb()
    })
    
    return _current_model

def unload_model() -> None:
    """
    Unloads the current model and triggers garbage collection.
    """
    global _current_model
    
    logger = ResourceLogger()
    
    if _current_model is not None:
        logger.log_resource("MODEL_UNLOADING", {
            "precision": _current_precision,
            "ram_before_unload_gb": get_current_ram_usage_gb()
        })
        
        _current_model = None
        gc.collect()
        
        logger.log_resource("MODEL_UNLOADED", {
            "ram_after_unload_gb": get_current_ram_usage_gb()
        })
    else:
        logger.log_resource("MODEL_UNLOAD_SKIPPED", {
            "reason": "No model loaded"
        })

def get_current_model() -> Optional[Any]:
    """Returns the currently loaded model instance."""
    return _current_model
