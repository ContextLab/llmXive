"""
Configuration utilities for the LLM‑code‑coverage project.

This module defines data classes for model configuration, provides a simple
seed manager, and exposes ``get_model_config`` with a flexible signature
that satisfies all current call‑sites:

* ``get_model_config()`` – returns the fallback configuration.
* ``get_model_config(candidate_model)`` – returns a configuration for the
  explicitly requested model.
* ``get_model_config().fallback_model`` – attribute access used in
  ``code/main.py``.
* ``get_model_config(args.model)`` – used when the model name is supplied
  via the command line.
"""

import os
import random
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from types import SimpleNamespace

# --------------------------------------------------------------------------- #
# Seed management
# --------------------------------------------------------------------------- #

_SEED: Optional[int] = None

def set_seed(seed: int) -> None:
    """Globally set the random seed for reproducibility."""
    global _SEED
    _SEED = seed
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:  # pragma: no cover
        pass

def get_seed() -> Optional[int]:
    """Return the currently configured seed (or ``None`` if not set)."""
    return _SEED

# --------------------------------------------------------------------------- #
# API key handling
# --------------------------------------------------------------------------- #

def get_api_key() -> str:
    """Retrieve the LLM API key from the environment."""
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise EnvironmentError("LLM_API_KEY environment variable not set")
    return key

# --------------------------------------------------------------------------- #
# Model configuration data‑class
# --------------------------------------------------------------------------- #

@dataclass
class ModelConfig:
    """Configuration for a single model."""
    model_name: str
    temperature: float = 0.0
    max_new_tokens: int = 256
    # Additional fields can be added as needed.

@dataclass
class Config:
    """
    Global configuration container.

    ``fallback_model`` is the default model used when no explicit model is
    supplied.  The value can be overridden via the ``DEFAULT_MODEL`` env
    variable.
    """
    fallback_model: str = field(
        default_factory=lambda: os.getenv("DEFAULT_MODEL", "gpt-4")
    )
    # Mapping from model identifier to a ``ModelConfig`` instance.
    model_registry: Dict[str, ModelConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Populate a minimal registry with the fallback model so that
        # ``get_model_config`` can always return a valid ``ModelConfig``.
        if self.fallback_model not in self.model_registry:
            self.model_registry[self.fallback_model] = ModelConfig(
                model_name=self.fallback_model
            )

# Global config instance – lazily instantiated on first use.
_GLOBAL_CONFIG: Optional[Config] = None

def _get_global_config() -> Config:
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = Config()
    return _GLOBAL_CONFIG

# --------------------------------------------------------------------------- #
# Model configuration accessor (flexible signature)
# --------------------------------------------------------------------------- #

def get_model_config(*args, **kwargs) -> SimpleNamespace:
    """
    Retrieve a model configuration.

    The function is deliberately tolerant of the various call patterns used
    throughout the code base:

    * ``get_model_config()`` – returns the fallback configuration.
    * ``get_model_config(candidate_model)`` – returns configuration for the
      supplied model identifier.
    * ``get_model_config(model_name=...)`` – keyword style (future‑proof).

    The return value is a ``SimpleNamespace`` with at least the attributes
    ``model_name`` and ``fallback_model`` so that existing code can access
    either attribute without error.
    """
    # Resolve the requested model name, if any.
    model_name: Optional[str] = None
    if args:
        model_name = args[0]
    elif "model_name" in kwargs:
        model_name = kwargs["model_name"]

    cfg = _get_global_config()
    fallback = cfg.fallback_model

    # Determine which model to use.
    selected_name = model_name if model_name else fallback

    # Retrieve (or create) the concrete ModelConfig.
    if selected_name not in cfg.model_registry:
        # If the requested model is unknown we still create a minimal entry
        # so downstream code does not fail.
        cfg.model_registry[selected_name] = ModelConfig(model_name=selected_name)

    selected_cfg = cfg.model_registry[selected_name]

    # Return a lightweight namespace that provides both the explicit model
    # name and the fallback for convenience.
    return SimpleNamespace(
        model_name=selected_cfg.model_name,
        temperature=selected_cfg.temperature,
        max_new_tokens=selected_cfg.max_new_tokens,
        fallback_model=fallback,
    )
