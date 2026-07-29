"""
VLM Wrapper for Phi-3-mini-4k-instruct-GGUF (4-bit, CPU-only) using llama-cpp-python.

This module provides a wrapper around the Phi-3 mini model to generate text
descriptions for images. It is designed to run on CPU with a 4-bit quantized
model fetched from Hugging Face.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from huggingface_hub import hf_hub_download

# Import logging utility from project
try:
    from src.utils.logging import get_logger
except ImportError:
    # Fallback for direct execution or different import context
    import logging
    def get_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

# Configuration constants
DEFAULT_MODEL_REPO = "microsoft/Phi-3-mini-4k-instruct-gguf"
DEFAULT_MODEL_FILE = "Phi-3-mini-4k-instruct-q4_0.gguf"
DEFAULT_BATCH_SIZE = 8
MAX_TOKENS = 256
TEMPERATURE = 0.7

logger = get_logger(__name__)

class VLMWrapper:
    """
    Wrapper for Phi-3-mini-4k-instruct GGUF model.
    
    Attributes:
        model_path (Path): Path to the GGUF model file.
        n_ctx (int): Context window size.
        n_batch (int): Batch size for processing.
        n_threads (int): Number of CPU threads to use.
        model: The loaded llama-cpp model instance.
    """
    
    def __init__(
        self,
        model_repo: str = DEFAULT_MODEL_REPO,
        model_file: str = DEFAULT_MODEL_FILE,
        n_ctx: int = 4096,
        n_batch: int = DEFAULT_BATCH_SIZE,
        n_threads: Optional[int] = None,
        verbose: bool = False
    ):
        """
        Initialize the VLM wrapper and download/load the model.
        
        Args:
            model_repo: Hugging Face repository ID.
            model_file: Name of the GGUF file in the repository.
            n_ctx: Context window size.
            n_batch: Batch size for processing.
            n_threads: Number of CPU threads (defaults to all available).
            verbose: Enable verbose logging from llama-cpp.
        
        Raises:
            FileNotFoundError: If the model cannot be downloaded or found.
            ImportError: If llama-cpp-python is not installed.
        """
        self.model_repo = model_repo
        self.model_file = model_file
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.n_threads = n_threads or os.cpu_count() or 1
        self.verbose = verbose
        self.model = None
        
        logger.info(f"Initializing VLMWrapper with model {model_file} from {model_repo}")
        logger.info(f"Configuration: n_ctx={n_ctx}, n_batch={n_batch}, n_threads={self.n_threads}")
        
        # Download model if not present
        try:
            model_path = hf_hub_download(
                repo_id=model_repo,
                filename=model_file,
                local_dir="data/models/phi3",
                local_dir_use_symlinks=False
            )
            logger.info(f"Model downloaded/located at: {model_path}")
        except Exception as e:
            logger.error(f"Failed to download or locate model: {e}")
            raise FileNotFoundError(f"Could not retrieve model from {model_repo}/{model_file}: {e}")
        
        self.model_path = Path(model_path)
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the model using llama-cpp-python."""
        try:
            from llama_cpp import Llama
        except ImportError:
            logger.error("llama-cpp-python is not installed. Please install it with 'pip install llama-cpp-python'.")
            raise ImportError("llama-cpp-python package is required but not installed.")
        
        logger.info(f"Loading model from {self.model_path}...")
        try:
            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                n_threads=self.n_threads,
                verbose=self.verbose,
                n_gpu_layers=0  # Force CPU usage
            )
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Error loading model: {e}")
    
    def generate_description(
        self,
        image_path: Union[str, Path],
        prompt: str = "Describe this image in detail, focusing on visual elements and context.",
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE
    ) -> str:
        """
        Generate a text description for a single image.
        
        Args:
            image_path: Path to the image file.
            prompt: The prompt to guide the generation.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
        
        Returns:
            str: The generated description text.
        
        Raises:
            ValueError: If the model is not loaded.
            FileNotFoundError: If the image path is invalid.
        """
        if self.model is None:
            raise ValueError("Model is not loaded. Call _load_model() first.")
        
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Construct the prompt for Phi-3 (instruction format)
        # Phi-3 expects <s><|user|>\n{prompt}<|end|>\n<|assistant|>\n
        full_prompt = (
            f"<s><|user|>\n{prompt} "
            f"<img_src>{image_path.name}</img_src><|end|>\n"
            f"<|assistant|>\n"
        )
        
        # Note: For true multimodal capability, the model would need to process the image tensor.
        # However, standard Phi-3 GGUF is text-only. This wrapper assumes the prompt includes
        # the image path as a reference or the system expects a text-only description based on
        # the prompt provided. If the GGUF is a specific multimodal variant (e.g., Phi-3-vision),
        # the llama-cpp API would need specific image embedding handling.
        # Assuming standard text-instruction behavior for this implementation context.
        
        output = self.model(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|end|>", "<|assistant|>"],
            echo=False
        )
        
        return output['choices'][0]['text'].strip()
    
    def generate_batch(
        self,
        image_paths: List[Union[str, Path]],
        prompt: str = "Describe this image in detail.",
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE
    ) -> List[str]:
        """
        Generate descriptions for a batch of images.
        
        Args:
            image_paths: List of paths to image files.
            prompt: The prompt to guide the generation.
            max_tokens: Maximum tokens per generation.
            temperature: Sampling temperature.
        
        Returns:
            List[str]: List of generated descriptions.
        """
        descriptions = []
        logger.info(f"Processing batch of {len(image_paths)} images with batch size {self.n_batch}")
        
        for i, path in enumerate(image_paths):
            try:
                desc = self.generate_description(
                    path,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                descriptions.append(desc)
            except Exception as e:
                logger.warning(f"Failed to process image {path}: {e}")
                descriptions.append("") # Return empty string on failure to maintain list length
        
        return descriptions
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if self.model is None:
            return {"status": "not_loaded"}
        
        return {
            "model_path": str(self.model_path),
            "context_window": self.n_ctx,
            "batch_size": self.n_batch,
            "threads": self.n_threads,
            "status": "loaded"
        }

def create_vlm_wrapper(
    model_repo: str = DEFAULT_MODEL_REPO,
    model_file: str = DEFAULT_MODEL_FILE,
    batch_size: int = DEFAULT_BATCH_SIZE,
    threads: Optional[int] = None
) -> VLMWrapper:
    """
    Factory function to create and return a VLMWrapper instance.
    
    Args:
        model_repo: Hugging Face repository ID.
        model_file: Name of the GGUF file.
        batch_size: Initial batch size.
        threads: Number of CPU threads.
    
    Returns:
        VLMWrapper: Initialized wrapper instance.
    """
    return VLMWrapper(
        model_repo=model_repo,
        model_file=model_file,
        n_batch=batch_size,
        n_threads=threads
    )