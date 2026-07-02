"""
Configuration management for the llmXive plant disease resistance pipeline.

Loads environment variables and defines default paths for project directories.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project root is the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default directory structure as defined in T001
DEFAULT_PATHS: Dict[str, Path] = {
    "code": _PROJECT_ROOT / "code",
    "data": _PROJECT_ROOT / "data",
    "data_raw": _PROJECT_ROOT / "data" / "raw",
    "data_processed": _PROJECT_ROOT / "data" / "processed",
    "artifacts": _PROJECT_ROOT / "artifacts",
    "artifacts_models": _PROJECT_ROOT / "artifacts" / "models",
    "artifacts_reports": _PROJECT_ROOT / "artifacts" / "reports",
    "artifacts_figures": _PROJECT_ROOT / "artifacts" / "figures",
    "tests": _PROJECT_ROOT / "tests",
    "specs": _PROJECT_ROOT / "specs",
}

# Environment variable keys
ENV_PREFIX = "LLMXIVE_"
ENV_DATA_ROOT = f"{ENV_PREFIX}DATA_ROOT"
ENV_LOG_LEVEL = f"{ENV_PREFIX}LOG_LEVEL"
ENV_SEED = f"{ENV_PREFIX}SEED"
ENV_SIMULATION_MODE = f"{ENV_PREFIX}SIMULATION_MODE"

def get_env_var(key: str, default: str = "") -> str:
    """Retrieve an environment variable, falling back to the provided default."""
    return os.environ.get(key, default)

def get_int_env_var(key: str, default: int = 0) -> int:
    """Retrieve an integer environment variable."""
    try:
        return int(get_env_var(key, str(default)))
    except ValueError:
        return default

def get_bool_env_var(key: str, default: bool = False) -> bool:
    """Retrieve a boolean environment variable (checks for '1', 'true', 'yes')."""
    val = get_env_var(key, "").lower()
    return val in ("1", "true", "yes", "on")

class Config:
    """
    Central configuration object holding paths and runtime settings.
    """

    def __init__(self):
        # Determine root paths
        data_root_override = get_env_var(ENV_DATA_ROOT)
        if data_root_override:
            base_path = Path(data_root_override)
            self._paths = {
                "code": base_path / "code",
                "data": base_path / "data",
                "data_raw": base_path / "data" / "raw",
                "data_processed": base_path / "data" / "processed",
                "artifacts": base_path / "artifacts",
                "artifacts_models": base_path / "artifacts" / "models",
                "artifacts_reports": base_path / "artifacts" / "reports",
                "artifacts_figures": base_path / "artifacts" / "figures",
                "tests": base_path / "tests",
                "specs": base_path / "specs",
            }
        else:
            self._paths = DEFAULT_PATHS

        # Runtime settings
        self.log_level = get_env_var(ENV_LOG_LEVEL, "INFO").upper()
        self.seed = get_int_env_var(ENV_SEED, 42)
        self.simulation_mode = get_bool_env_var(ENV_SIMULATION_MODE, False)

        # Ensure directories exist (optional, can be done in setup T001)
        # self._ensure_dirs()

    @property
    def paths(self) -> Dict[str, Path]:
        """Return the dictionary of configured paths."""
        return self._paths

    def get_path(self, name: str) -> Path:
        """Get a specific path by name, raising KeyError if not found."""
        if name not in self._paths:
            raise KeyError(f"Path name '{name}' not found in config.")
        return self._paths[name]

    def __repr__(self) -> str:
        return (
            f"Config(log_level={self.log_level}, seed={self.seed}, "
            f"simulation_mode={self.simulation_mode})"
        )

# Singleton instance for easy import
config = Config()

# Convenience accessors
def get_data_path() -> Path:
    return config.get_path("data")

def get_processed_data_path() -> Path:
    return config.get_path("data_processed")

def get_artifacts_path() -> Path:
    return config.get_path("artifacts")

def get_reports_path() -> Path:
    return config.get_path("artifacts_reports")