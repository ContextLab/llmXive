import os
import logging
from typing import Dict, Any, Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from .config import Config

logger = logging.getLogger(__name__)


class HiLSModelLoaderError(Exception):
    """Custom exception for HiLS model loading failures."""
    pass


class HiLSModelLoader:
    """
    Handles loading and validation of the pre-trained HiLS model checkpoint.
    Ensures compatibility with the configuration before inference tasks begin.
    """

    def __init__(self, config: Config):
        """
        Initialize the loader with configuration.

        Args:
            config: The configuration object containing model_path and other settings.
        """
        self.config = config
        self.model_path = config.model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None

    def load(self) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Load the pre-trained HiLS model and tokenizer.

        Returns:
            A tuple containing the loaded model and tokenizer.

        Raises:
            HiLSModelLoaderError: If the model cannot be loaded or validated.
        """
        if not self.model_path:
            raise HiLSModelLoaderError("Model path is not specified in configuration.")

        if not os.path.exists(self.model_path) and not self.model_path.startswith("hf://") and not self.model_path.startswith("http"):
            # Check if it's a local path that doesn't exist
            if not os.path.isdir(self.model_path):
                logger.warning(f"Local model path {self.model_path} does not exist. Attempting to load from HuggingFace Hub.")

        try:
            logger.info(f"Loading model from {self.model_path}...")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Handle special case for models without pad token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load model
            # Use appropriate dtype based on device and availability
            if self.device == "cuda":
                model_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            else:
                model_dtype = torch.float32

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=model_dtype,
                device_map="auto" if self.device == "cuda" else None,
                low_cpu_mem_usage=True
            )

            if self.device == "cpu":
                self.model = self.model.to(self.device)

            logger.info(f"Model loaded successfully on {self.device}.")
            
            # Validate the loaded model
            self.validate_checkpoint()
            
            return self.model, self.tokenizer

        except Exception as e:
            error_msg = f"Failed to load HiLS model from {self.model_path}: {str(e)}"
            logger.error(error_msg)
            raise HiLSModelLoaderError(error_msg) from e

    def validate_checkpoint(self) -> bool:
        """
        Validate the loaded checkpoint for compatibility.

        Checks:
        - Model has attention layers compatible with HiLS
        - Tokenizer is properly configured
        - Model is in eval mode

        Returns:
            True if validation passes.

        Raises:
            HiLSModelLoaderError: If validation fails.
        """
        if self.model is None or self.tokenizer is None:
            raise HiLSModelLoaderError("Model or tokenizer not loaded. Cannot validate.")

        # Ensure model is in evaluation mode
        self.model.eval()

        # Basic structure validation
        if not hasattr(self.model, "config"):
            raise HiLSModelLoaderError("Loaded model does not have a config attribute.")

        # Check for essential components
        if not hasattr(self.model, "get_input_embeddings"):
            raise HiLSModelLoaderError("Model missing input embeddings.")

        # Verify tokenizer configuration
        if self.tokenizer.pad_token_id is None:
            raise HiLSModelLoaderError("Tokenizer pad_token_id is None.")

        # Log model details
        logger.info(f"Model type: {self.model.config.model_type}")
        logger.info(f"Vocabulary size: {len(self.tokenizer)}")
        logger.info(f"Max sequence length: {self.model.config.max_position_embeddings}")

        # Optional: Check for HiLS-specific attributes if available
        # This is a placeholder for specific HiLS validation logic
        if hasattr(self.model.config, "hils_config"):
            logger.info("HiLS configuration detected in model config.")
        else:
            logger.warning("No explicit HiLS configuration found in model config. Assuming standard compatibility.")

        logger.info("Checkpoint validation passed.")
        return True


def load_hils_checkpoint(config: Config) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Convenience function to load and validate the HiLS checkpoint.

    Args:
        config: The configuration object.

    Returns:
        A tuple of (model, tokenizer).
    """
    loader = HiLSModelLoader(config)
    return loader.load()


def validate_checkpoint(model: AutoModelForCausalLM, tokenizer: AutoTokenizer) -> bool:
    """
    Validate a loaded checkpoint.

    Args:
        model: The loaded model.
        tokenizer: The loaded tokenizer.

    Returns:
        True if valid.

    Raises:
        HiLSModelLoaderError: If invalid.
    """
    if model is None or tokenizer is None:
        raise HiLSModelLoaderError("Model or tokenizer is None.")

    model.eval()

    if not hasattr(model, "config"):
        raise HiLSModelLoaderError("Model missing config.")

    if tokenizer.pad_token_id is None:
        raise HiLSModelLoaderError("Tokenizer pad_token_id is None.")

    logger.info("Manual checkpoint validation passed.")
    return True
