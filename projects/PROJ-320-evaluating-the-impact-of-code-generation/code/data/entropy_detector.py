"""Secondary entropy detector (T005).

Computes a normalised Shannon entropy score over the whitespace-split
token distribution of a plain-text PR diff. The score (`entropy_score`)
is normalised to the 0-1 range by dividing by the maximum possible
entropy log2(K), where K is the number of distinct tokens observed.
"""
from __future__ import annotations

import math
from typing import Dict, List


def tokenize_diff(diff_text: str) -> List[str]:
    """Tokenise a diff by whitespace splitting (per T005 spec)."""
    if not diff_text:
        return []
    return diff_text.split()


def token_frequencies(tokens: List[str]) -> Dict[str, int]:
    """Count occurrences of each token."""
    freq: Dict[str, int] = {}
    for tok in tokens:
        freq[tok] = freq.get(tok, 0) + 1
    return freq


def shannon_entropy(tokens: List[str]) -> float:
    """Shannon entropy (in bits) of the token distribution."""
    if not tokens:
        return 0.0
    freq = token_frequencies(tokens)
    total = len(tokens)
    entropy = 0.0
    for count in freq.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def compute_entropy(diff_text: str) -> float:
    """Compute the normalised 0-1 entropy score of a PR diff.

    Args:
        diff_text: plain-text diff of a pull request.

    Returns:
        float in [0.0, 1.0]: Shannon entropy of the whitespace-token
        distribution, normalised by log2(K) where K is the number of
        distinct tokens (the maximum attainable entropy for K symbols).
        Empty or single-token diffs return 0.0.
    """
    if not isinstance(diff_text, str):
        raise TypeError(f"diff_text must be a string, got {type(diff_text).__name__}")

    tokens = tokenize_diff(diff_text)
    if not tokens:
        return 0.0

    freq = token_frequencies(tokens)
    distinct = len(freq)
    if distinct <= 1:
        return 0.0

    entropy = shannon_entropy(tokens)
    max_entropy = math.log2(distinct)
    normalized = entropy / max_entropy if max_entropy > 0 else 0.0
    # Guard against tiny floating point excursions outside [0, 1].
    return max(0.0, min(1.0, normalized))
