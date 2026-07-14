"""Configuration utilities for the LLM code generation pipeline.

This module provides:
- Seed management utilities (`get_seed`, `set_seed`).
- API key loading (`get_api_key`).
- Model configuration handling (`ModelConfig`, `get_model_config`,
  `get_model_chain`, `resolve_model`, `resolve_fallback_model`,
  `get_fallback_chain`).
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from typing import Any, List, Optional

# ---------------------------------------------------------------------------
# Seed management
# ---------------------------------------------------------------------------

_SEED: Optional[int] = None


def get_seed() -> Optional[int]:
    """Return the current random seed (if set)."""
    return _SEED


def set_seed(seed: int) -> None:
    """Set the random seed for `random` and `numpy` (if installed)."""
    global _SEED
    _SEED = seed
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# API key handling
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    """Retrieve the LLM API key from the environment variable `LLM_API_KEY`."""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise EnvironmentError("Environment variable LLM_API_KEY not set.")
    return api_key

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------------
# Model configuration utilities
# ----------------------------------------------------------------------
@dataclass
class ModelConfig:
    """Simple configuration container for a model."""

    name: str
    temperature: float = 0.0
    max_tokens: int = 256
    # Additional fields can be added as needed by downstream code
    extra: dict = field(default_factory=dict)

    The function is tolerant of being called with:
    * a concrete model name (e.g. ``\"gpt-4\"``),
    * ``None`` (meaning “use the default primary model”),
    * an arbitrary string that is not part of the built‑in fallback list.

_FALLBACK_CHAIN = ["code-llama-7b", "bigcode/starcoderbase-3b"]


def get_fallback_chain() -> List[str]:
    """Return the ordered list of fallback model identifiers."""
    return _FALLBACK_CHAIN.copy()


def resolve_fallback_model(model_name: str) -> str:
    """Resolve the next fallback model after ``model_name``."""
    chain = get_fallback_chain()
    try:
        idx = chain.index(model_name)
    except ValueError:
        # If the model is not in the chain, start from the beginning
        return chain[0]
    # Return the next model if available, otherwise the last one
    return chain[min(idx + 1, len(chain) - 1)]

# ---------------------------------------------------------------------------
# Model chain utilities
# ---------------------------------------------------------------------------

def get_model_chain(primary_model: str) -> List[str]:
    """Return the full model chain starting with ``primary_model`` followed by fallbacks."""
    chain = [primary_model]
    # Append the fallback chain in order, skipping duplicates
    for fb in get_fallback_chain():
        if fb != primary_model:
            chain.append(fb)
    return chain

# ---------------------------------------------------------------------------
# Flexible model config getter
# ---------------------------------------------------------------------------

def get_model_config(*args: Any, **kwargs: Any) -> ModelConfig:
    """Return a :class:`ModelConfig` for the requested model.

    Accepts a variety of call signatures:
    - ``get_model_config('gpt-4')``
    - ``get_model_config(model_name='gpt-4')``
    - ``get_model_config(candidate_model='gpt-4')``
    - ``get_model_config(model_name='gpt-4', temperature=0.2, max_tokens=512)``

    Raises:
        ValueError: If no model name can be inferred.
    """
    # Resolve model name from positional or keyword arguments
    model_name: Optional[str] = None
    if args:
        model_name = args[0]
    else:
        model_name = (
            kwargs.get("model_name")
            or kwargs.get("candidate_model")
            or kwargs.get("model")
        )
    if not model_name:
        raise ValueError("Model name must be provided to get_model_config()")

    # Extract optional hyper‑parameters
    temperature = kwargs.get("temperature", 0.0)
    max_tokens = kwargs.get("max_tokens", 256)
    extra = {k: v for k, v in kwargs.items() if k not in {"model_name", "candidate_model", "model", "temperature", "max_tokens"}}

    return ModelConfig(name=model_name, temperature=temperature, max_tokens=max_tokens, extra=extra)