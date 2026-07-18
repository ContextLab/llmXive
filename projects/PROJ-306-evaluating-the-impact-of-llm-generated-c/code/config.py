"""
Configuration management for the LLM pipeline.

Handles seed management, API key loading, and model fallback logic.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

CONFIG_PATH = "config.yaml"
DEFAULT_SEED = 42


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    api_endpoint: Optional[str] = None
    api_key_env: Optional[str] = None
    is_local: bool = False
    quantization: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


def get_seed() -> int:
    """Get the random seed from environment or default."""
    return int(os.getenv("SEED", DEFAULT_SEED))


def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    random.seed(seed)
    os.environ["SEED"] = str(seed)


def get_api_key() -> Optional[str]:
    """Load API key from environment variable."""
    return os.getenv("LLM_API_KEY")


def get_model_chain() -> List[str]:
    """
    Returns an ordered list of model names representing the hierarchy
    from proprietary to open-source architectures.
    """
    # Default chain: Proprietary -> Open Source (Local)
    chain = os.getenv("MODEL_CHAIN", "gpt,code-llama-7b")
    return [m.strip() for m in chain.split(",")]


def get_model_fallback_sequence() -> List[ModelConfig]:
    """
    Returns a list of ModelConfig objects representing the fallback chain.
    Attempts to resolve each model in the chain.
    """
    names = get_model_chain()
    configs = []
    for name in names:
        try:
            cfg = resolve_model(name)
            configs.append(cfg)
        except Exception as e:
            # Log warning but continue to next model
            print(f"Warning: Could not resolve model {name}: {e}")
    return configs


def resolve_model(model_name: str) -> ModelConfig:
    """
    Resolve a model name to its configuration.
    Tries to load from config.yaml, then falls back to defaults.
    """
    # Try loading from config file first
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config_data = yaml.safe_load(f)
            models = config_data.get("models", {})
            if model_name in models:
                cfg = models[model_name]
                return ModelConfig(
                    name=model_name,
                    api_endpoint=cfg.get("api_endpoint"),
                    api_key_env=cfg.get("api_key_env"),
                    is_local=cfg.get("is_local", False),
                    quantization=cfg.get("quantization"),
                    parameters=cfg.get("parameters", {})
                )
        except Exception as e:
            print(f"Warning: Could not load config for {model_name}: {e}")

    # Default configurations if not in file
    defaults = {
        "gpt": {
            "api_endpoint": "https://api.openai.com/v1/chat/completions",
            "api_key_env": "LLM_API_KEY",
            "is_local": False,
            "parameters": {"temperature": 0.2, "max_tokens": 512}
        },
        "code-llama-7b": {
            "is_local": True,
            "quantization": "4-bit",
            "parameters": {"temperature": 0.0, "max_tokens": 512}
        }
    }

    if model_name in defaults:
        d = defaults[model_name]
        return ModelConfig(
            name=model_name,
            api_endpoint=d.get("api_endpoint"),
            api_key_env=d.get("api_key_env"),
            is_local=d.get("is_local", False),
            quantization=d.get("quantization"),
            parameters=d.get("parameters", {})
        )

    # Fallback for unknown models
    return ModelConfig(name=model_name, is_local=False)


def get_model_config(model_name: str) -> ModelConfig:
    """
    Wrapper to resolve model configuration.
    Ensures compatibility with callers expecting a config object.
    """
    return resolve_model(model_name)