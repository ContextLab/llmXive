"""
Composite metric utilities for knot complexity analysis.

This module defines a new composite metric that combines existing
invariants (crossing number) with braid word length to provide an
additional quantitative descriptor of knot complexity.
"""

import math

def combined_complexity_score(crossing_number: int, braid_word: str) -> float:
    """
    Compute a composite complexity metric for a knot.

    The metric combines the minimal crossing number and the length of the
    braid word (as a proxy for braid complexity).  It is defined as:

        score = crossing_number * (1 + log10(len(braid_word) + 1))

    This provides a simple way to weight knots that have many crossings
    together with a long braid representation, offering a new invariant‑like
    quantity for downstream analyses.
    """
    braid_len = len(braid_word)
    return crossing_number * (1 + math.log10(braid_len + 1))
