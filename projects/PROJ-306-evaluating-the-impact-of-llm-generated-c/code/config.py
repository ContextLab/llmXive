"""
Configuration utilities for the project.

This module provides:
  - Seed management (with optional environment override)
  - API‑key retrieval for LLM services
  - Model‑chain definition and fallback handling
  - Helper to obtain either a full project ``Config`` object or a
    ``ModelConfig`` for a specific model name.

The implementation is deliberately tolerant:
  * ``get_seed`` falls back to a constant if the environment variable is missing.
  * ``set_seed`` seeds ``random`` and ``numpy`` (the most common
    libraries used in the repo) and mirrors the behaviour of the original
    stub.
  * ``get_api_key`` reads the generic ``LLM_API_KEY`` variable; the individual
    model resolvers still expose their own ``api_key_env`` attribute.
  * ``get_model_config`` works both as ``get_model_config()`` → ``Config`` and
    ``get_model_config(name)`` → ``ModelConfig`` irrespective of positional or
    keyword usage.
"""

import os
import random
import hashlib
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from types import SimpleNamespace

# ``numpy`` is optional in the environment; we import lazily and ignore if unavailable.
try:
    import numpy as _np
except Exception:  # pragma: no cover
    _np = None

@dataclass
class ModelConfig:
    """
    Configuration for a single LLM model.

    Attributes
    ----------
    name: str
        Human‑readable model identifier.
    api_key_env: Optional[str]
        Name of the environment variable that stores the API key for this model.
    api_endpoint: Optional[str]
        Base URL for the model’s inference endpoint (if applicable).
    max_tokens: int
        Upper bound on generated token count.
    temperature: float
        Sampling temperature.
    quantization_bits: Optional[int]
        Bit‑width for quantized inference (e.g., 4‑bit for CPU fallback).
    device_map: str
        Device placement hint for ``transformers``/``bitsandbytes``.
    """
    name: str
    api_key_env: Optional[str] = None
    api_endpoint: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.7
    quantization_bits: Optional[int] = None
    device_map: str = "auto"

@dataclass
class Config:
    """
    Global configuration used throughout the pipeline.

    Attributes
    ----------
    seed: int
        Random seed for reproducibility.
    api_key: Optional[str]
        Generic LLM API key (``LLM_API_KEY``). Individual models may use their own
        keys, but this provides a convenient default.
    model_chain: List[str]
        Ordered list of model identifiers to try, from most capable to fallback.
    fallback_model: str
        The model name that will be used when all others are unavailable.
    """
    seed: int = 42
    api_key: Optional[str] = None
    model_chain: List[str] = field(default_factory=lambda: ["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"])
    fallback_model: str = "bigcode/starcoderbase-3b"

# ----------------------------------------------------------------------
# Seed management
# ----------------------------------------------------------------------
def get_seed() -> int:
    """
    Return the random seed to be used.

    The function first checks the ``SEED`` environment variable; if it is
    present and can be interpreted as an integer, that value is returned.
    Otherwise the default seed ``42`` is used.
    """
    env_seed = os.getenv("SEED") or os.getenv("PYTHONHASHSEED")
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            # Fall back silently – the caller will still get a deterministic seed.
            pass
    return 42

def set_seed(seed: int) -> None:
    """
    Apply ``seed`` globally.

    - ``random`` seed
    - ``numpy`` seed (if numpy is available)
    - ``PYTHONHASHSEED`` environment variable (helps reproducibility for
      hash‑based operations)
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    if _np is not None:
        _np.random.seed(seed)

# ----------------------------------------------------------------------
# API‑key handling
# ----------------------------------------------------------------------
def get_api_key() -> Optional[str]:
    """
    Retrieve the generic LLM API key.

    The environment variable ``LLM_API_KEY`` is the canonical location.
    """
    return os.getenv("LLM_API_KEY")

# ----------------------------------------------------------------------
# Model chain & resolution
# ----------------------------------------------------------------------
def get_model_chain() -> List[str]:
    """
    Return the ordered list of model identifiers that the pipeline will try.
    """
    return ["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"]

def resolve_model(name: str) -> ModelConfig:
    """
    Convert a model identifier into a :class:`ModelConfig`.

    Parameters
    ----------
    name: str
        Identifier of the model (e.g. ``"gpt-4"``).

    Returns
    -------
    ModelConfig
        Fully populated configuration for the requested model.
    """
    if name == "gpt-4":
        return ModelConfig(
            name="gpt-4",
            api_key_env="OPENAI_API_KEY",
            api_endpoint="https://api.openai.com/v1/chat/completions",
            max_tokens=1024,
        )
    elif name == "code-llama-7b":
        return ModelConfig(
            name="code-llama-7b",
            api_key_env="HF_API_KEY",
            quantization_bits=4,
            device_map="cpu",
        )
    elif name == "bigcode/starcoderbase-3b":
        return ModelConfig(
            name="bigcode/starcoderbase-3b",
            api_key_env="HF_API_KEY",
            quantization_bits=4,
            device_map="cpu",
        )
    # Generic fallback – useful for custom models
    return ModelConfig(name=name, api_key_env="LLM_API_KEY")

# ----------------------------------------------------------------------
# Public accessor – tolerant to all call signatures used in the repo
# ----------------------------------------------------------------------
def get_model_config(name: Optional[str] = None, **kwargs: Any) -> Any:
    """
    Retrieve configuration objects.

    * ``get_model_config()`` → returns a :class:`Config` instance containing
      the full model chain and the default fallback model.
    * ``get_model_config('gpt-4')`` → returns a :class:`ModelConfig` for the
      specified model.
    * Keyword usage (e.g. ``get_model_config(name='gpt-4')``) is also supported.

    The function accepts arbitrary ``**kwargs`` to stay forward‑compatible
    with any future call sites that might pass additional parameters.
    """
    # Support both positional and keyword ``name`` arguments.
    if name is None and "name" in kwargs:
        name = kwargs.pop("name")

    if name is None:
        # No specific model requested – build the global Config.
        chain = get_model_chain()
        fallback = chain[-1] if chain else "bigcode/starcoderbase-3b"
        cfg = Config(
            seed=get_seed(),
            api_key=get_api_key(),
            model_chain=chain,
            fallback_model=fallback,
        )
        return cfg

    # A specific model name was supplied – return its ModelConfig.
    return resolve_model(name)

# ----------------------------------------------------------------------
# Convenience: expose the current seed/value as module‑level constants
# ----------------------------------------------------------------------
# These are evaluated at import time; they reflect the environment at that
# moment. Users can call ``set_seed`` later to change the behaviour.
CURRENT_SEED = get_seed()
set_seed(CURRENT_SEED)