"""Configuration utilities for the LLM code generation pipeline.

This module provides seed handling, API‑key loading, and model resolution.
The original implementation already defined ``ModelConfig``, ``get_seed``,
``set_seed``, ``get_api_key``, and ``resolve_model``.  The missing piece
for the current task is a flexible ``get_model_config`` that can be called
both as ``get_model_config(candidate_model)`` and ``get_model_config(model=…)``.
The implementation below preserves the existing public API while adding
the required tolerant wrapper.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from typing import Any, List, Optional

# --------------------------------------------------------------------------- #
# Existing data structures (kept unchanged)
# --------------------------------------------------------------------------- #
@dataclass
class ModelConfig:
    """Simple container for model configuration."""
    name: str
    provider: str = "openai"
    temperature: float = 0.0
    max_tokens: int = 512
    # Additional fields can be added as needed.

# --------------------------------------------------------------------------- #
# Seed utilities (unchanged)
# --------------------------------------------------------------------------- #
def get_seed() -> int:
    """Return a deterministic seed (could be made configurable later)."""
    return 42

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = get_seed()
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass

# --------------------------------------------------------------------------- #
# API‑key handling (unchanged)
# --------------------------------------------------------------------------- #
def get_api_key() -> str:
    """Load the LLM API key from the environment."""
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise EnvironmentError("LLM_API_KEY not set in environment")
    return key

# --------------------------------------------------------------------------- #
# Model resolution (unchanged)
# --------------------------------------------------------------------------- #
def resolve_model(model_name: str) -> ModelConfig:
    """Map a model identifier to a ``ModelConfig`` instance.

    The fallback chain (gpt‑4 → code‑llama‑7b → bigcode/starcoderbase‑3b)
    is encoded here.
    """
    model_name = model_name.lower()
    if model_name in {"gpt-4", "gpt4"}:
        return ModelConfig(name="gpt-4", provider="openai")
    if model_name in {"code-llama-7b", "code_llama_7b"}:
        return ModelConfig(name="code-llama-7b", provider="huggingface")
    # Default fallback – bigcode/starcoderbase‑3b (4‑bit quantised on CPU)
    return ModelConfig(name="bigcode/starcoderbase-3b", provider="huggingface")

# --------------------------------------------------------------------------- #
# Flexible ``get_model_config`` wrapper (required for T013)
# --------------------------------------------------------------------------- #
def get_model_config(*args: Any, **kwargs: Any) -> ModelConfig:
    """Return a ``ModelConfig`` for the requested model.

    Accepts either a positional argument ``candidate_model`` or a keyword
    argument ``model``.  Any additional arguments are ignored so that the
    function never raises because of an unexpected call shape.
    """
    if args:
        model_name = args[0]
    else:
        model_name = kwargs.get("model")
    if not model_name:
        # Default to the primary model if nothing is supplied.
        model_name = "gpt-4"
    return resolve_model(str(model_name))