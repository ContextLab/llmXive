"""
DEPRECATED MODULE

The runner now simply forwards to ``analysis.visualization.main``.
"""
import warnings

warnings.warn(
    "code.analysis.complexity_visualization_runner is deprecated. "
    "Use analysis.visualization.main() directly.",
    DeprecationWarning,
    stacklevel=2,
)

from analysis.visualization import main  # noqa: F401