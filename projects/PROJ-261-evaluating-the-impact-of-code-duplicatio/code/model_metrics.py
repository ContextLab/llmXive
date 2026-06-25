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

import logging
import math
from typing import Any, Optional

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


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


def validate_perplexity(value: float) -> bool:
    """
    Validate that a perplexity value is finite and not NaN.

    This function implements the NaN/infinite value detection required by
    test task T013. Any NaN or infinite perplexity values should be
    rejected and logged as errors.

    Parameters
    ----------
    value: float
        The perplexity value to validate.

    Returns
    -------
    bool
        True if the value is valid (finite and not NaN), False otherwise.
    """
    if math.isnan(value) or math.isinf(value):
        return False
    return True


def compute_perplexity(
    text: str,
    model: Any,
    tokenizer: Any,
    max_length: int = 512,
) -> float:
    """
    Compute token-level perplexity for a given text using the loaded model.

    Parameters
    ----------
    text: str
        The input text to compute perplexity for.
    model: Any
        The loaded language model (from ``load_model_8bit``).
    tokenizer: Any
        The tokenizer corresponding to the model.
    max_length: int
        Maximum sequence length to process. Longer texts will be truncated.

    Returns
    -------
    float
        The perplexity value (exp of average cross-entropy loss).

    Raises
    ------
    ValueError
        If the computed perplexity is NaN or infinite.
    """
    # Tokenize the input text
    inputs = tokenizer(
        text,
        return_tensors="pt",
        max_length=max_length,
        truncation=True,
    )

    # Move inputs to the same device as the model
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Compute loss (model returns logits, we compute cross-entropy)
    with torch.no_grad():
        outputs = model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss

    # Perplexity is exp(loss)
    perplexity = torch.exp(loss).item()

    # Validate the result (T013 requirement)
    if not validate_perplexity(perplexity):
        raise ValueError(
            f"Invalid perplexity value: {perplexity}. "
            "Perplexity must be finite and not NaN."
        )

    return perplexity


def compute_perplexity_batch(
    texts: list[str],
    model: Any,
    tokenizer: Any,
    max_length: int = 512,
) -> list[dict[str, Any]]:
    """
    Compute perplexity for a batch of texts.

    Parameters
    ----------
    texts: list[str]
        List of input texts to compute perplexity for.
    model: Any
        The loaded language model.
    tokenizer: Any
        The tokenizer corresponding to the model.
    max_length: int
        Maximum sequence length per text.

    Returns
    -------
    list[dict[str, Any]]
        List of results, each containing:
        - "text_index": index of the text in the input list
        - "text_length": length of the text (in characters)
        - "perplexity": computed perplexity value
        - "valid": whether the perplexity value passed validation
    """
    results = []

    for idx, text in enumerate(texts):
        try:
            perplexity = compute_perplexity(
                text, model, tokenizer, max_length=max_length
            )
            results.append({
                "text_index": idx,
                "text_length": len(text),
                "perplexity": perplexity,
                "valid": True,
            })
        except ValueError as e:
            # Log the error but continue processing other texts
            logging.warning(
                f"Perplexity computation failed for text {idx}: {e}"
            )
            results.append({
                "text_index": idx,
                "text_length": len(text),
                "perplexity": float("nan"),
                "valid": False,
            })
        except Exception as e:
            # Catch-all for unexpected errors
            logging.error(
                f"Unexpected error computing perplexity for text {idx}: {e}"
            )
            results.append({
                "text_index": idx,
                "text_length": len(text),
                "perplexity": float("nan"),
                "valid": False,
            })

    return results


def load_model_and_tokenizer(
    model_name: str = "Salesforce/codegen-350M-mono",
) -> tuple[Any, Any]:
    """
    Load both the model and its corresponding tokenizer.

    Parameters
    ----------
    model_name: str
        The HuggingFace model identifier.

    Returns
    -------
    tuple[Any, Any]
        A tuple of (model, tokenizer).
    """
    model = load_model_8bit(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, tokenizer