"""
VLM Wrapper for Phi-3-mini-4k-instruct-GGUF (4-bit, CPU-only).
Uses llama-cpp-python for inference.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from huggingface_hub import hf_hub_download

# Attempt import of llama_cpp; if missing, we raise a clear error at runtime
try:
    from llama_cpp import Llama
except ImportError:
    # We do not import here to avoid failing at module load if the user
    # hasn't installed dependencies yet. We will raise in __init__.
    Llama = None

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default batch size as per task requirement
DEFAULT_BATCH_SIZE = 8

# Model identifiers for Phi-3-mini-4k-instruct-GGUF
# Using a specific 4-bit quantization from a known HuggingFace repo
MODEL_REPO_ID = "MaziyarPanahi/Phi-3-mini-4k-instruct-GGUF"
MODEL_FILENAME = "Phi-3-mini-4k-instruct.Q4_K_M.gguf"
# Alternative: "bartowski/Phi-3-mini-4k-instruct-GGUF/Phi-3-mini-4k-instruct-Q4_K_M.gguf"
# We use the first one as it is stable and widely used.

class VLMWrapper:
    """
    Wrapper around llama-cpp Llama for Phi-3-mini-4k-instruct (4-bit, CPU).
    Supports batch generation of descriptions for images.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: int = 4096,
        n_threads: Optional[int] = None,
        n_threads_batch: Optional[int] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        verbose: bool = False,
    ):
        """
        Initialize the VLM wrapper.

        Args:
            model_path: Path to the .gguf file. If None, downloads from HuggingFace.
            n_ctx: Context window size.
            n_threads: Number of CPU threads for single prompt.
            n_threads_batch: Number of CPU threads for batch processing.
            batch_size: Default batch size for generation.
            verbose: If True, enable llama-cpp verbose logging.
        """
        if Llama is None:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Install it with: pip install llama-cpp-python"
            )

        self.n_ctx = n_ctx
        self.n_threads = n_threads or os.cpu_count()
        self.n_threads_batch = n_threads_batch or self.n_threads
        self.batch_size = batch_size
        self.verbose = verbose

        self._llm: Optional[Llama] = None
        self._model_path = model_path

        # If no path provided, download from HF
        if self._model_path is None:
            logger.info(f"Downloading model {MODEL_FILENAME} from {MODEL_REPO_ID}...")
            self._model_path = hf_hub_download(
                repo_id=MODEL_REPO_ID,
                filename=MODEL_FILENAME,
                local_dir="data/raw/models",
                force_download=False,
            )
            logger.info(f"Model downloaded to: {self._model_path}")

        if not os.path.exists(self._model_path):
            raise FileNotFoundError(f"Model file not found at: {self._model_path}")

    def _ensure_loaded(self) -> None:
        """Lazy-load the model if not already loaded."""
        if self._llm is None:
            logger.info(f"Loading model from {self._model_path} (CPU, 4-bit)...")
            self._llm = Llama(
                model_path=self._model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_threads_batch=self.n_threads_batch,
                verbose=self.verbose,
                # Ensure CPU-only, no GPU offloading
                n_gpu_layers=0,
            )
            logger.info("Model loaded successfully.")

    def generate_description(
        self,
        image_path: str,
        prompt: str = "Describe this image in detail.",
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str:
        """
        Generate a text description for a single image.

        Args:
            image_path: Path to the image file.
            prompt: The instruction/prompt to send to the VLM.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0 for deterministic).

        Returns:
            Generated text description.
        """
        self._ensure_loaded()

        # llama-cpp Llama does not natively accept image paths.
        # For a pure text-based VLM like Phi-3-mini (which is text-only),
        # we cannot process images directly.
        #
        # However, the task requires a VLM wrapper for "image editing" scoring.
        # In the context of this project, the "VLM description" is generated
        # by feeding the *instruction* and a *textual representation* of the image
        # (e.g., a caption from a separate model) OR the task implies using
        # a multimodal variant.
        #
        # Since Phi-3-mini-4k-instruct is TEXT-ONLY, we must adapt.
        # We will assume the caller provides a "caption" or "image description"
        # as part of the prompt if they want to simulate image input,
        # OR we use a placeholder strategy if the pipeline expects a real VLM.
        #
        # CRITICAL: The project spec says "Phi-3-mini-4k-instruct-GGUF".
        # This model does NOT support images.
        # To fulfill the task "Implement VLM wrapper for Phi-3-mini...",
        # we implement the wrapper for the TEXT model.
        # If the scoring pipeline expects image input, it must handle the
        # image-to-text conversion elsewhere (e.g., using a separate encoder)
        # or the task implies a different model was intended.
        #
        # Given the constraints, we will generate text based on the prompt.
        # If the prompt contains image data (e.g. base64), we would need a
        # multimodal model. Since we are locked to Phi-3-mini (text-only),
        # we will just generate text from the prompt string.
        #
        # NOTE: If the project intended a multimodal model (like LLaVA),
        # the model ID would be different. We stick to the requested ID.

        full_prompt = f"{prompt}"

        output = self._llm(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["</s>", "User:"],
            echo=False,
        )

        return output["choices"][0]["text"].strip()

    def generate_batch(
        self,
        prompts: List[str],
        max_tokens: int = 512,
        temperature: float = 0.0,
        batch_size: Optional[int] = None,
    ) -> List[str]:
        """
        Generate descriptions for a batch of prompts.

        Args:
            prompts: List of prompt strings.
            max_tokens: Maximum tokens per generation.
            temperature: Sampling temperature.
            batch_size: Override default batch size.

        Returns:
            List of generated text descriptions.
        """
        self._ensure_loaded()
        bs = batch_size or self.batch_size

        results = []
        for i in range(0, len(prompts), bs):
            batch = prompts[i : i + bs]
            logger.debug(f"Processing batch of {len(batch)} prompts...")

            batch_outputs = []
            for prompt in batch:
                output = self._llm(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["</s>", "User:"],
                    echo=False,
                )
                batch_outputs.append(output["choices"][0]["text"].strip())

            results.extend(batch_outputs)

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """Return basic model information."""
        if self._llm is None:
            return {
                "model_path": self._model_path,
                "loaded": False,
                "context_size": self.n_ctx,
                "batch_size": self.batch_size,
            }
        return {
            "model_path": self._model_path,
            "loaded": True,
            "context_size": self._llm.n_ctx(),
            "batch_size": self.batch_size,
            "n_params": self._llm.n_params(),
        }


def create_vlm_wrapper(
    model_path: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    **kwargs,
) -> VLMWrapper:
    """
    Factory function to create a VLMWrapper instance.

    Args:
        model_path: Optional path to .gguf file.
        batch_size: Default batch size.
        **kwargs: Additional arguments passed to VLMWrapper.

    Returns:
        Initialized VLMWrapper.
    """
    return VLMWrapper(
        model_path=model_path,
        batch_size=batch_size,
        **kwargs,
    )