"""
Configuration management for the llmXive research pipeline.

Handles:
- Seed management for reproducibility
- API key loading from environment variables
- Model fallback logic (gpt-4 -> code-llama-7b -> bigcode/starcoderbase-3b)
"""
import os
import random
import numpy as np
from typing import Optional, List, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Default configuration
DEFAULT_SEED = 42
DEFAULT_MODEL_PRIMARY = "gpt-4"
DEFAULT_MODEL_FALLBACK_1 = "code-llama-7b"
DEFAULT_MODEL_FALLBACK_2 = "bigcode/starcoderbase-3b"

# Model configuration details
MODEL_CONFIGS = {
    DEFAULT_MODEL_PRIMARY: {
        "type": "api",
        "provider": "openai",
        "requires_key": True,
    },
    DEFAULT_MODEL_FALLBACK_1: {
        "type": "local",
        "provider": "huggingface",
        "requires_quantization": False,
        "model_id": "codellama/CodeLlama-7b-Instruct-hf",
    },
    DEFAULT_MODEL_FALLBACK_2: {
        "type": "local",
        "provider": "huggingface",
        "requires_quantization": True,  # Mandatory per SC-005 (7GB RAM limit)
        "model_id": "bigcode/starcoderbase-3b",
        "quantization_bits": 4,
    },
}

# Fallback order
MODEL_FALLBACK_ORDER: List[str] = [
    DEFAULT_MODEL_PRIMARY,
    DEFAULT_MODEL_FALLBACK_1,
    DEFAULT_MODEL_FALLBACK_2,
]


def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch (if available).

    Args:
        seed: The integer seed value to use.
    """
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed, skip


def get_api_key(provider: str = "openai") -> Optional[str]:
    """
    Retrieve the API key for a given provider from environment variables.

    Args:
        provider: The provider name (e.g., 'openai', 'huggingface').

    Returns:
        The API key string if found, None otherwise.
    """
    key_map = {
        "openai": "LLM_API_KEY",
        "huggingface": "HF_TOKEN",
    }
    env_var = key_map.get(provider, f"{provider.upper()}_API_KEY")
    return os.getenv(env_var)


def get_model_config(model_name: str) -> dict:
    """
    Retrieve the configuration for a specific model.

    Args:
        model_name: The name of the model.

    Returns:
        A dictionary containing the model configuration.

    Raises:
        ValueError: If the model name is not found in MODEL_CONFIGS.
    """
    if model_name not in MODEL_CONFIGS:
        raise ValueError(f"Model '{model_name}' not found in configuration.")
    return MODEL_CONFIGS[model_name]


def get_fallback_models() -> List[Tuple[str, dict]]:
    """
    Get the list of fallback models in order with their configurations.

    Returns:
        A list of tuples (model_name, config) representing the fallback chain.
    """
    result = []
    for model_name in MODEL_FALLBACK_ORDER:
        try:
            config = get_model_config(model_name)
            result.append((model_name, config))
        except ValueError:
            # Skip models that are not configured
            continue
    return result


def resolve_model(model_preference: Optional[str] = None) -> Tuple[str, dict]:
    """
    Resolve the actual model to use based on preference and availability.

    Args:
        model_preference: Optional specific model name requested.

    Returns:
        A tuple (model_name, config) for the selected model.

    Logic:
        1. If model_preference is provided and valid, use it.
        2. Otherwise, iterate through MODEL_FALLBACK_ORDER.
        3. For API models, check if API key exists.
        4. Return the first valid model found.
    """
    # 1. Check explicit preference
    if model_preference:
        try:
            config = get_model_config(model_preference)
            # Validate API key if required
            if config.get("requires_key"):
                if not get_api_key(config.get("provider", "openai")):
                    raise ValueError(f"API key missing for {model_preference}")
            return model_preference, config
        except ValueError:
            # If preference is invalid, fall through to default logic
            pass

    # 2. Iterate through fallback order
    for model_name, config in get_fallback_models():
        if config.get("requires_key"):
            if not get_api_key(config.get("provider", "openai")):
                continue  # Skip if API key missing
        
        # For local models, we assume they are available unless specified otherwise
        # (In a real scenario, we might check disk space or GPU availability here)
        return model_name, config

    # Fallback to nothing if all fail
    raise RuntimeError("No valid model found in fallback chain. Check API keys and local model availability.")


# Convenience function for quick access
def get_primary_model() -> str:
    """Returns the name of the primary model."""
    return DEFAULT_MODEL_PRIMARY

def get_fallback_model_1() -> str:
    """Returns the name of the first fallback model."""
    return DEFAULT_MODEL_FALLBACK_1

def get_fallback_model_2() -> str:
    """Returns the name of the second fallback model."""
    return DEFAULT_MODEL_FALLBACK_2