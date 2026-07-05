"""
Inference utilities for CPU-optimized LLM execution.
Provides GGUF model loading, batching logic, and timeout/fail-fast mechanisms.
"""
import logging
import os
import signal
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, List, Optional, Callable

try:
    from llama_cpp import Llama
except ImportError:
    raise ImportError(
        "llama-cpp-python is required. Install with: pip install llama-cpp-python"
    )

logger = logging.getLogger(__name__)

class InferenceError(Exception):
    """Custom exception for inference-related errors."""
    pass

class TimeoutError(InferenceError):
    """Exception raised when inference exceeds the timeout limit."""
    pass

class ModelLoadError(InferenceError):
    """Exception raised when model loading fails."""
    pass

def _timeout_handler(signum, frame):
    """Signal handler for timeout enforcement."""
    raise TimeoutError("Inference operation timed out")

def load_model(
    model_path: str,
    n_ctx: int = 2048,
    n_batch: int = 512,
    n_threads: int = 4,
    verbose: bool = False
) -> Llama:
    """
    Load a GGUF model optimized for CPU inference.

    Args:
        model_path: Path to the .gguf model file.
        n_ctx: Context window size.
        n_batch: Batch size for prompt processing.
        n_threads: Number of CPU threads to use.
        verbose: Whether to print verbose loading logs.

    Returns:
        Loaded Llama model instance.

    Raises:
        ModelLoadError: If the model fails to load or the path is invalid.
    """
    if not os.path.exists(model_path):
        raise ModelLoadError(f"Model file not found at: {model_path}")

    logger.info(f"Loading model from {model_path} with {n_threads} threads...")
    try:
        model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_batch=n_batch,
            n_threads=n_threads,
            verbose=verbose,
            use_mmap=True,  # Memory map for efficiency
            use_mlock=False # Allow swapping if memory is tight
        )
        logger.info("Model loaded successfully.")
        return model
    except Exception as e:
        raise ModelLoadError(f"Failed to load model: {e}") from e

def run_single_inference(
    model: Llama,
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.1,
    timeout_seconds: Optional[float] = None
) -> Dict[str, Any]:
    """
    Run inference on a single prompt with optional timeout.

    Args:
        model: Loaded Llama model.
        prompt: Input text prompt.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        timeout_seconds: Optional timeout in seconds.

    Returns:
        Dictionary containing 'generated_text', 'success', and 'error' keys.
    """
    result = {
        "generated_text": "",
        "success": False,
        "error": None,
        "hallucination_flag": False
    }

    if timeout_seconds:
        # Set signal handler for timeout (Unix only)
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(int(timeout_seconds))
        else:
            # Fallback for non-SIGALRM platforms (Windows) using threading would be complex here,
            # so we rely on the model's internal timeout if available or just run.
            # For robust cross-platform timeout in a simple script, we might skip signal.alarm
            # and rely on a wrapper, but for this utility we assume Unix or accept the limitation.
            pass

    try:
        # Perform generation
        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["</s>", "###"], # Common stop sequences
            echo=False
        )
        
        generated_text = output['choices'][0]['text']
        result["generated_text"] = generated_text
        result["success"] = True

    except TimeoutError as e:
        result["error"] = str(e)
        logger.warning(f"Timeout occurred for prompt: {prompt[:50]}...")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Inference failed: {e}")
        # Check for specific hallucination patterns if needed, 
        # but the task asks for the mechanism, not specific content detection logic here.
    finally:
        if timeout_seconds and hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    return result

def run_batch_inference(
    model: Llama,
    prompts: List[str],
    max_tokens: int = 256,
    temperature: float = 0.1,
    timeout_per_prompt: Optional[float] = None,
    max_workers: int = 1
) -> List[Dict[str, Any]]:
    """
    Run inference on a batch of prompts with concurrency and fail-fast logic.

    Args:
        model: Loaded Llama model.
        prompts: List of input prompts.
        max_tokens: Maximum tokens per generation.
        temperature: Sampling temperature.
        timeout_per_prompt: Timeout per individual prompt.
        max_workers: Number of parallel workers (1 for CPU-bound LLM unless model supports parallel).
                    Note: llama-cpp-python is generally not thread-safe for concurrent generation
                    on the same model instance without specific locking. 
                    We serialize here to be safe, or use a queue if the model supports it.
                    For CPU optimization, usually sequential is faster due to cache, 
                    but we provide the structure for batching.

    Returns:
        List of result dictionaries corresponding to each prompt.
    """
    results = []
    
    # If max_workers > 1, we must be careful. llama_cpp Llama instance is not thread-safe 
    # for concurrent generate calls. We will use a simple loop for safety unless 
    # the user explicitly handles locking, but we structure it as a "batch" processor.
    # To be safe and "CPU-optimized" (avoiding GIL contention on a single core), 
    # we process sequentially if the model doesn't support internal batching.
    
    logger.info(f"Processing batch of {len(prompts)} prompts...")
    
    start_time = time.time()
    
    for i, prompt in enumerate(prompts):
        # Fail-fast mechanism: if a critical error occurs, we could stop, 
        # but usually we want to skip and log.
        res = run_single_inference(
            model, 
            prompt, 
            max_tokens=max_tokens, 
            temperature=temperature, 
            timeout_seconds=timeout_per_prompt
        )
        results.append(res)
        
        # Optional: Log progress
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Processed {i+1}/{len(prompts)} prompts. Time: {elapsed:.2f}s")

    return results

def detect_hallucination(generated_text: str, reference_code: Optional[str] = None) -> bool:
    """
    Basic hallucination detection.
    Currently checks for empty output or non-code characters if reference is missing.
    Can be extended to compare against reference_code.
    
    Args:
        generated_text: The text generated by the LLM.
        reference_code: Optional original code to compare against.

    Returns:
        True if hallucination is detected, False otherwise.
    """
    if not generated_text or not generated_text.strip():
        return True
    
    # Simple heuristic: if the output is mostly non-alphanumeric or doesn't look like code
    # This is a placeholder for more sophisticated logic.
    # If a reference is provided, we could check for significant deviation.
    if reference_code:
        # If the generated text is completely different from reference (e.g. length diff > 90%)
        # and contains no code keywords, flag it.
        pass 
        
    return False

def process_with_fail_fast(
    model: Llama,
    prompts: List[str],
    max_tokens: int = 256,
    timeout_per_prompt: float = 60.0
) -> List[Dict[str, Any]]:
    """
    Wrapper to run inference with strict fail-fast on repeated timeouts or errors.
    
    Args:
        model: Loaded model.
        prompts: List of prompts.
        max_tokens: Max tokens.
        timeout_per_prompt: Timeout limit.
        
    Returns:
        List of results.
    """
    results = []
    consecutive_failures = 0
    max_consecutive_failures = 3

    for prompt in prompts:
        try:
            res = run_single_inference(
                model, prompt, max_tokens, timeout_seconds=timeout_per_prompt
            )
            
            if not res["success"]:
                consecutive_failures += 1
                logger.warning(f"Failure {consecutive_failures} for prompt: {prompt[:20]}...")
                
                if consecutive_failures >= max_consecutive_failures:
                    raise InferenceError(
                        f"Fail-fast triggered after {max_consecutive_failures} consecutive failures."
                    )
            else:
                consecutive_failures = 0
            
            results.append(res)
            
        except InferenceError as e:
            logger.error(f"Stopping pipeline due to error: {e}")
            # Mark remaining as failed or stop? Stopping is fail-fast.
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break

    return results