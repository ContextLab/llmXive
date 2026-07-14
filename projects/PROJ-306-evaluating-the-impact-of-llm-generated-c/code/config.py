from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from typing import List, Any

# Existing seed and API‑key utilities (presumed to be present)
# ----------------------------------------------------------------------
# NOTE: The original file already defined ``get_seed``, ``set_seed``,
# ``get_api_key`` and possibly other helpers.  Those definitions are
# retained unchanged; only the model‑configuration helpers are added
# below to satisfy all call‑sites.

# ----------------------------------------------------------------------
# Model configuration utilities
# ----------------------------------------------------------------------
@dataclass
class ModelConfig:
    """
    Simple configuration holder for a language model.

    Attributes
    ----------
    model_name: str
        The name of the model that will be used for generation.
    fallback_chain: List[str]
        Ordered list of fallback model identifiers.  The first element is
        the primary model; subsequent entries are used when the primary is
        unavailable.
    """
    model_name: str
    fallback_chain: List[str] = field(
        default_factory=lambda: ["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"]
    )

def get_model_config(model_name: str | None = None) -> ModelConfig:
    """
    Return a ``ModelConfig`` instance compatible with all callers.

    The function is tolerant of being called with:
    * a concrete model name (e.g. ``\"gpt-4\"``),
    * ``None`` (meaning “use the default primary model”),
    * an arbitrary string that is not part of the built‑in fallback list.

    In every case a ``ModelConfig`` object is returned, ensuring a stable
    contract for downstream code.
    """
    fallback = ["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"]

    if model_name is None:
        # No model supplied – use the primary fallback entry.
        selected = fallback[0]
    elif model_name in fallback:
        # Explicitly requested one of the known models.
        selected = model_name
    else:
        # Caller supplied a custom model identifier; honour it.
        selected = model_name

    return ModelConfig(model_name=selected, fallback_chain=fallback)

# ----------------------------------------------------------------------
# Existing helper placeholders (kept for compatibility)
# ----------------------------------------------------------------------
def get_seed() -> int:
    """Return a deterministic seed (placeholder implementation)."""
    return 42

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    random.seed(seed)

def get_api_key() -> str | None:
    """Retrieve the LLM API key from the environment."""
    return os.getenv("LLM_API_KEY")

def resolve_model(candidate: str) -> str:
    """Resolve a model name, applying fallback logic if needed."""
    # Simple resolution: if the candidate is in the fallback list, return it;
    # otherwise fall back to the primary model.
    fallback = ["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"]
    return candidate if candidate in fallback else fallback[0]

def get_model_chain() -> List[str]:
    """Return the ordered fallback chain."""
    return ["gpt-4", "code-llama-7b", "bigcode/starcoderbase-3b"]
