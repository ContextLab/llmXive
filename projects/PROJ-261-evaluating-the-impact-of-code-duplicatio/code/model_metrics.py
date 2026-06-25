"""
Model metrics utilities.

This module provides functionality to load language models in 8‑bit quantized
mode using the `bitsandbytes` integration provided by the 🤗 Transformers
library. The primary purpose of this function in the current test suite is
to trigger an exception when model loading fails (e.g., due to missing
dependencies, network issues, or corrupted model files). The implementation
is intentionally minimal – it delegates all heavy lifting to
`transformers.AutoModelForCausalLM.from_pretrained` and propagates any
exception raised by that call.
"""

from typing import Any


def load_model_8bit(model_name: str) -> Any:
    """
    Load a causal language model in 8‑bit quantized mode.

    Parameters
    ----------
    model_name: str
        The identifier of the model to load (e.g., a HuggingFace repository
        name).

    Returns
    -------
    Any
        The loaded model object.

    Raises
    ------
    Exception
        Any exception raised by the underlying ``from_pretrained`` call is
        propagated to the caller. This includes ``ImportError`` when
        ``bitsandbytes`` is unavailable, ``RuntimeError`` for network
        failures, or any other loading‑related errors.
    """
    # Import inside the function to avoid import‑time side effects if the
    # optional dependencies are not installed in the execution environment.
    from transformers import AutoModelForCausalLM

    # The ``load_in_8bit`` flag triggers the bitsandbytes integration.
    # ``device_map="auto"`` lets Transformers decide the device placement.
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        load_in_8bit=True,
    )
    return model
