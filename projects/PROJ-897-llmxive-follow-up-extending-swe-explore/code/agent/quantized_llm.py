"""
Quantized Model Orchestration for llmXive.

This module implements the loading of a quantized LLM (e.g., Qwen-1.5B) using
bitsandbytes for 8-bit precision. It includes memory monitoring and offload
logic to gracefully handle memory constraints by signaling the execution
environment to switch to a GPU-enabled runner.
"""

import json
import sys
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

import psutil
import torch

# Import configuration constants from the project root
# Assuming config.py is in the root of 'code/' or accessible via PYTHONPATH
try:
    from config import get_path, get_config_summary, MODEL_PRECISION, MAX_RUNTIME_HOURS
except ImportError:
    from code.config import get_path, get_config_summary, MODEL_PRECISION, MAX_RUNTIME_HOURS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MEMORY_THRESHOLD_GB = 6.0
OFFLOAD_FLAG_FILENAME = "gpu_offload_request.json"
OFFLOAD_FLAG_DIR = "data/results"

# Default model configuration (can be overridden via CLI or env)
DEFAULT_MODEL_NAME = "Qwen/Qwen1.5-1.8B-Chat"
TARGET_DEVICE = "cpu"

def check_process_memory() -> float:
    """
    Checks the current process's memory usage in GB.
    
    Returns:
        float: Memory usage in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_gb = mem_info.rss / (1024 ** 3)
    logger.info(f"Current process RSS memory usage: {mem_gb:.2f} GB")
    return mem_gb

def request_gpu_offload(reason: str) -> bool:
    """
    Writes a flag to disk requesting the execution environment to switch to GPU.
    
    Args:
        reason: A string explaining why the offload is requested.
        
    Returns:
        bool: True if the flag was written successfully.
    """
    try:
        # Ensure the directory exists
        offload_dir = get_path(OFFLOAD_FLAG_DIR)
        Path(offload_dir).mkdir(parents=True, exist_ok=True)
        
        flag_path = Path(offload_dir) / OFFLOAD_FLAG_FILENAME
        
        payload = {
            "request_type": "gpu_offload",
            "reason": reason,
            "timestamp": "auto", # Will be replaced or left as is
            "requested_by": "T043_quantized_llm"
        }
        
        with open(flag_path, 'w') as f:
            json.dump(payload, f, indent=2)
        
        logger.info(f"GPU offload request written to {flag_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write GPU offload request: {e}")
        return False

def load_quantized_model(
    model_name: Optional[str] = None,
    precision: Optional[str] = None
) -> Optional[Any]:
    """
    Loads a quantized model using bitsandbytes.
    
    Args:
        model_name: HuggingFace model ID. Defaults to Qwen-1.8B if not provided.
        precision: Precision string (e.g., '8-bit'). Defaults to config value.
        
    Returns:
        The loaded model if successful, None if offload is requested.
        
    Raises:
        RuntimeError: If the model cannot be loaded and offload is not requested.
    """
    model_name = model_name or DEFAULT_MODEL_NAME
    precision = precision or MODEL_PRECISION

    logger.info(f"Attempting to load model: {model_name} with precision: {precision}")

    # Check memory before loading
    current_mem = check_process_memory()
    
    if current_mem > MEMORY_THRESHOLD_GB:
        logger.warning(
            f"Memory usage ({current_mem:.2f} GB) exceeds threshold ({MEMORY_THRESHOLD_GB} GB). "
            f"Requesting GPU offload."
        )
        request_gpu_offload(
            reason=f"Process memory {current_mem:.2f}GB exceeds {MEMORY_THRESHOLD_GB}GB limit for CPU quantization."
        )
        return None

    try:
        # Import transformers inside try block to handle missing deps gracefully if needed
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        # Configure 8-bit quantization
        if precision == '8-bit':
            bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False
            )
        else:
            # Fallback to standard loading if 8-bit is not requested or supported
            bnb_config = None

        logger.info("Initializing tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        logger.info("Initializing model with quantization config...")
        
        if bnb_config:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto", # Let bitsandbytes handle device mapping
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                trust_remote_code=True
            )

        logger.info("Model loaded successfully.")
        
        # Final memory check
        final_mem = check_process_memory()
        logger.info(f"Memory usage after loading: {final_mem:.2f} GB")
        
        return model, tokenizer

    except ImportError as e:
        logger.error(f"Missing dependency for quantized loading: {e}")
        logger.error("Please ensure 'bitsandbytes' and 'transformers' are installed.")
        raise RuntimeError(f"Quantized loading failed due to missing dependencies: {e}")
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        # If we are already high on memory, we might have triggered the offload flag above,
        # but if we failed here for another reason, we should not silently succeed.
        raise RuntimeError(f"Model loading failed: {e}")

def main():
    """
    Main entry point for testing the quantized model loader.
    This function is designed to be run as a script to verify the offload logic.
    """
    logger.info("Starting Quantized Model Orchestration check (T043).")
    
    # Check if offload flag already exists (idempotency check)
    offload_dir = get_path(OFFLOAD_FLAG_DIR)
    flag_path = Path(offload_dir) / OFFLOAD_FLAG_FILENAME
    if flag_path.exists():
        logger.warning(f"Offload flag already exists at {flag_path}. Skipping load.")
        return

    try:
        model, tokenizer = load_quantized_model()
        if model is None:
            logger.info("Model loading returned None (Offload requested). Exiting gracefully.")
            sys.exit(0)
        
        logger.info("Model loaded successfully. Test passed.")
        # Simple inference test to ensure model is usable
        input_text = "Hello, how are you?"
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=10)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Test response: {response}")
        
    except RuntimeError as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
