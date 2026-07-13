from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass, field
from typing import List, Optional

# --------------------------------------------------------------------------- #
# Seed management utilities
# --------------------------------------------------------------------------- #
def get_seed() -> int:
    """
    Return a deterministic integer seed derived from the environment.

    Priority:
    1. ``LLM_SEED`` environment variable (must be an integer string).
    2. A hash of the current working directory – stable across runs on the same
       repository location.
    """
    seed_env = os.getenv("LLM_SEED")
    if seed_env and seed_env.isdigit():
        return int(seed_env)
    cwd = os.getcwd()
    return int(hashlib.sha256(cwd.encode()).hexdigest(), 16) % (2**32)


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set seeds for ``random`` (and other libraries if added later) to ensure
    reproducibility across the pipeline.
    """
    if seed is None:
        seed = get_seed()
    random.seed(seed)


# --------------------------------------------------------------------------- #
# API key handling
# --------------------------------------------------------------------------- #
def get_api_key() -> str:
    """
    Retrieve the LLM API key from the environment.

    Raises
    ------
    EnvironmentError
        If ``LLM_API_KEY`` is not defined.
    """
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise EnvironmentError("LLM_API_KEY not set in environment")
    return key


# --------------------------------------------------------------------------- #
# Model configuration structures
# --------------------------------------------------------------------------- #
@dataclass
class ModelConfig:
    """
    Container for model configuration used by the generation pipeline.
    """
    name: str
    fallback_chain: List[str] = field(
        default_factory=lambda: ["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"]
    )
    api_key: Optional[str] = None
    temperature: float = 0.0
    max_new_tokens: int = 256


@dataclass
class Config:
    """
    Global configuration used throughout the pipeline.
    """
    seed: int = field(default_factory=get_seed)
    api_key: str = field(default_factory=get_api_key)
    model_config: ModelConfig = field(
        default_factory=lambda: ModelConfig(name="gpt-4")
    )


# --------------------------------------------------------------------------- #
# Helper functions for model availability & resolution
# --------------------------------------------------------------------------- #
_KNOWN_MODELS = {"gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"}


def _is_model_available(name: str) -> bool:
    """
    Determine whether a model is “available”.

    For the purposes of this repository we treat all known models as available.
    In a real deployment this could query the HuggingFace hub, an OpenAI endpoint,
    or look for locally‑installed binaries.
    """
    return name in _KNOWN_MODELS


def get_model_chain(candidate: str) -> List[str]:
    """
    Return a fallback chain for *candidate*.

    The default chain is ``["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"]``.
    If *candidate* is recognised, it is moved to the front while preserving the
    order of the remaining models.
    """
    default_chain = ["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"]
    if candidate in default_chain:
        chain = [candidate] + [m for m in default_chain if m != candidate]
    else:
        chain = default_chain
    return chain


def resolve_model(candidate: str) -> str:
    """
    Resolve *candidate* to the first *available* model in its fallback chain.

    The function:
    1. Builds the candidate's fallback chain via :func:`get_model_chain`.
    2. Returns the first model in that chain for which ``_is_model_available`` is
       ``True``.
    3. If none are available (highly unlikely in this limited context), it raises
       a ``RuntimeError``.
    """
    chain = get_model_chain(candidate)
    for model_name in chain:
        if _is_model_available(model_name):
            return model_name
    raise RuntimeError(
        f"No available model found for candidate '{candidate}'. "
        f"Tried chain: {chain}"
    )


# --------------------------------------------------------------------------- #
# Public API required by other modules
# --------------------------------------------------------------------------- #
def get_model_config(candidate_model: Optional[str] = None) -> ModelConfig:
    """
    Return a :class:`ModelConfig` for *candidate_model* respecting the fallback order.

    Parameters
    ----------
    candidate_model : str | None
        The explicitly requested model.  If ``None`` or empty, the default model
        ``gpt-4`` (the first element of the default chain) is used.

    Returns
    -------
    ModelConfig
        An instance with ``name`` set to the resolved model and ``fallback_chain``
        reflecting the full ordered list of candidates.
    """
    if not candidate_model:
        # No explicit request – use the default chain's first element.
        resolved_name = "gpt-4"
        fallback = ["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"]
    else:
        candidate_model = candidate_model.strip()
        resolved_name = resolve_model(candidate_model)
        fallback = get_model_chain(candidate_model)

    return ModelConfig(name=resolved_name, fallback_chain=fallback)


__all__ = [
    "get_seed",
    "set_seed",
    "get_api_key",
    "ModelConfig",
    "Config",
    "get_model_chain",
    "resolve_model",
    "get_model_config",
]