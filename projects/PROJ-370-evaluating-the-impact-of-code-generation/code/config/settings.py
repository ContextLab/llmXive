"""
Backwards-compatible configuration shim.

All configuration now lives in ``code/src/config/settings.py`` (Task
T002).  This module re-exports the full API so that existing imports of
``code.config.settings`` keep working unchanged.
"""

from code.src.config.settings import (  # noqa: F401
    DEFAULT_CONFIG_PATH,
    HYPERPARAMS,
    NUMPY_SEED,
    PATHS,
    PROJECT_ROOT,
    PYTHON_SEED,
    RANDOM_SEED,
    TARGET_REPOS,
    ensure_directories,
    get_config,
    get_hyperparams,
    get_paths,
    get_seed,
    get_target_repos,
    load_config,
    save_config,
)

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "HYPERPARAMS",
    "NUMPY_SEED",
    "PATHS",
    "PROJECT_ROOT",
    "PYTHON_SEED",
    "RANDOM_SEED",
    "TARGET_REPOS",
    "ensure_directories",
    "get_config",
    "get_hyperparams",
    "get_paths",
    "get_seed",
    "get_target_repos",
    "load_config",
    "save_config",
]
