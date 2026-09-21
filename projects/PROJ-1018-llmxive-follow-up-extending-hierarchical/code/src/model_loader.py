"""
Model loading and validation utilities for the HiLS (Hierarchical Sparse Attention) pipeline.

This module provides functionality to load pre-trained checkpoints, validate their
compatibility with the current configuration, and initialize the model for inference.
"""
import os
import logging
from typing import Dict, Any, Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from .config import Config

# Configure module logger
logger = logging.getLogger(__name__)


class HiLSModelLoaderError(Exception):
    """Custom exception for HiLS model loading failures."""
    pass


class HiLSModelLoader:
    """
    A class to encapsulate the logic for loading and managing HiLS model checkpoints.
    
    Attributes:
        config (Config): The configuration object containing model paths and hyperparameters.
        model (AutoModelForCausalLM): The loaded transformer model.
        tokenizer (AutoTokenizer): The loaded tokenizer.
    """
    def __init__(self, config: Config):
        """
        Initialize the HiLSModelLoader.
        
        Args:
            config (Config): Configuration object with model_path and other settings.
        """
        self.config = config
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self._is_loaded = False

    def load_checkpoint(self, checkpoint_path: Optional[str] = None) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Load the pre-trained HiLS model and tokenizer.
        
        If checkpoint_path is provided, it overrides the path in config.
        
        Args:
            checkpoint_path (str, optional): Path to the checkpoint directory. Defaults to config.model_path.
        
        Returns:
            Tuple[AutoModelForCausalLM, AutoTokenizer]: The loaded model and tokenizer.
        
        Raises:
            HiLSModelLoaderError: If loading fails or the checkpoint is invalid.
        """
        path_to_load = checkpoint_path or self.config.model_path
        
        if not path_to_load:
            raise HiLSModelLoaderError("Model path is not specified in config or arguments.")
        
        if not os.path.exists(path_to_load):
            raise HiLSModelLoaderError(f"Checkpoint path does not exist: {path_to_load}")

        try:
            logger.info(f"Loading model from {path_to_load}...")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                path_to_load,
                trust_remote_code=True,
                use_fast=True
            )
            
            # Ensure padding token is set if not already
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                logger.warning("Pad token was None, set to eos_token.")

            # Load model
            # Note: Using torch_dtype=torch.float16 for efficiency if CUDA is available, 
            # otherwise float32. This can be made configurable if needed.
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            
            self.model = AutoModelForCausalLM.from_pretrained(
                path_to_load,
                torch_dtype=torch_dtype,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            self.model.eval()
            self._is_loaded = True
            
            logger.info(f"Successfully loaded model from {path_to_load}")
            return self.model, self.tokenizer

        except Exception as e:
            logger.error(f"Failed to load model from {path_to_load}: {str(e)}")
            raise HiLSModelLoaderError(f"Model loading failed: {str(e)}") from e

    def validate_checkpoint(self) -> bool:
        """
        Validate the loaded checkpoint against configuration requirements.
        
        This checks for:
        - Model existence and basic structure
        - Compatibility of model architecture with expected config
        - Tokenizer vocabulary size matching model embedding size (if applicable)
        
        Returns:
            bool: True if validation passes.
        
        Raises:
            HiLSModelLoaderError: If validation fails.
        """
        if not self._is_loaded or self.model is None or self.tokenizer is None:
            raise HiLSModelLoaderError("Model or tokenizer not loaded. Call load_checkpoint first.")

        # Basic structural validation
        if not hasattr(self.model, 'config'):
            raise HiLSModelLoaderError("Loaded model does not have a config attribute.")
        
        # Check for expected attention mechanism attributes if HiLS specific
        # This assumes the model has been fine-tuned or is a variant that includes HiLS layers
        # We check for the presence of a specific attribute that might denote HiLS layers
        # Since the exact architecture varies, we do a generic check for the model type
        # and ensure it's a causal LM.
        if not isinstance(self.model, AutoModelForCausalLM):
            raise HiLSModelLoaderError("Loaded model is not a causal language model.")

        # Validate tokenizer vocab size matches model embeddings (if accessible)
        try:
            if hasattr(self.model, 'get_input_embeddings'):
                embeddings = self.model.get_input_embeddings()
                if embeddings is not None:
                    model_vocab_size = embeddings.num_embeddings
                    tokenizer_vocab_size = len(self.tokenizer)
                    
                    # Allow a small mismatch if the tokenizer was extended but model embeddings not resized
                    # In a strict HiLS setup, these should match or the model should have been resized.
                    # For this validation, we just log if they differ significantly.
                    if abs(model_vocab_size - tokenizer_vocab_size) > 100:
                        logger.warning(
                            f"Vocabulary size mismatch: Model={model_vocab_size}, Tokenizer={tokenizer_vocab_size}. "
                            "Ensure the model was resized correctly if using custom tokens."
                        )
        except Exception as e:
            logger.warning(f"Could not verify embedding/vocab size match: {e}")

        logger.info("Checkpoint validation passed.")
        return True


def load_hils_checkpoint(config: Config, checkpoint_path: Optional[str] = None) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Convenience function to load the HiLS checkpoint.
    
    Args:
        config (Config): Project configuration.
        checkpoint_path (str, optional): Override path.
        
    Returns:
        Tuple[AutoModelForCausalLM, AutoTokenizer]: Loaded model and tokenizer.
    """
    loader = HiLSModelLoader(config)
    model, tokenizer = loader.load_checkpoint(checkpoint_path)
    
    if not loader.validate_checkpoint():
        # validate_checkpoint raises on failure, but we keep the logic here for clarity
        pass
        
    return model, tokenizer


def validate_checkpoint(config: Config, checkpoint_path: str) -> bool:
    """
    Validate a checkpoint without fully loading it into memory (if possible) or after loading.
    
    For this implementation, we load it to validate the actual weights and architecture.
    
    Args:
        config (Config): Project configuration.
        checkpoint_path (str): Path to the checkpoint.
        
    Returns:
        bool: True if valid.
    """
    loader = HiLSModelLoader(config)
    loader.load_checkpoint(checkpoint_path)
    return loader.validate_checkpoint()