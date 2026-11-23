"""
DEPRECATED MODULE

The original functionality has been merged into ``analysis.visualization``.
This file remains for backward compatibility; importing from it will
raise a deprecation warning.
"""
import warnings

warnings.warn(
    "code.analysis.complexity_visualization is deprecated. "
    "Please import from code.analysis.visualization instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re‑export key symbols for any legacy imports.
from analysis.visualization import KnotRecord, generate_complexity_visualization_examples, main  # noqa: F401