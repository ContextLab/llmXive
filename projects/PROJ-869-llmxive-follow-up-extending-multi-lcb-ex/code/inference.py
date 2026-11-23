from code.config import config
from code.utils.logger import get_logger
from typing import Optional
import os
import time
import json

logger = get_logger(__name__)

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    logger.warning("llama-cpp-python not installed. Real model loading will fail.")

class MockModel:
    """
    A mock model for testing when real model loading fails or for simulation.
    IMPORTANT: Per task constraints, this class should NOT be used for actual
    inference runs if real data is required. It is provided for structural
    compatibility only.
    """
    def __init__(self):
        self.loaded = True
        logger.warning("MockModel instantiated. Real inference will not occur.")

def load_model(model_path: Optional[str] = None) -> any:
    """
    Loads the LLM model from a GGUF file.
    
    Prerequisite: T003 (Feasibility Gate) must have passed, ensuring the model
    is available and the runner is capable (or offloaded to GPU).
    
    Args:
        model_path: Optional path to the GGUF file. If None, uses config.MODEL_PATH.
        
    Returns:
        An Llama instance (real) or MockModel (if forced/fallback, though fallback
        is discouraged for real data tasks).
        
    Raises:
        RuntimeError: If the model cannot be loaded and real inference is required.
    """
    if not model_path:
        model_path = config.get('MODEL_PATH')
        
    if not model_path:
        raise RuntimeError("No model path provided and MODEL_PATH not in config.")
        
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. "
                                f"Ensure T003 feasibility gate passed or download the GGUF file.")
                                
    if not LLAMA_AVAILABLE:
        raise RuntimeError(
            "llama-cpp-python is not installed. "
            "Install it via 'pip install llama-cpp-python' to load the GGUF model."
        )

    logger.info(f"Loading GGUF model from {model_path}...")
    
    # Configuration for CPU-quantized model loading
    # We rely on the feasibility gate (T003) to have determined if this is viable.
    # We do NOT use bitsandbytes/CUDA quantization here as per constraints.
    try:
        model = Llama(
            model_path=model_path,
            n_ctx=config.get('MODEL_CTX_SIZE', 4096),
            n_threads=config.get('MODEL_N_THREADS', None),  # None lets llama-cpp auto-detect
            n_batch=config.get('MODEL_N_BATCH', 512),
            use_mmap=True,
            use_mlock=False,
            verbose=False  # Suppress llama.cpp internal logs unless debug needed
        )
        logger.info(f"Model loaded successfully from {model_path}.")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        # Do not return a mock model here if real data is required.
        # Let the caller handle the failure.
        raise RuntimeError(f"Model loading failed. Verify model path and feasibility gate: {e}")

def generate_code(model: any, prompt: str, temperature: float = 0.7, seed: int = 42) -> str:
    """
    Generates code using the loaded model.
    
    Args:
        model: The loaded Llama model instance.
        prompt: The full prompt string (problem statement + anchor + instructions).
        temperature: Sampling temperature.
        seed: Random seed for reproducibility.
        
    Returns:
        The generated code string.
        
    Raises:
        RuntimeError: If the model is a MockModel or generation fails.
    """
    if isinstance(model, MockModel):
        raise RuntimeError(
            "Cannot generate code with MockModel. "
            "This indicates a failure in loading the real GGUF model. "
            "Real data inference requires a real model instance."
        )
    
    if not hasattr(model, '__call__'):
        raise TypeError("Provided model instance is not callable.")

    logger.debug(f"Generating code with temperature={temperature}, seed={seed}")
    
    try:
        # llama_cpp generation parameters
        output = model(
            prompt,
            max_tokens=config.get('MODEL_MAX_TOKENS', 512),
            temperature=temperature,
            seed=seed,
            stop=["\n\n###", "```", "END"],  # Common stop sequences
            echo=False
        )
        
        # llama_cpp returns a dict with 'choices' list
        if 'choices' not in output or len(output['choices']) == 0:
            raise RuntimeError("Model returned no choices.")
            
        generated_text = output['choices'][0]['text']
        return generated_text.strip()
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise RuntimeError(f"Code generation failed: {e}")

def run_inference_pipeline(
    model_path: str,
    prompts: list,
    output_path: str,
    temperature: float = 0.7,
    seed: int = 42
) -> dict:
    """
    Orchestrates the loading of the model and generation of code for a list of prompts.
    Writes results to a JSON file.
    
    Args:
        model_path: Path to the GGUF model.
        prompts: List of prompt strings.
        output_path: Path to write the results JSON.
        temperature: Sampling temperature.
        seed: Random seed.
        
    Returns:
        A dictionary of results.
    """
    logger.info(f"Starting inference pipeline with {len(prompts)} prompts.")
    
    # 1. Load Model
    model = load_model(model_path)
    
    results = []
    for i, prompt in enumerate(prompts):
        logger.info(f"Processing prompt {i+1}/{len(prompts)}")
        try:
            code = generate_code(model, prompt, temperature=temperature, seed=seed)
            results.append({
                "index": i,
                "prompt_preview": prompt[:100] + "...",
                "generated_code": code,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Failed to generate for prompt {i}: {e}")
            results.append({
                "index": i,
                "prompt_preview": prompt[:100] + "...",
                "generated_code": None,
                "status": "failed",
                "error": str(e)
            })
            
    # 2. Save Results
    from code.utils.common import save_json
    save_json(results, output_path)
    logger.info(f"Inference pipeline complete. Results saved to {output_path}.")
    
    return results