"""
Utility package initializer.

We intentionally avoid importing submodules that themselves import
``code.utils`` to prevent circular import issues. Submodules should be
imported directly where needed, e.g.:

    from utils.logging_config import get_logger
    from code.utils.constants import SEED
"""
# Lazy attribute access to avoid eager imports that can cause circular
# dependencies. Only the requested attribute is imported on demand.

from importlib import import_module

def __getattr__(name):
    if name in {
        "PROJECT_ROOT",
        "DATA_RAW_PATH",
        "DATA_PROCESSED_PATH",
        "LOG_PATH",
        "RESULTS_PATH",
        "LOG_LEVEL",
        "RANDOM_SEED",
        "SPECIES_LIST",
        "STRESS_LIST",
        "REFERENCE_VALIDATOR_THRESHOLD",
    }:
        return getattr(import_module(".config", __package__), name)
    if name in {"setup_logging", "get_logger", "log_warning"}:
        return getattr(import_module(".logging_config", __package__), name)
    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = [
    "PROJECT_ROOT",
    "DATA_RAW_PATH",
    "DATA_PROCESSED_PATH",
    "LOG_PATH",
    "RESULTS_PATH",
    "LOG_LEVEL",
    "RANDOM_SEED",
    "SPECIES_LIST",
    "STRESS_LIST",
    "REFERENCE_VALIDATOR_THRESHOLD",
    "setup_logging",
    "get_logger",
    "log_warning",
]