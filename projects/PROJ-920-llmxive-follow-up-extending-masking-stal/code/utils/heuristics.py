"""
Heuristics utilities for the llmXive follow‑up project.

This module provides functions to compute the technical token ratio and the
composite semantic density of a text block. The composite density follows
the specification FR‑008:

    density = 0.6 * entropy_per_token + 0.4 * technical_token_ratio

The implementation is deliberately pure: it depends only on the supplied
text and the list of technical terms. No external state (e.g. simulation
results, agent outputs) is consulted.
"""

import re
from typing import List, Set

# Local import to avoid circular dependencies
from .entropy import entropy_per_token


def calculate_technical_token_ratio(text: str, terms: Set[str] = None) -> float:
    """
    Calculate the ratio of technical tokens to total tokens in the text.

    Args:
        text: The input text to analyze.
        terms: An optional set of technical terms. If None, the built‑in
               term list is used (the function falls back to an empty set,
               yielding a ratio of 0.0).

    Returns:
        A float in the range [0.0, 1.0] representing the proportion of
        tokens that are technical.
    """
    if not text:
        return 0.0

    # Tokenise on whitespace; this is sufficient for the synthetic data.
    tokens = re.findall(r"\b\w+\b", text.lower())
    if not tokens:
        return 0.0

    if terms is None:
        terms = set()
    technical_count = sum(1 for token in tokens if token in terms)
    return technical_count / len(tokens)


def calculate_composite_density(text: str, terms: List[str]) -> float:
    """
    Compute the composite semantic density for a piece of text.

    The function is a **pure** computation: it only uses the supplied
    ``text`` and the list of ``terms``. No other arguments are accepted,
    satisfying the FR‑007 requirement that density calculation must be
    isolated from agent‑output or simulation state.

    The formula implements FR‑008 exactly:

        density = 0.6 * entropy_per_token + 0.4 * technical_token_ratio

    where ``entropy_per_token`` is measured in bits per token via the
    ``entropy_per_token`` helper (byte‑level Shannon entropy divided by the
    token length, default token length = 1).

    Args:
        text: The text block whose density is to be measured.
        terms: A list of technical terms (strings). The list is converted
               to a ``set`` for efficient membership testing.

    Returns:
        A float representing the composite density. For the synthetic
        trajectories used in this project the value typically lies in
        the interval [0, 1], but the function does not artificially clamp
        the result; callers may apply their own bounds if required.
    """
    # Compute entropy per token (bits/token). The helper already handles
    # empty strings and returns 0.0 in that case.
    entropy = entropy_per_token(text)

    # Compute technical token ratio using the helper above.
    tech_ratio = calculate_technical_token_ratio(text, set(terms))

    # Apply the weighted sum as defined by the specification.
    return 0.6 * entropy + 0.4 * tech_ratio
