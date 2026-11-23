"""
Environment configuration management.
Handles seeds, paths, timeouts, API keys, and pinned reference set SHA.
"""

import os
from pathlib import Path
from typing import Any, Optional, Dict

# ----------------------------------------------------------------------
# Project root resolution
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ----------------------------------------------------------------------
# Default configuration dictionary
# ----------------------------------------------------------------------
DEFAULT_CONFIG: Dict[str, Any] = {
    # Randomness
    "random_seed": 42,
    # API timeouts
    "github_api_timeout": 30,          # seconds
    "git_clone_timeout": 300,          # seconds
    "pmd_timeout_seconds": 120,       # seconds
    # Resource limits
    "pmd_memory_limit_gb": 2,
    "max_retries": 3,
    "retry_delay_seconds": 5,
    # Output locations
    "output_dir": PROJECT_ROOT / "data",
    "reports_dir": PROJECT_ROOT / "reports",
    "logs_dir": PROJECT_ROOT / "logs",
    "temp_dir": PROJECT_ROOT / "temp_clones",
    # API keys (populated from environment at runtime)
    "github_token": None,
    "huggingface_token": None,
    # External tool locations
    "pmd_home": None,
    "java_home": None,
    # Pinned reference set SHA (Python 3.12.0 source tarball)
    "reference_set_sha": "v3.12.0",
}

# ----------------------------------------------------------------------
# Exported constants required by the test suite and other modules
# ----------------------------------------------------------------------
FALSE_POSITIVE_THRESHOLD: float = 0.05  # (2203.15897, https://arxiv.org/abs/2203.15897)

# Random seed constants – both a variable and a getter are provided for
# compatibility with existing code that expects either.
RANDOM_SEED: int = DEFAULT_CONFIG["random_seed"]
DEFAULT_RANDOM_SEED: int = RANDOM_SEED

# API timeout constants
DEFAULT_API_TIMEOUT_SECONDS: int = DEFAULT_CONFIG["github_api_timeout"]
DEFAULT_PROCESS_TIMEOUT_SECONDS: int = DEFAULT_CONFIG["git_clone_timeout"]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_env_overrides() -> None:
    """
    Populate DEFAULT_CONFIG with values from the environment, if present.
    Environment variable names are expected to be upper‑cased versions of
    the configuration keys.
    """
    for key in list(DEFAULT_CONFIG.keys()):
        env_key = key.upper()
        if env_key in os.environ:
            # Attempt to preserve type where possible
            current = DEFAULT_CONFIG[key]
            env_val = os.environ[env_key]
            if isinstance(current, bool):
                DEFAULT_CONFIG[key] = env_val.lower() in ("1", "true", "yes")
            elif isinstance(current, int):
                try:
                    DEFAULT_CONFIG[key] = int(env_val)
                except ValueError:
                    DEFAULT_CONFIG[key] = env_val
            else:
                DEFAULT_CONFIG[key] = env_val

# Apply overrides at import time so the config reflects the running env.
_load_env_overrides()

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return PROJECT_ROOT

def get_config(key: Optional[str] = None) -> Any:
    """
    Retrieve a configuration value.

    Args:
        key: Specific configuration key to retrieve, or ``None`` to obtain a copy
             of the entire configuration dictionary.

    Returns:
        The requested configuration value, or a shallow copy of the full config.
    """
    if key is None:
        return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.get(key)

def validate_config() -> Dict[str, Any]:
    """
    Validate that critical configuration entries are present.

    Returns:
        A dictionary containing a boolean ``valid`` flag, a list of any missing
        keys, and the full configuration for debugging purposes.
    """
    missing_keys = []

    if get_config("github_token") is None:
        missing_keys.append("GITHUB_TOKEN")
    if get_config("pmd_home") is None:
        missing_keys.append("PMD_HOME")
    if get_config("java_home") is None:
        missing_keys.append("JAVA_HOME")

    return {
        "valid": len(missing_keys) == 0,
        "missing_keys": missing_keys,
        "config": get_config(),
    }

def get_output_paths() -> Dict[str, Path]:
    """
    Assemble the primary output directories used throughout the pipeline.

    Returns:
        Mapping of logical names (``raw``, ``intermediate``, ``processed``,
        ``reports``, ``logs``) to absolute ``Path`` objects.
    """
    base = get_config("output_dir")
    return {
        "raw": base / "raw",
        "intermediate": base / "intermediate",
        "processed": base / "processed",
        "reports": get_config("reports_dir"),
        "logs": get_config("logs_dir"),
    }

def get_timeouts() -> Dict[str, int]:
    """
    Gather timeout settings for external services.

    Returns:
        Mapping with keys ``github_api``, ``git_clone`` and ``pmd``.
    """
    return {
        "github_api": get_config("github_api_timeout"),
        "git_clone": get_config("git_clone_timeout"),
        "pmd": get_config("pmd_timeout_seconds"),
    }

def get_limits() -> Dict[str, Any]:
    """
    Retrieve resource‑limit configuration values.

    Returns:
        Mapping with keys ``pmd_memory_gb``, ``max_retries`` and
        ``retry_delay_seconds``.
    """
    return {
        "pmd_memory_gb": get_config("pmd_memory_limit_gb"),
        "max_retries": get_config("max_retries"),
        "retry_delay_seconds": get_config("retry_delay_seconds"),
    }

def get_random_seed() -> int:
    """Convenient accessor for the configured random seed."""
    return get_config("random_seed")

def ensure_directories_exist() -> bool:
    """
    Ensure that all standard output directories exist, creating them if
    necessary.

    Returns:
        ``True`` if all directories are present after the call.
    """
    paths = get_output_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return True

# ----------------------------------------------------------------------
# Additional convenience utilities required by ``utils.__init__``
# ----------------------------------------------------------------------
class Config(dict):
    """
    Lightweight configuration wrapper used throughout the code base.

    It behaves like a dictionary but provides attribute access for
    convenience (e.g. ``cfg.random_seed``).  The class is instantiated
    via :meth:`load`.
    """

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from the default source."""
        return cls(get_config())

def get_path(key: str) -> Optional[Path]:
    """
    Resolve a configuration entry that represents a filesystem path.

    Args:
        key: The configuration key (e.g. ``'output_dir'``).

    Returns:
        A ``Path`` object if the key exists and is not ``None``,
        otherwise ``None``.
    """
    val = get_config(key)
    if val is None:
        return None
    return Path(val) if not isinstance(val, Path) else val

def get_data_path() -> Path:
    """
    Shortcut to obtain the root data directory (``output_dir``/``raw``).
    """
    return get_path("output_dir") / "raw"

def require_env_var(var_name: str) -> str:
    """
    Ensure that a required environment variable is set.

    Raises:
        EnvironmentError: If the variable is missing.
    """
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f"Required environment variable '{var_name}' is not set.")
    return value

def get_llm_api_key() -> str:
    """Retrieve the HuggingFace API key from configuration or the environment."""
    token = get_config("huggingface_token")
    if token:
        return token
    return require_env_var("HF_API_KEY")

def get_github_token() -> str:
    """Retrieve the GitHub token from configuration or the environment."""
    token = get_config("github_token")
    if token:
        return token
    return require_env_var("GITHUB_TOKEN")

# Export symbols for ``from utils import *`` and for the explicit imports
# performed in ``utils.__init__``.
__all__ = [
    "Config",
    "get_config",
    "get_path",
    "get_data_path",
    "require_env_var",
    "get_llm_api_key",
    "get_github_token",
    "PROJECT_ROOT",
    "DEFAULT_RANDOM_SEED",
    "DEFAULT_API_TIMEOUT_SECONDS",
    "DEFAULT_PROCESS_TIMEOUT_SECONDS",
    "FALSE_POSITIVE_THRESHOLD",
    "RANDOM_SEED",
    "REFERENCE_SET_SHA",
]

# Alias for backward compatibility with code that expects the constant name.
REFERENCE_SET_SHA: str = DEFAULT_CONFIG["reference_set_sha"]