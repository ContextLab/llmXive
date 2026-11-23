"""
LLM Inference Engine wrapper using llama-cpp-python.
Handles model loading, inference, and metrics logging.
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from huggingface_hub import hf_hub_download

try:
    from llama_cpp import Llama
except ImportError:
    raise ImportError("llama-cpp-python is required. Install with: pip install llama-cpp-python")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMInferenceEngine:
    """
    Wrapper for LLM inference using llama-cpp-python.
    Supports model downloading from HuggingFace if not locally available.
    """
    
    def __init__(self, model_path: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the LLM inference engine.
        
        Args:
            model_path: Path to the GGUF model file. If None, downloads from HuggingFace.
            cache_dir: Directory for caching downloaded models.
        """
        self.model_path = model_path or self._download_default_model(cache_dir)
        self.model = None
        self._load_model()
    
    def _download_default_model(self, cache_dir: Optional[str] = None) -> str:
        """
        Download the default Llama-2-7B-Chat-GGUF model from HuggingFace.
        
        Args:
            cache_dir: Directory for caching.
        
        Returns:
            Path to the downloaded model file.
        """
        logger.info("Downloading default model from HuggingFace...")
        
        repo_id = "TheBloke/Llama-2-7B-Chat-GGUF"
        filename = "llama-2-7b-chat.Q4_K_M.gguf"
        
        try:
            model_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=cache_dir,
                local_dir=cache_dir
            )
            logger.info(f"Model downloaded to: {model_path}")
            return model_path
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise
    
    def _load_model(self):
        """Load the LLM model."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        logger.info(f"Loading model from: {self.model_path}")
        self.model = Llama(
            model_path=self.model_path,
            n_ctx=2048,  # Context window size
            n_threads=4,  # Number of threads
            verbose=False
        )
        logger.info("Model loaded successfully")
    
    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> Tuple[str, int, float]:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input prompt string.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
        
        Returns:
            Tuple of (generated_text, token_count, latency_seconds)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        start_time = time.time()
        
        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["</s>", "Question:"],  # Stop sequences
                echo=False
            )
            
            generated_text = output["choices"][0]["text"]
            token_count = output["usage"]["completion_tokens"]
            
            latency = time.time() - start_time
            
            logger.info(f"Generated {token_count} tokens in {latency:.2f}s")
            
            return generated_text, token_count, latency
            
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_path": self.model_path,
            "context_window": 2048,
            "threads": 4
        }
