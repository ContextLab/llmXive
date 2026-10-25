"""Top-level package for quantifying initial conditions."""

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

# Minimal public API – heavy imports are deferred to avoid import‑time side effects.
# Sub‑packages expose their own symbols; we only provide a convenient accessor for
# configuration utilities.

try:
    from .config import get_full_config, set_simulation_seed  # type: ignore
except Exception:  # pragma: no cover
    # Stubs that raise informative errors if the config module cannot be imported.
    def get_full_config(*args, **kwargs):
        raise ImportError("Configuration module not available.")

    def set_simulation_seed(*args, **kwargs):
        raise ImportError("Configuration module not available.")

__all__ = [
    "get_full_config",
    "set_simulation_seed",
]
