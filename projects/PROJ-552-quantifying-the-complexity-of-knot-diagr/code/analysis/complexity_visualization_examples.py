"""
DEPRECATED MODULE

The original example‑generation script has been merged into
``analysis.visualization``.  Importing this module will emit a
deprecation warning but continue to provide the previous ``main`` entry‑point.
"""
import warnings

warnings.warn(
    "code.analysis.complexity_visualization_examples is deprecated. "
    "Use analysis.visualization.run_examples() instead.",
    DeprecationWarning,
    stacklevel=2,
)

from analysis.visualization import run_examples as main  # noqa: F401