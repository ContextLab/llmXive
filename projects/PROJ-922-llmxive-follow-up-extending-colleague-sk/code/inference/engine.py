import os
import signal
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from utils.config import get_project_root, get_data_dir, ensure_dir, get_device, get_model_cache_dir
from utils.logging import get_logger

logger = get_logger(__name__)

class InferenceTimeoutError(Exception):
    """Exception raised when inference times out."""
    pass

class InferenceOOMError(Exception):
    """Exception raised when inference runs out of memory."""
    pass

class ModelLoadError(Exception):
    """Exception raised when model loading fails."""
    pass

class InferenceEngine:
    """
    Inference engine for running LLM inference on CPU.
    
    This engine supports loading quantized models and generating text with
    timeout and OOM protection.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the inference engine.
        
        Args:
            model_path: Path to the model file. If None, uses default cache location.
        """
        self.model = None
        self.model_path = model_path
        self.device = get_device()
        
        # Default model settings
        self.n_ctx = 2048
        self.n_threads = 4
        self.n_batch = 512
        
        # Try to load model
        try:
            self._load_model()
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise ModelLoadError(f"Model load failed: {str(e)}")
    
    def _load_model(self) -> None:
        """Load the quantized model."""
        try:
            # Check if llama-cpp-python is available
            try:
                from llama_cpp import Llama
            except ImportError:
                logger.error("llama-cpp-python not installed. Please install it with: pip install llama-cpp-python")
                raise ModelLoadError("llama-cpp-python not installed")
            
            # Determine model path
            if self.model_path is None:
                model_cache_dir = get_model_cache_dir()
                ensure_dir(model_cache_dir)
                # Try common model names
                possible_models = [
                    model_cache_dir / "llama-2-7b-chat.Q4_K_M.gguf",
                    model_cache_dir / "phi-3-mini-4k-instruct-q4.gguf",
                    model_cache_dir / "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
                ]
                
                model_path = None
                for p in possible_models:
                    if p.exists():
                        model_path = str(p)
                        break
                
                if model_path is None:
                    # If no model found, try to download a small one for testing
                    # In production, this should be pre-downloaded
                    logger.warning("No model found in cache. Using a placeholder for testing.")
                    # For now, we'll raise an error if no model is found
                    raise ModelLoadError("No model file found. Please download a model and place it in the cache directory.")
                self.model_path = model_path
            else:
                self.model_path = str(self.model_path)
            
            # Load model
            logger.info(f"Loading model from {self.model_path}")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_batch=self.n_batch,
                n_gpu_layers=0,  # CPU only
                verbose=False
            )
            logger.info("Model loaded successfully")
            
        except FileNotFoundError as e:
            raise ModelLoadError(f"Model file not found: {str(e)}")
        except Exception as e:
            raise ModelLoadError(f"Failed to load model: {str(e)}")
    
    def _timeout_handler(self, seconds: int):
        """Handler for timeout signal."""
        raise InferenceTimeoutError(f"Inference timed out after {seconds} seconds")
    
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7, 
                timeout: int = 300) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The input prompt.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            timeout: Timeout in seconds.
            
        Returns:
            Generated text.
            
        Raises:
            InferenceTimeoutError: If generation times out.
            InferenceOOMError: If out of memory occurs.
        """
        if self.model is None:
            raise ModelLoadError("Model not loaded")
        
        # Set up timeout
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(timeout)
        else:
            # Windows doesn't support SIGALRM
            timeout_occurred = False
            def timeout_check():
                nonlocal timeout_occurred
                time.sleep(timeout)
                timeout_occurred = True
            
            timeout_thread = threading.Thread(target=timeout_check)
            timeout_thread.daemon = True
            timeout_thread.start()
        
        try:
            # Run inference
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["</s>", "Task:", "[System:"],
                echo=False
            )
            
            # Check for timeout on Windows
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            else:
                if timeout_occurred:
                    raise InferenceTimeoutError(f"Inference timed out after {timeout} seconds")
            
            # Extract generated text
            generated_text = output['choices'][0]['text']
            return generated_text.strip()
            
        except InferenceTimeoutError:
            raise
        except MemoryError:
            raise InferenceOOMError("Out of memory during inference")
        except Exception as e:
            if "timed out" in str(e).lower():
                raise InferenceTimeoutError(str(e))
            elif "memory" in str(e).lower() or "oom" in str(e).lower():
                raise InferenceOOMError(str(e))
            else:
                raise

def load_model(model_path: Optional[str] = None) -> InferenceEngine:
    """
    Load a model and return an inference engine.
    
    Args:
        model_path: Path to the model file.
        
    Returns:
        InferenceEngine instance.
    """
    return InferenceEngine(model_path)

def generate(engine: InferenceEngine, prompt: str, max_tokens: int = 512, 
            temperature: float = 0.7, timeout: int = 300) -> str:
    """
    Generate text using an existing engine.
    
    Args:
        engine: InferenceEngine instance.
        prompt: The input prompt.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        timeout: Timeout in seconds.
        
    Returns:
        Generated text.
    """
    return engine.generate(prompt, max_tokens, temperature, timeout)

def main():
    """Main entry point for testing the engine."""
    logger.info("Testing inference engine")
    
    try:
        engine = InferenceEngine()
        test_prompt = "[System: You are a helpful assistant. Task: Write a short poem about AI.]"
        output = engine.generate(test_prompt, max_tokens=100, timeout=60)
        logger.info(f"Generated output: {output}")
    except Exception as e:
        logger.error(f"Engine test failed: {e}")
        raise

if __name__ == "__main__":
    main()