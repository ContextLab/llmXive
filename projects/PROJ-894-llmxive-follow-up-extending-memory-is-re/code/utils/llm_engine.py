"""
LLM Inference Engine using llama-cpp-python.

Provides a wrapper for running quantized LLM inference on local GGUF models.
"""
import os
import logging
from pathlib import Path
from typing import Optional

from llama_cpp import Llama

logger = logging.getLogger(__name__)

# Default model path configuration
# This should be updated to point to the actual downloaded GGUF file
DEFAULT_MODEL_PATH = "models/llama-2-7b-chat.Q4_0.gguf"

class LLMInferenceEngine:
    """
    Wrapper for llama-cpp-python LLM inference.

    Attributes:
        model_path (str): Path to the GGUF model file.
        model (Llama): The loaded LLM instance.
    """

    def __init__(self, model_path: Optional[str] = None, n_ctx: int = 2048, n_threads: int = 4):
        """
        Initialize the LLM engine.

        Args:
            model_path: Path to the GGUF model file. Defaults to DEFAULT_MODEL_PATH.
            n_ctx: Context window size.
            n_threads: Number of threads for inference.
        """
        self.model_path = model_path or DEFAULT_MODEL_PATH

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model file not found at {self.model_path}. "
                f"Please download a GGUF model (e.g., from HuggingFace) and place it at this path."
            )

        logger.info(f"Loading model from {self.model_path} with q4_0 quantization...")
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                verbose=False
            )
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def run_inference(self, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> str:
        """
        Run inference on the given prompt.

        Args:
            prompt: The input text prompt.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.

        Returns:
            The generated text response.
        """
        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["</s>", "User:", "Assistant:"],
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            raise

def run_inference(model_path: str, prompt: str, max_tokens: int = 256, temperature: float = 0.7) -> str:
    """
    Convenience function to run inference without instantiating the class.

    Args:
        model_path: Path to the GGUF model file.
        prompt: The input text prompt.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature.

    Returns:
        The generated text response.
    """
    engine = LLMInferenceEngine(model_path=model_path)
    return engine.run_inference(prompt, max_tokens, temperature)
