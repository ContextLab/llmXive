"""
Inference module for llmXive pipeline.
Implements real-time timeout enforcement for LLM generation calls.
"""
import os
import sys
import time
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Import shared utilities and config
from config import get_config
from error_handling import InferenceTimeoutError
from data_models import ModelResponse

# Configure logging
logger = logging.getLogger(__name__)

# Ensure output directories exist
INTERIM_DIR = Path("data/interim")
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT_LOG_PATH = INTERIM_DIR / "timeout_failures.log"

def log_timeout_failure(prompt_id: str, duration: float, message: str) -> None:
    """Log a timeout failure to the designated log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    log_entry = f"[{timestamp}] PROMPT_ID={prompt_id} DURATION={duration:.2f}s | {message}\n"
    with open(TIMEOUT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)
    logger.warning(f"Timeout recorded: {prompt_id} -> {message}")

def generate_with_timeout(
    model: Any,
    prompt: str,
    timeout_seconds: float,
    prompt_id: str,
    **gen_kwargs
) -> Optional[str]:
    """
    Execute model generation with a hard timeout enforced via threading.
    
    This implementation uses a cross-platform approach compatible with Windows,
    Linux, and macOS by utilizing `threading.Timer` and a shared state container
    instead of Unix-specific `signal` modules which do not work across threads on Windows.
    
    Args:
        model: The llama-cpp-python model instance.
        prompt: The input prompt string.
        timeout_seconds: Maximum allowed time for generation.
        prompt_id: Unique identifier for logging.
        **gen_kwargs: Arguments passed to model.generate or model.create_completion.
    
    Returns:
        The generated text string if successful, None if timed out.
    
    Raises:
        InferenceTimeoutError: If the generation exceeds the timeout.
    """
    result_container = {"text": None, "error": None, "timed_out": False}
    generation_complete = threading.Event()
    
    def run_generation():
        try:
            # Attempt to generate using the standard llama-cpp API
            # Depending on the exact wrapper, this might be model(prompt, ...) or model.generate(...)
            # Assuming a standard completion interface:
            output = model(prompt, **gen_kwargs)
            
            # Handle different return types (dict vs object)
            if isinstance(output, dict):
                result_container["text"] = output.get("choices", [{}])[0].get("text", "")
            else:
                # Fallback for object-based returns
                result_container["text"] = str(output)
                
        except Exception as e:
            result_container["error"] = e
        finally:
            generation_complete.set()

    # Start the generation in a daemon thread
    thread = threading.Thread(target=run_generation)
    thread.daemon = True
    thread.start()
    
    # Wait for completion or timeout
    completed = generation_complete.wait(timeout=timeout_seconds)

    if not completed:
        # Timeout occurred
        result_container["timed_out"] = True
        msg = f"Generation exceeded {timeout_seconds}s limit."
        log_timeout_failure(prompt_id, timeout_seconds, msg)
        raise InferenceTimeoutError(
            f"Inference timed out for prompt {prompt_id} after {timeout_seconds}s"
        )

    if result_container["error"]:
        raise result_container["error"]

    return result_container["text"]

def run_inference_with_timeout(
    model: Any,
    prompt_item: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[ModelResponse], bool]:
    """
    Wrapper to run inference on a single prompt with timeout enforcement.
    
    Args:
        model: The loaded LLM model.
        prompt_item: Dictionary containing 'prompt_id' and 'text'.
        config: Configuration dictionary (optional, loaded from get_config if None).
    
    Returns:
        Tuple of (ModelResponse object or None, success boolean).
        Returns (None, False) if timeout occurs.
    """
    if config is None:
        config = get_config()
    
    timeout_limit = config.get("inference_timeout_seconds", 60.0)
    prompt_id = prompt_item.get("prompt_id", "unknown")
    prompt_text = prompt_item.get("text", "")
    
    gen_params = {
        "max_tokens": config.get("max_tokens", 256),
        "temperature": config.get("temperature", 0.7),
        "stop": ["\n\n", "User:", "Assistant:"],
        "echo": False
    }
    
    try:
        start_time = time.time()
        generated_text = generate_with_timeout(
            model, 
            prompt_text, 
            timeout_limit, 
            prompt_id, 
            **gen_params
        )
        duration = time.time() - start_time
        
        response_obj = ModelResponse(
            prompt_id=prompt_id,
            raw_text=prompt_text,
            response_text=generated_text,
            generation_time=duration,
            status="success"
        )
        return response_obj, True
        
    except InferenceTimeoutError:
        logger.error(f"Skipping prompt {prompt_id} due to timeout.")
        return None, False
    except Exception as e:
        logger.error(f"Unexpected error during inference for {prompt_id}: {e}")
        # Log to the same file or a general error log
        log_timeout_failure(prompt_id, 0, f"Error: {str(e)}")
        return None, False

def main():
    """
    Entry point for testing the timeout mechanism independently.
    This function is invoked by the main pipeline but can be tested standalone.
    """
    logger.info("Inference module loaded. Timeout enforcement ready.")
    # In a real run, this would be called by main.py after model loading
    pass

if __name__ == "__main__":
    main()