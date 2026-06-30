"""
Configuration management for the LLM Code Coverage Evaluation pipeline.

Handles:
- Seed management for reproducibility
- API key loading from environment variables
- Model fallback logic (gpt-4 -> code-llama-7b -> bigcode/starcoderbase-3b)
"""
import os
import random
import hashlib
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Constants
DEFAULT_SEED = 42
FALLBACK_MODEL_CHAIN = [
    "gpt-4",
    "code-llama-7b",
    "bigcode/starcoderbase-3b"
]

@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    is_local: bool = False
    requires_quantization: bool = False
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.95

class Config:
    """
    Centralized configuration manager.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Initialize seed
        self.seed = int(os.getenv("LLM_XIVE_SEED", DEFAULT_SEED))
        self._set_seeds(self.seed)

        # Load API Key
        self.api_key = os.getenv("LLM_API_KEY")
        if not self.api_key:
            # Warn but do not fail immediately; allow fallback to local models
            print("Warning: LLM_API_KEY not found in environment. Local models will be used if available.")

        # Define model configurations
        self.models: Dict[str, ModelConfig] = {
            "gpt-4": ModelConfig(
                name="gpt-4",
                is_local=False,
                max_tokens=2048,
                temperature=0.0 # Deterministic for evaluation
            ),
            "code-llama-7b": ModelConfig(
                name="code-llama-7b",
                is_local=True,
                requires_quantization=True,
                max_tokens=1024,
                temperature=0.7
            ),
            "bigcode/starcoderbase-3b": ModelConfig(
                name="bigcode/starcoderbase-3b",
                is_local=True,
                requires_quantization=True, # Mandatory for 7GB RAM limit
                max_tokens=1024,
                temperature=0.7
            )
        }

    def _set_seeds(self, seed: int):
        """Set random seeds for reproducibility."""
        random.seed(seed)
        try:
            import numpy as np
            np.random.seed(seed)
        except ImportError:
            pass
        
        # Try to set torch seeds if available
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass

    def set_seed(self, seed: int):
        """Update the seed and re-seed all libraries."""
        self.seed = seed
        self._set_seeds(seed)

    def get_api_key(self) -> Optional[str]:
        """Retrieve the API key."""
        return self.api_key

    def get_fallback_chain(self) -> List[str]:
        """Return the ordered list of model names to try."""
        return FALLBACK_MODEL_CHAIN.copy()

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model name."""
        return self.models.get(model_name)

    def resolve_model(self, preferred: Optional[str] = None) -> ModelConfig:
        """
        Resolve the best available model based on preference and availability.
        
        Logic:
        1. If preferred is provided and valid, use it.
        2. Otherwise, iterate through the fallback chain.
        3. If a model is local, we assume it's available (configures loading).
        4. If a model requires API key and key is missing, skip it.
        
        Returns the ModelConfig for the chosen model.
        """
        candidates = []
        if preferred:
            if preferred in self.models:
                candidates.append(preferred)
            else:
                # If preferred is not in our known list, add it as a generic entry
                # but mark it as unknown config (caller must handle)
                candidates.append(preferred)
        
        candidates.extend([m for m in FALLBACK_MODEL_CHAIN if m not in candidates])

        for model_name in candidates:
            if model_name not in self.models:
                # Unknown model, assume remote API
                if not self.api_key:
                    continue # Cannot use remote model without key
                # Create a temporary config for unknown models
                return ModelConfig(name=model_name, is_local=False)
            
            config = self.models[model_name]
            if config.is_local:
                # Local models are always "available" in terms of config
                # (actual loading happens in llm_generator)
                return config
            else:
                # Remote model
                if self.api_key:
                    return config
                # Skip if no API key
                continue

        raise RuntimeError(
            "No suitable model found. "
            "Either provide an LLM_API_KEY for remote models or ensure local models are configured."
        )

# Global singleton instance
config = Config()

def get_seed() -> int:
    """Helper to get current seed."""
    return config.seed

def get_api_key() -> Optional[str]:
    """Helper to get API key."""
    return config.get_api_key()

def get_model_chain() -> List[str]:
    """Helper to get model fallback chain."""
    return config.get_fallback_chain()

def get_model_config(name: str) -> Optional[ModelConfig]:
    """Helper to get model config."""
    return config.get_model_config(name)

def resolve_model(preferred: Optional[str] = None) -> ModelConfig:
    """Helper to resolve the best model."""
    return config.resolve_model(preferred)

def set_seed(seed: int):
    """Helper to set seed."""
    config.set_seed(seed)