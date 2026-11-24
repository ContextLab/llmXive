"""
Utility functions for computing semantic density metrics.

This module provides:
  - calculate_technical_token_ratio: proportion of tokens that are technical terms.
  - calculate_composite_density: weighted combination of entropy per token and technical token ratio.

The composite density follows the formula defined in FR‑008:
    density = 0.6 * entropy_per_token + 0.4 * technical_token_ratio
The result is clamped to the interval [0.0, 1.0] to keep downstream values bounded.
"""

import re
from typing import List, Set

from .entropy import entropy_per_token


def calculate_technical_token_ratio(text: str, terms: Set[str] = None) -> float:
    """
    Calculate the proportion of tokens in *text* that appear in the supplied
    technical term set.

    Tokens are obtained by a simple whitespace split; punctuation is retained
    as part of the token. Matching is case‑insensitive.

    Parameters
    ----------
    text: str
        The input text to analyse.
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
    # Normalise both token and term to lower case for case‑insensitive matching
    tokens = re.findall(r"\S+", text)
    if not tokens:
        return 0.0
    tech_tokens = sum(1 for tok in tokens if tok.lower() in {t.lower() for t in terms})
    return tech_tokens / len(tokens)


def _clamp_density(value: float) -> float:
    """
    Clamp a density value to the closed interval [0.0, 1.0].
    """
    return max(0.0, min(1.0, value))


def calculate_composite_density(text: str, terms: List[str]) -> float:
    """
    Compute the composite semantic density for *text*.

    Formula (FR‑008):
        density = 0.6 * entropy_per_token + 0.4 * technical_token_ratio

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
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    term_set = set(terms or [])
    ent = entropy_per_token(text)
    tech_ratio = calculate_technical_token_ratio(text, term_set)
    density = 0.6 * ent + 0.4 * tech_ratio
    return _clamp_density(density)
