"""
Package marker for evaluation utilities.
Exposes the primary evaluation entry point so that ``from eval import
evaluate_checkpoint`` works even though a sibling module ``eval.py`` also
exists. This resolves the name‑collision between the ``eval`` package and
the ``eval.py`` script.
"""

# Re‑export the public API from the module implementation.
from .eval import evaluate_checkpoint  # noqa: F401
