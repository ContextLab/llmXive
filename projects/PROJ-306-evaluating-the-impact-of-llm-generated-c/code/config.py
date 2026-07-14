"""Configuration utilities for the project.

Provides seed management, API key loading, model configuration, and model
resolution/fallback logic.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Seed management
# ---------------------------------------------------------------------------

_SEED: int | None = None

def get_seed() -> int | None:
    """Return the current global seed (may be ``None`` if not set)."""
    return _SEED

def set_seed(seed: int) -> None:
    """Set a global random seed for reproducibility."""
    global _SEED
    _SEED = seed
    random.seed(seed)

# ---------------------------------------------------------------------------
# API key handling
# ---------------------------------------------------------------------------

def get_api_key() -> str | None:
    """Fetch the LLM API key from the environment variable ``LLM_API_KEY``."""
    return os.getenv("LLM_API_KEY")

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    """Simple container for model‑specific configuration."""

    model_name: str
    temperature: float = 0.0
    max_new_tokens: int = 256
    # Additional fields can be added as the project evolves

# Default model chain – primary model followed by fallbacks
_DEFAULT_MODEL_CHAIN: List[str] = [
    "gpt-4",
    "code-llama-7b",
    "bigcode/starcoderbase-3b",
]

def resolve_model(model_name: str) -> str:
    """Return a concrete model identifier.

    For the purpose of this repository the function simply returns the
    supplied name. In a real deployment it could map aliases to full model
    identifiers or perform environment checks.
    """
    return model_name

def get_model_config(model_name: str) -> ModelConfig:
    """Return a :class:`ModelConfig` for *model_name*.

    The function currently only populates the ``model_name`` field; other
    hyper‑parameters retain their defaults.
    """
    return ModelConfig(model_name=resolve_model(model_name))

# ---------------------------------------------------------------------------
# Model fallback chain
# ---------------------------------------------------------------------------

def get_model_chain(candidate_model: str) -> List[str]:
    """Return an ordered list of models to attempt.

    The first element is the *candidate_model* supplied by the caller.
    The remaining elements follow the project‑wide fallback order defined
    in ``_DEFAULT_MODEL_CHAIN`` while avoiding duplicates.

    Example
    -------
    >>> get_model_chain("code-llama-7b")
    ['code-llama-7b', 'gpt-4', 'bigcode/starcoderbase-3b']
    """
    chain = [candidate_model]
    for fallback in _DEFAULT_MODEL_CHAIN:
        if fallback != candidate_model and fallback not in chain:
            chain.append(fallback)
    return chain
