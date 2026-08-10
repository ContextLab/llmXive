import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from huggingface_hub import hf_hub_download

# Dynamic import to avoid hard dependency if not installed,
# but we assume it is installed per requirements.txt
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None  # type: ignore

from src.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL_REPO = "Microsoft/Phi-3-mini-4k-instruct-gguf"
DEFAULT_MODEL_FILE = "Phi-3-mini-4k-instruct-q4.gguf"
DEFAULT_BATCH_SIZE = 8
DEFAULT_N_CTX = 4096
DEFAULT_N_THREADS = 4

class VLMWrapper:
    """
    Wrapper for Phi-3-mini-4k-instruct-GGUF using llama-cpp-python.
    Optimized for CPU-only inference.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: int = DEFAULT_N_CTX,
        n_threads: int = DEFAULT_N_THREADS,
        verbose: bool = False,
    ):
        if Llama is None:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Please install it via requirements.txt."
            )

        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.verbose = verbose
        self.model: Optional[Llama] = None
        self._is_loaded = False

        if self.model_path:
            self.load_model()

    def load_model(self) -> None:
        """
        Load the GGUF model from the specified path or download it.
        """
        if self._is_loaded:
            logger.warning("Model already loaded.")
            return

        path_to_use = self.model_path

        # If no path provided, try to download from HuggingFace
        if not path_to_use:
            logger.info(f"Downloading model from {DEFAULT_MODEL_REPO}...")
            try:
                path_to_use = hf_hub_download(
                    repo_id=DEFAULT_MODEL_REPO,
                    filename=DEFAULT_MODEL_FILE,
                    local_dir="data/models",
                    local_dir_use_symlinks=False,
                )
                logger.info(f"Model downloaded to {path_to_use}")
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                raise

        if not os.path.exists(path_to_use):
            raise FileNotFoundError(f"Model file not found: {path_to_use}")

        logger.info(f"Loading model from {path_to_use} (threads={self.n_threads})...")
        self.model = Llama(
            model_path=path_to_use,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            verbose=self.verbose,
            use_mmap=True,
            use_mlock=False,
        )
        self._is_loaded = True
        logger.info("Model loaded successfully.")

    def generate_description(
        self,
        instruction: str,
        source_image_path: Optional[Union[str, Path]] = None,
        edited_image_path: Optional[Union[str, Path]] = None,
        max_tokens: int = 512,
        batch_size: int = 1,
    ) -> str:
        """
        Generate a text description based on the instruction and optional images.
        Since Phi-3-mini GGUF is text-only, we treat images as text references or skip them.
        For this specific task (T017), we focus on text-based generation as the model
        is a text-only instruction model.
        """
        if not self._is_loaded:
            self.load_model()

        # Construct prompt
        prompt = f"<|user|>\n{instruction}<|end|>\n<|assistant|>\n"

        output = self.model(
            prompt,
            max_tokens=max_tokens,
            stop=["<|end|>", "<|user|>"],
            echo=False,
        )

        return output["choices"][0]["text"].strip()

    def generate_batch(
        self,
        instructions: List[str],
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_tokens: int = 512,
    ) -> List[str]:
        """
        Generate descriptions for a batch of instructions.
        """
        if not self._is_loaded:
            self.load_model()

        results = []
        for i in range(0, len(instructions), batch_size):
            batch = instructions[i : i + batch_size]
            for instruction in batch:
                desc = self.generate_description(
                    instruction=instruction, max_tokens=max_tokens
                )
                results.append(desc)
        return results

    def get_model_info(self) -> Dict[str, Any]:
        """
        Return basic model information.
        """
        if not self._is_loaded:
            return {
                "loaded": False,
                "model_path": self.model_path,
                "n_ctx": self.n_ctx,
                "n_threads": self.n_threads,
            }
        return {
            "loaded": True,
            "model_path": self.model_path,
            "n_ctx": self.n_ctx,
            "n_threads": self.n_threads,
            "vocab_size": self.model.vocab_size if self.model else None,
            "n_embd": self.model.n_embd if self.model else None,
        }


def create_vlm_wrapper(
    model_path: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    n_ctx: int = DEFAULT_N_CTX,
    n_threads: int = DEFAULT_N_THREADS,
) -> VLMWrapper:
    """
    Factory function to create a VLMWrapper instance.
    """
    return VLMWrapper(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
    )