"""
Utility functions for computing semantic density based on Shannon entropy
and technical token ratio.

The composite density follows FR‑008:
    density = 0.6 * entropy_per_token + 0.4 * technical_token_ratio

The final density is clamped to the interval [0.0, 1.0] to satisfy downstream
expectations and the unit tests that assert 0 ≤ density ≤ 1.
"""

import re
from typing import List, Set

from .entropy import entropy_per_token

__all__ = [
    "calculate_technical_token_ratio",
    "_clamp_density",
    "calculate_composite_density",
]


def calculate_technical_token_ratio(text: str, terms: Set[str] = None) -> float:
    """
    Calculate the proportion of tokens in *text* that appear in the supplied
    technical term set.

    Parameters
    ----------
    text: str
        The input text to analyze.
    terms: Set[str] | None
        A set of technical terms. If ``None`` an empty set is used,
        yielding a ratio of 0.0.

    Returns
    -------
    float
        Ratio in the range [0.0, 1.0].
    """
    if not text:
        return 0.0

    if terms is None:
        terms = set()

    # Simple whitespace tokenisation – sufficient for the synthetic data.
    tokens = re.findall(r"\b\w+\b", text.lower())
    if not tokens:
        return 0.0

    technical_hits = sum(1 for token in tokens if token in terms)
    return technical_hits / len(tokens)


def _clamp_density(value: float) -> float:
    """
    Clamp a density value to the closed interval [0.0, 1.0].

    This helper is deliberately private; the public API is
    :func:`calculate_composite_density`, which always applies the clamp
    before returning a result.

    Parameters
    ----------
    value: float
        The raw density value.

    Returns
    -------
    float
        ``value`` limited to the range [0.0, 1.0].
    """
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def calculate_composite_density(text: str, terms: List[str]) -> float:
    """
    Compute the composite semantic density for *text*.

    The function is a pure computation that depends **only** on the
    supplied text and the list of technical terms. No external state,
    simulation results, or agent outputs are consulted, satisfying FR‑007.

    Formula (FR‑008):
        density = 0.6 * entropy_per_token + 0.4 * technical_token_ratio

    The result is clamped to [0, 1] to keep downstream values bounded.

    Parameters
    ----------
    text: str
        The text block whose density is to be measured.
    terms: List[str]
        List of technical terms. Converted to a ``set`` for fast lookup.

    Returns
    -------
    float
        Composite density, guaranteed to lie in [0.0, 1.0].
    """
    # Defensive programming – ensure we work with the expected types.
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(terms, list):
        raise TypeError("terms must be a list of strings")

    # Compute the two components.
    entropy = entropy_per_token(text)  # bits per token, may be >1
    technical_ratio = calculate_technical_token_ratio(
        text, set(terms)
    )  # already in [0, 1]

    # Weighted combination per FR‑008.
    raw_density = 0.6 * entropy + 0.4 * technical_ratio

    # Clamp to the required interval.
    return _clamp_density(raw_density)