import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import llama_cpp
from src.config.env_config import get_model_path, load_config

@dataclass
class InferenceResult:
    """Result container for a single quantized inference run."""
    input_id: str
    quantization_level: str
    logits: Optional[List[float]]
    success: bool
    error_message: Optional[str] = None
    skipped: bool = False

def load_quantized_model(model_path: str, quantization_level: str, n_ctx: int = 2048) -> llama_cpp.Llama:
    """
    Load a quantized LLM using llama-cpp-python.
    
    Args:
        model_path: Path to the GGUF model file.
        quantization_level: One of 'INT4', 'INT8', 'FP8'.
        n_ctx: Context window size.
        
    Returns:
        Loaded Llama model instance.
        
    Raises:
        llama_cpp.LlamaError: If model loading fails due to format or compatibility.
        OSError: If file not found or permission denied.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")

    # Map quantization levels to llama-cpp parameters if needed
    # For GGUF, the quantization is usually baked into the filename, 
    # but we ensure we load with appropriate settings if supported.
    # Currently, llama-cpp-python auto-detects GGUF format.
    
    try:
        model = llama_cpp.Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=4,
            n_batch=512,
            verbose=False
        )
        return model
    except (llama_cpp.LlamaError, OSError) as e:
        raise e

def run_quantized_inference(model: llama_cpp.Llama, prompt: str, max_tokens: int = 128) -> List[float]:
    """
    Run inference on a quantized model and return logits.
    
    Args:
        model: Loaded Llama model.
        prompt: Input text prompt.
        max_tokens: Maximum tokens to generate.
        
    Returns:
        List of logits (or logprobs) for the generated sequence.
        
    Raises:
        llama_cpp.LlamaError: If inference fails.
    """
    try:
        # Run generation
        output = model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.0,  # Deterministic for consistency
            logprobs=1,       # Request log probabilities
            echo=False,
            stop=[]
        )
        
        # Extract logprobs if available, otherwise return empty list
        # The structure depends on llama-cpp version, typically 'choices' -> 'logprobs'
        if 'choices' in output and len(output['choices']) > 0:
            choice = output['choices'][0]
            if 'logprobs' in choice and choice['logprobs']:
                # Return list of log probabilities
                return [float(lp) for lp in choice['logprobs'].get('token_logprobs', [])]
        return []
    except (llama_cpp.LlamaError, OSError) as e:
        raise e

def process_sample(sample: Dict[str, Any], model: llama_cpp.Llama, quantization_level: str) -> InferenceResult:
    """
    Process a single sample: run quantized inference and capture results.
    
    Args:
        sample: Dictionary containing 'input_id' and 'prompt'.
        model: Loaded Llama model.
        quantization_level: String identifier for the quantization used.
        
    Returns:
        InferenceResult object.
    """
    input_id = sample.get('input_id', 'unknown')
    prompt = sample.get('prompt', '')
    
    if not prompt:
        return InferenceResult(
            input_id=input_id,
            quantization_level=quantization_level,
            logits=None,
            success=False,
            error_message="Empty prompt provided",
            skipped=True
        )
    
    try:
        logits = run_quantized_inference(model, prompt)
        return InferenceResult(
            input_id=input_id,
            quantization_level=quantization_level,
            logits=logits,
            success=True
        )
    except (llama_cpp.LlamaError, OSError) as e:
        # Log the error specifically as requested
        logging.error(f"Error loading quantization: {str(e)}")
        # Skip the current sample by marking it as skipped
        return InferenceResult(
            input_id=input_id,
            quantization_level=quantization_level,
            logits=None,
            success=False,
            error_message=str(e),
            skipped=True
        )

def run_quantized_inference_batch(
    samples: List[Dict[str, Any]],
    model_path: str,
    quantization_level: str,
    n_ctx: int = 2048
) -> List[InferenceResult]:
    """
    Run quantized inference on a batch of samples, handling engine failures gracefully.
    
    This function implements the core requirement of T013:
    - Explicitly catch LlamaError and OSError.
    - Log the error with specific format.
    - Skip the current sample (log as skipped) and continue processing.
    - DO NOT raise a critical exception to halt the pipeline.
    
    Args:
        samples: List of sample dictionaries with 'input_id' and 'prompt'.
        model_path: Path to the GGUF model.
        quantization_level: 'INT4', 'INT8', or 'FP8'.
        n_ctx: Context window size.
        
    Returns:
        List of InferenceResult objects.
    """
    logger = logging.getLogger(__name__)
    results = []
    
    logger.info(f"Starting batch inference for {len(samples)} samples at level {quantization_level}")
    
    try:
        model = load_quantized_model(model_path, quantization_level, n_ctx)
        logger.info(f"Model loaded successfully for {quantization_level}")
    except (llama_cpp.LlamaError, OSError) as e:
        # Log the error if model loading fails
        logger.error(f"Error loading quantization: {str(e)}")
        # If model fails to load, we cannot process any samples.
        # Return skipped results for all to maintain pipeline continuity.
        for sample in samples:
            results.append(InferenceResult(
                input_id=sample.get('input_id', 'unknown'),
                quantization_level=quantization_level,
                logits=None,
                success=False,
                error_message=f"Model load failed: {str(e)}",
                skipped=True
            ))
        return results
    
    for sample in samples:
        result = process_sample(sample, model, quantization_level)
        results.append(result)
        
        if result.skipped:
            logger.warning(f"Skipped sample {result.input_id} due to inference error.")
        elif result.success:
            logger.debug(f"Processed sample {result.input_id} successfully.")
    
    return results

def main():
    """
    Entry point for testing the module directly.
    """
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    model_path = get_model_path()
    
    if not model_path:
        logging.error("MODEL_PATH not configured in .env")
        return

    # Dummy sample for testing
    test_samples = [
        {"input_id": "test_001", "prompt": "What is 2+2?"},
        {"input_id": "test_002", "prompt": ""},  # Empty prompt to test skipping
    ]
    
    # Note: This will fail if the model doesn't exist, demonstrating the error handling
    results = run_quantized_inference_batch(
        test_samples, 
        model_path, 
        quantization_level="INT4"
    )
    
    for res in results:
        status = "SUCCESS" if res.success else "SKIPPED"
        print(f"Sample {res.input_id}: {status} - {res.error_message}")

if __name__ == "__main__":
    main()