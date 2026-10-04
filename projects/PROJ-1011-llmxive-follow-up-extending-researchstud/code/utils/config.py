import os
import random
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
import yaml
from pathlib import Path

from utils.logging_config import get_logger

logger = get_logger("config")

def set_seed(seed: int = 42):
    """
    Sets the random seed for reproducibility across numpy, python random, and torch (if available).
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        logger.debug("PyTorch not found, skipping torch seed setting.")
    
    logger.info(f"Seed set to {seed}")

def get_environment_hash() -> str:
    """
    Generates a hash of the current environment configuration for reproducibility tracking.
    """
    env_vars = {
        "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", ""),
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
    }
    data = json.dumps(env_vars, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()

def validate_seed(seed: int) -> bool:
    """
    Validates that the seed is a non-negative integer.
    """
    return isinstance(seed, int) and seed >= 0

def get_model_config() -> Dict[str, Any]:
    """
    Loads model configuration from data-sources.yaml or a dedicated config file.
    Returns a dictionary with model settings.
    """
    config_path = Path("data-sources.yaml")
    if not config_path.exists():
        logger.warning("data-sources.yaml not found. Using defaults.")
        return {
            "primary_model": "all-MiniLM-L6-v2",
            "fallback_model": "paraphrase-MiniLM-L3-v2",
            "similarity_threshold": 0.5,
            "top_k_patterns": 3
        }
    
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            # Extract model section if it exists, otherwise return defaults
            model_config = data.get("model_config", {})
            # Ensure defaults are present
            defaults = {
                "primary_model": "all-MiniLM-L6-v2",
                "fallback_model": "paraphrase-MiniLM-L3-v2",
                "similarity_threshold": 0.5,
                "top_k_patterns": 3
            }
            return {**defaults, **model_config}
    except Exception as e:
        logger.error(f"Error loading model config: {e}")
        return {
            "primary_model": "all-MiniLM-L6-v2",
            "fallback_model": "paraphrase-MiniLM-L3-v2",
            "similarity_threshold": 0.5,
            "top_k_patterns": 3
        }

def select_model_on_memory_error(primary_model: str, fallback_model: str) -> str:
    """
    Selects the fallback model when memory error occurs.
    """
    logger.warning(f"Memory error on {primary_model}. Selecting {fallback_model}.")
    return fallback_model
