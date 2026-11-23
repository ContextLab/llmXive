"""
Model definitions and initialization logic for Dream-State Learning.

Provides CPU-optimized loaders for DistilBERT and TinyLlama models
with default precision settings.
"""
import torch
from typing import Dict, Any, Optional, Tuple
from transformers import (
    AutoModelForSequenceClassification,
    AutoModelForCausalLM,
    AutoTokenizer,
    AutoConfig,
)
from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# Model registry mapping model names to their initialization functions
MODEL_REGISTRY: Dict[str, str] = {
    "distilbert": "distilbert-base-uncased",
    "tinyllama": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
}

def get_model_type(model_name: str) -> str:
    """
    Determine the model type based on the model name or config.

    Args:
        model_name: The identifier for the model (e.g., 'distilbert', 'tinyllama')

    Returns:
        A string indicating the model architecture type ('seq_class', 'causal_lm')
    """
    if "llama" in model_name.lower() or "tinyllama" in model_name.lower():
        return "causal_lm"
    elif "bert" in model_name.lower():
        return "seq_class"
    else:
        # Default to sequence classification for BERT-like models
        return "seq_class"

def load_model(
    model_name: str,
    config: Config,
    num_labels: Optional[int] = None,
    device: Optional[torch.device] = None,
) -> Tuple[Any, AutoTokenizer]:
    """
    Load a pre-trained model and tokenizer, optimized for CPU execution.

    This function enforces CPU-only execution and default precision (float32)
    as per project constraints. It handles both DistilBERT (for sequence
    classification) and TinyLlama (for causal language modeling).

    Args:
        model_name: The identifier for the model ('distilbert' or 'tinyllama')
        config: The project configuration object containing hyperparameters
        num_labels: Number of classification labels (required for DistilBERT)
        device: The device to load the model onto (defaults to CPU)

    Returns:
        A tuple containing (model, tokenizer)

    Raises:
        ValueError: If the model_name is not recognized or if required
                    parameters are missing for specific model types.
    """
    if device is None:
        # Enforce CPU-only as per project constraints
        device = torch.device("cpu")
        logger.info("Forcing CPU-only device as per project constraints.")

    # Resolve the actual Hugging Face model identifier
    hf_model_id = MODEL_REGISTRY.get(model_name.lower(), model_name)
    model_type = get_model_type(hf_model_id)

    logger.info(f"Loading {model_type} model: {hf_model_id}")
    logger.info(f"Target device: {device}, Precision: float32 (default)")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(hf_model_id)

    # Handle special tokenizer configurations
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model based on type
    if model_type == "seq_class":
        if num_labels is None:
            raise ValueError(
                "num_labels must be provided for sequence classification models."
            )
        model = AutoModelForSequenceClassification.from_pretrained(
            hf_model_id,
            num_labels=num_labels,
        )
    elif model_type == "causal_lm":
        model = AutoModelForCausalLM.from_pretrained(hf_model_id)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

    # Ensure default precision (float32) and move to device
    model = model.float()
    model = model.to(device)

    # Set model to evaluation mode by default; training mode is handled by Trainer
    model.eval()

    logger.info(f"Successfully loaded {model_name} model on {device}.")

    return model, tokenizer

def create_model_from_config(config: Config, num_labels: Optional[int] = None) -> Tuple[Any, AutoTokenizer]:
    """
    Convenience wrapper to load a model using the project's Config object.

    Args:
        config: The project configuration object
        num_labels: Number of classification labels (optional, inferred if possible)

    Returns:
        A tuple containing (model, tokenizer)
    """
    model_name = config.model_name
    device = torch.device("cpu")

    return load_model(model_name, config, num_labels=num_labels, device=device)

__all__ = [
    "load_model",
    "create_model_from_config",
    "get_model_type",
    "MODEL_REGISTRY",
]