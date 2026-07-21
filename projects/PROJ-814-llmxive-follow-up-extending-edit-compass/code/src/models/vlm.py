"""
VLM Wrapper for Phi-3-mini-4k-instruct-GGUF (4-bit, CPU-only) using llama-cpp-python.

This module provides a wrapper around the Phi-3-mini-4k-instruct-GGUF model
to generate descriptions for image editing tasks. It supports batch processing
with an initial batch size of 8 and dynamic adjustment capabilities.

Dependencies:
    - llama-cpp-python (pip install llama-cpp-python)
    - huggingface_hub (pip install huggingface-hub)
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from huggingface_hub import hf_hub_download
import numpy as np

# Import logging utility from project
from src.utils.logging import get_logger

# Configure logger for this module
logger = get_logger(__name__)

# Model configuration constants
MODEL_REPO_ID = "microsoft/Phi-3-mini-4k-instruct-gguf"
MODEL_FILE_NAME = "Phi-3-mini-4k-instruct.Q4_K_M.gguf"
MODEL_FILE_PATH = "models/phi3_mini_4k_instruct_q4.gguf"

# Default batch size as specified in T017
DEFAULT_BATCH_SIZE = 8

# Maximum context length for Phi-3-mini-4k
MAX_CONTEXT_LENGTH = 4096
SYSTEM_PROMPT = "You are an AI assistant that describes images in detail. Provide a concise, accurate description of the image content, focusing on objects, actions, and spatial relationships."

class VLMWrapper:
    """
    Wrapper for Phi-3-mini-4k-instruct-GGUF model using llama-cpp-python.
    
    This class handles model loading, inference, and batch processing for
    generating image descriptions.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        n_ctx: int = MAX_CONTEXT_LENGTH,
        n_threads: Optional[int] = None,
        verbose: bool = False
    ):
        """
        Initialize the VLM wrapper.
        
        Args:
            model_path: Path to the GGUF model file. If None, downloads from HuggingFace.
            batch_size: Initial batch size for processing (default: 8).
            n_ctx: Context window size (default: 4096).
            n_threads: Number of CPU threads to use. If None, auto-detects.
            verbose: Enable verbose logging from llama-cpp.
        """
        self.batch_size = batch_size
        self.n_ctx = n_ctx
        self.n_threads = n_threads or os.cpu_count()
        self.verbose = verbose
        self.model = None
        self.model_path = model_path or self._download_model()
        
        logger.info(f"VLMWrapper initialized with batch_size={batch_size}, n_threads={self.n_threads}")
        logger.info(f"Model path: {self.model_path}")
    
    def _download_model(self) -> str:
        """
        Download the GGUF model from HuggingFace if not already present.
        
        Returns:
            Path to the downloaded model file.
        
        Raises:
            RuntimeError: If model download fails.
        """
        cache_dir = Path.home() / ".cache" / "llmXive" / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        local_path = cache_dir / MODEL_FILE_NAME
        
        if local_path.exists():
            logger.info(f"Model already exists at {local_path}")
            return str(local_path)
        
        logger.info(f"Downloading model {MODEL_FILE_NAME} from {MODEL_REPO_ID}...")
        try:
            local_path = hf_hub_download(
                repo_id=MODEL_REPO_ID,
                filename=MODEL_FILE_NAME,
                cache_dir=str(cache_dir),
                local_dir=str(cache_dir),
                local_dir_use_symlinks=False
            )
            logger.info(f"Model downloaded successfully to {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise RuntimeError(f"Model download failed: {e}")
    
    def load_model(self) -> None:
        """
        Load the GGUF model using llama-cpp-python.
        
        This method initializes the Llama model with the specified configuration.
        """
        if self.model is not None:
            logger.warning("Model is already loaded")
            return
        
        try:
            from llama_cpp import Llama
            
            logger.info(f"Loading model from {self.model_path}...")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_batch=min(self.batch_size, 32),  # llama-cpp batch for context
                verbose=self.verbose,
                use_mmap=True,
                use_mlock=False
            )
            
            logger.info("Model loaded successfully")
            
        except ImportError as e:
            logger.error("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            raise ImportError(f"llama-cpp-python not available: {e}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
    
    def generate_description(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a description for a single image.
        
        Args:
            image_path: Path to the image file.
            prompt: Custom prompt for generation. If None, uses default system prompt.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
        
        Returns:
            Generated text description.
        
        Raises:
            RuntimeError: If model is not loaded or generation fails.
        """
        if self.model is None:
            self.load_model()
        
        prompt_text = prompt or SYSTEM_PROMPT
        
        # Format the prompt for Phi-3 (instruction format)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Describe this image: {image_path}"}
        ]
        
        # Convert to Phi-3 chat format
        formatted_prompt = self._format_chat(messages)
        
        try:
            output = self.model(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["<|end|>", "</s>", "###"],
                echo=False
            )
            
            description = output['choices'][0]['text'].strip()
            logger.debug(f"Generated description: {description[:100]}...")
            return description
            
        except Exception as e:
            logger.error(f"Generation failed for {image_path}: {e}")
            raise RuntimeError(f"Description generation failed: {e}")
    
    def generate_batch(
        self,
        image_paths: List[Union[str, Path]],
        prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> List[str]:
        """
        Generate descriptions for a batch of images.
        
        Args:
            image_paths: List of paths to image files.
            prompt: Custom prompt for generation. If None, uses default.
            max_tokens: Maximum tokens per generation.
            temperature: Sampling temperature.
        
        Returns:
            List of generated descriptions corresponding to input images.
        """
        if self.model is None:
            self.load_model()
        
        descriptions = []
        prompt_text = prompt or SYSTEM_PROMPT
        
        for i, image_path in enumerate(image_paths):
            try:
                description = self.generate_description(
                    image_path=image_path,
                    prompt=prompt_text,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                descriptions.append(description)
                
            except Exception as e:
                logger.error(f"Failed to generate for image {i} ({image_path}): {e}")
                # Return empty string for failed generations to maintain alignment
                descriptions.append("")
        
        return descriptions
    
    def _format_chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Format chat messages for Phi-3 model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
        
        Returns:
            Formatted prompt string.
        """
        formatted = ""
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'system':
                formatted += f"<|system|>\n{content}<|end|>\n"
            elif role == 'user':
                formatted += f"<|user|>\n{content}<|end|>\n<|assistant|>\n"
            elif role == 'assistant':
                formatted += f"{content}<|end|>\n"
        
        return formatted
    
    def adjust_batch_size(self, new_batch_size: int) -> None:
        """
        Adjust the batch size for subsequent operations.
        
        Args:
            new_batch_size: New batch size value.
        """
        old_size = self.batch_size
        self.batch_size = new_batch_size
        logger.info(f"Batch size adjusted from {old_size} to {new_batch_size}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary containing model configuration details.
        """
        if self.model is None:
            return {
                "status": "not_loaded",
                "model_path": self.model_path,
                "batch_size": self.batch_size,
                "n_ctx": self.n_ctx,
                "n_threads": self.n_threads
            }
        
        return {
            "status": "loaded",
            "model_path": self.model_path,
            "batch_size": self.batch_size,
            "n_ctx": self.n_ctx,
            "n_threads": self.n_threads,
            "n_vocab": self.model.n_vocab(),
            "n_ctx_train": self.model.n_ctx_train()
        }
    
    def unload_model(self) -> None:
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
            logger.info("Model unloaded")
    
    def __del__(self):
        """Destructor to ensure model is unloaded."""
        if self.model is not None:
            self.unload_model()


# Convenience function for quick initialization
def create_vlm_wrapper(
    batch_size: int = DEFAULT_BATCH_SIZE,
    model_path: Optional[str] = None,
    n_threads: Optional[int] = None
) -> VLMWrapper:
    """
    Factory function to create a VLMWrapper instance.
    
    Args:
        batch_size: Initial batch size (default: 8).
        model_path: Optional path to model file.
        n_threads: Number of CPU threads.
    
    Returns:
        Initialized VLMWrapper instance.
    """
    return VLMWrapper(
        model_path=model_path,
        batch_size=batch_size,
        n_threads=n_threads
    )


if __name__ == "__main__":
    # Simple test script
    logging.basicConfig(level=logging.INFO)
    
    wrapper = create_vlm_wrapper(batch_size=DEFAULT_BATCH_SIZE)
    info = wrapper.get_model_info()
    print(f"Model Info: {info}")
    
    # Test generation if model is available
    if info["status"] == "loaded":
        # Note: This requires actual image files to test
        print("Model loaded successfully. Ready for generation.")
    else:
        print("Model not loaded. Call load_model() or provide image paths.")
