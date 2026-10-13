"""
Configuration module for the llmXive follow‑up pipeline.

This module reads required and optional environment variables at import time
and exposes them as module‑level constants:

- ``HF_TOKEN`` (required): HuggingFace authentication token.
- ``SAMPLE_SIZE`` (optional): Number of tasks to sample; defaults to 500.

Missing ``HF_TOKEN`` raises a ``RuntimeError`` with a clear message.
``SAMPLE_SIZE`` is coerced to ``int``; if the environment variable is set
but cannot be parsed as an integer, a ``ValueError`` is raised.
"""

import os

__all__ = ["HF_TOKEN", "SAMPLE_SIZE"]

def _get_env_int(name: str, default: int) -> int:
    """
    Helper to read an integer environment variable.

    Parameters
    ----------
    name: str
        Name of the environment variable.
    default: int
        Value to return if the variable is not set.

    Returns
    -------
    int
        The integer value of the environment variable or the default.

    Raises
    ------
    ValueError
        If the variable is set but cannot be converted to ``int``.
    """
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except Exception as exc:
        raise ValueError(
            f"Environment variable {name!r} must be an integer, got {value!r}"
        ) from exc

# Required token – raise immediately if missing
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise RuntimeError(
        "Missing required environment variable 'HF_TOKEN'. "
        "Set it to a valid HuggingFace access token before running the pipeline."
    )

# Optional sample size – default to 500 if not provided
SAMPLE_SIZE = _get_env_int("SAMPLE_SIZE", 500)