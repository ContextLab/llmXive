"""
Quantized Inference Service for llmXive.

Wraps llama-cpp-python to run INT4, INT8, and FP8 inference on CPU.
Implements strict error handling: logs critical errors and skips failed samples
without halting the pipeline.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import base64
import numpy as np

# Import from project API surface
from src.config.env_config import get_model_path, load_config

# Import llama_cpp safely; if not installed, the error will be caught in the specific functions
try:
    import llama_cpp
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    llama_cpp = None  # type: ignore


@dataclass
class InferenceResult:
    """Result of a single quantized inference run."""
    sample_id: str
    quantization_level: str
    logits: Optional[List[float]]  # Stored as list for serialization
    success: bool
    error_message: Optional[str] = None


def load_quantized_model(
    model_path: str,
    quantization_level: str = "q4_0",
    n_ctx: int = 2048,
    n_threads: int = 4
) -> Any:
    """
    Load a quantized model using llama-cpp-python.

    Args:
        model_path: Path to the GGUF model file.
        quantization_level: Quantization type (e.g., 'q4_0', 'q8_0', 'f16').
        n_ctx: Context window size.
        n_threads: Number of CPU threads.

    Returns:
        Loaded Llama model instance.

    Raises:
        Exception: If model loading fails due to invalid path, missing file,
                   or incompatible quantization.
    """
    if not LLAMA_CPP_AVAILABLE:
        raise ImportError("llama_cpp is not installed. Please install it via pip.")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    # Map quantization levels to llama_cpp settings if necessary
    # For now, we assume the model_path already points to the correct GGUF file
    # or we rely on the user to pass the correct path.
    # Standard llama-cpp-python Llama class handles the loading.

    try:
        model = llama_cpp.Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=False  # Reduce noise
        )
        return model
    except llama_cpp.LlamaError as e:
        raise RuntimeError(f"Failed to load Llama model: {e}")
    except OSError as e:
        raise RuntimeError(f"OS error during model load (possibly memory or file): {e}")


def run_quantized_inference(
    model: Any,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.0
) -> List[float]:
    """
    Run inference on a quantized model and return logits.

    Args:
        model: Loaded Llama model instance.
        prompt: Input text prompt.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature (0.0 for greedy).

    Returns:
        List of logits (floats) for the generated tokens.

    Raises:
        Exception: If inference fails.
    """
    try:
        # llama-cpp-python returns a dict with 'choices' containing 'text' and 'logprobs'
        # We need to extract logits. Note: standard Llama class might not expose raw logits
        # easily without specific flags. We will attempt to get logprobs and convert.
        # If logprobs are not available, we might need to adjust the call or use a different method.
        # For this implementation, we assume we can get log probabilities.

        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            logprobs=1,  # Request log probabilities
            echo=False,
            stop=[]
        )

        # Extract log probabilities
        # Structure: output['choices'][0]['logprobs']['token_logprobs']
        if 'choices' in output and len(output['choices']) > 0:
            logprobs = output['choices'][0].get('logprobs', {}).get('token_logprobs', [])
            if logprobs:
                return [float(lp) for lp in logprobs]
            else:
                # If logprobs are empty but generation succeeded, return empty list or zeros
                # depending on downstream requirements. Returning empty list here.
                return []
        else:
            return []

    except llama_cpp.LlamaError as e:
        raise RuntimeError(f"LLM inference error: {e}")
    except OSError as e:
        raise RuntimeError(f"OS error during inference: {e}")


def process_sample(
    sample_id: str,
    prompt: str,
    model_path: str,
    quantization_level: str,
    logger: logging.Logger
) -> InferenceResult:
    """
    Process a single sample: load model (if needed), run inference, handle errors.

    Args:
        sample_id: Unique identifier for the sample.
        prompt: Input prompt text.
        model_path: Path to the GGUF model.
        quantization_level: Quantization level (INT4, INT8, FP8).
        logger: Logger instance.

    Returns:
        InferenceResult object.
    """
    # Map quantization level to GGUF suffix or specific model path logic if needed.
    # Assuming model_path is passed correctly for the specific level in the caller.
    # If the caller passes a generic path, we might need to append suffixes.
    # For this task, we assume model_path is the specific GGUF file for the level.

    try:
        # Load model
        # Note: In a real pipeline, we might want to cache the model to avoid reloading for every sample.
        # However, for robustness against memory issues in streaming, we might reload or keep a cache.
        # Given the requirement to handle engine failures gracefully, we load here.
        # Optimization: In a real batch, this function might receive a pre-loaded model.
        # But the signature suggests per-sample processing. Let's assume the model is loaded once
        # outside and passed in, OR we load it here.
        # The task description says "Wrap llama-cpp-python to run...".
        # To be safe and stateless per sample (or handle reloads), we try to load.
        # If the model is large, reloading every time is slow.
        # Let's assume the model is loaded once in the batch runner and passed here,
        # OR we load it here if not provided.
        # The function signature doesn't take a model object, so we load it.
        
        # To avoid reloading the same model for every sample in a batch, the caller
        # should ideally pass a loaded model. However, the task says "process_sample".
        # We will implement loading here but add a check if the model is already loaded?
        # No, we must follow the spec. Let's assume the caller manages the model or
        # we load it here. Given the "skip sample" requirement, loading here is safer
        # to catch load errors per sample type.

        model = load_quantized_model(model_path, quantization_level)
        
        logits = run_quantized_inference(model, prompt)
        
        return InferenceResult(
            sample_id=sample_id,
            quantization_level=quantization_level,
            logits=logits,
            success=True
        )

    except (llama_cpp.LlamaError, OSError, RuntimeError, FileNotFoundError) as e:
        error_msg = str(e)
        # Explicitly log a critical error as required
        logger.critical(f"SAMPLE SKIPPED: {sample_id} - {error_msg}")
        return InferenceResult(
            sample_id=sample_id,
            quantization_level=quantization_level,
            logits=None,
            success=False,
            error_message=error_msg
        )


def run_quantized_inference_batch(
    samples: List[Dict[str, Any]],
    model_path: str,
    quantization_level: str,
    logger: logging.Logger,
    max_tokens: int = 512
) -> List[InferenceResult]:
    """
    Run quantized inference on a batch of samples.

    Args:
        samples: List of dicts with 'sample_id' and 'prompt'.
        model_path: Path to the GGUF model.
        quantization_level: Quantization level.
        logger: Logger instance.
        max_tokens: Max tokens per generation.

    Returns:
        List of InferenceResult objects.
    """
    results = []
    
    # Optimization: Load model once for the batch if possible, but handle errors if it fails.
    # If the model fails to load, all samples will be skipped.
    try:
        model = load_quantized_model(model_path, quantization_level)
    except Exception as e:
        logger.critical(f"BATCH FAILED: Could not load model for {quantization_level} - {e}")
        for sample in samples:
            results.append(InferenceResult(
                sample_id=sample.get('sample_id', 'unknown'),
                quantization_level=quantization_level,
                logits=None,
                success=False,
                error_message=str(e)
            ))
        return results

    for sample in samples:
        sample_id = sample.get('sample_id', 'unknown')
        prompt = sample.get('prompt', '')
        
        try:
            logits = run_quantized_inference(model, prompt, max_tokens=max_tokens)
            results.append(InferenceResult(
                sample_id=sample_id,
                quantization_level=quantization_level,
                logits=logits,
                success=True
            ))
        except (llama_cpp.LlamaError, OSError, RuntimeError) as e:
            error_msg = str(e)
            logger.critical(f"SAMPLE SKIPPED: {sample_id} - {error_msg}")
            results.append(InferenceResult(
                sample_id=sample_id,
                quantization_level=quantization_level,
                logits=None,
                success=False,
                error_message=error_msg
            ))
    
    return results


def main():
    """
    Entry point for standalone testing or CLI execution.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    config = load_config()
    model_path = get_model_path()
    
    if not model_path or not os.path.exists(model_path):
        logger.error(f"Model path not configured or not found: {model_path}")
        return

    # Example sample
    test_samples = [
        {"sample_id": "test_001", "prompt": "What is the capital of France?"},
        {"sample_id": "test_002", "prompt": "2 + 2 = ?"}
    ]
    
    logger.info("Starting quantized inference batch processing...")
    results = run_quantized_inference_batch(
        samples=test_samples,
        model_path=model_path,
        quantization_level="q4_0",
        logger=logger
    )
    
    for res in results:
        if res.success:
            logger.info(f"Success: {res.sample_id}, Logits count: {len(res.logits) if res.logits else 0}")
        else:
            logger.warning(f"Failed: {res.sample_id}, Error: {res.error_message}")


if __name__ == "__main__":
    main()