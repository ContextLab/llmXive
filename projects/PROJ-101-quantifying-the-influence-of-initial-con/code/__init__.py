"""Top-level package for quantifying initial conditions."""

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

# Import core public APIs that are guaranteed to exist.
# Use lazy imports where optional sub-modules may be missing.
try:
    from .config import get_full_config, set_simulation_seed  # type: ignore
except Exception:  # pragma: no cover
    # Provide fallback stubs if config module is unavailable.
    def get_full_config(*args, **kwargs):
        raise ImportError("config module not available")

    def set_simulation_seed(*args, **kwargs):
        raise ImportError("config module not available")

# Core stability utilities are always present.
from .utils.stability import check_boundedness, check_convergence  # noqa: F401

# The data generator and FTLE computation are optional; they may be added later.
try:
    from .data.generator import generate_coupled_lorenz_trajectory  # type: ignore
except Exception:  # pragma: no cover
    def generate_coupled_lorenz_trajectory(*args, **kwargs):
        raise ImportError("data.generator module not available")

try:
    from .analysis.ftle import compute_ftle_single_trajectory  # type: ignore
except Exception:  # pragma: no cover
    def compute_ftle_single_trajectory(*args, **kwargs):
        raise ImportError("analysis.ftle module not available")

try:
    from .analysis.baseline import compute_asymptotic_baseline  # type: ignore
except Exception:  # pragma: no cover
    def compute_asymptotic_baseline(*args, **kwargs):
        raise ImportError("analysis.baseline module not available")

__all__ = [
    "get_full_config",
    "set_simulation_seed",
    "check_boundedness",
    "check_convergence",
    "generate_coupled_lorenz_trajectory",
    "compute_ftle_single_trajectory",
    "compute_asymptotic_baseline",
]
