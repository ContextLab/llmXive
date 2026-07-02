"""
Configuration module for the plant disease resistance prediction pipeline.

Loads environment variables and defines default paths for project artifacts.
"""
import os
from pathlib import Path

# Project root is assumed to be two levels up from this file (code/config.py)
# Structure: <root>/code/config.py -> <root>
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default directory paths
DEFAULT_DATA_DIR = _PROJECT_ROOT / "data"
DEFAULT_PROCESSED_DATA_DIR = DEFAULT_DATA_DIR / "processed"
DEFAULT_RAW_DATA_DIR = DEFAULT_DATA_DIR / "raw"
DEFAULT_ARTIFACTS_DIR = _PROJECT_ROOT / "artifacts"
DEFAULT_MODELS_DIR = DEFAULT_ARTIFACTS_DIR / "models"
DEFAULT_REPORTS_DIR = DEFAULT_ARTIFACTS_DIR / "reports"
DEFAULT_FIGURES_DIR = DEFAULT_ARTIFACTS_DIR / "figures"
DEFAULT_LOGS_DIR = _PROJECT_ROOT / "logs"

# Default file paths
DEFAULT_MANIFEST_PATH = DEFAULT_DATA_DIR / "data_manifest.yaml"
DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"

# Environment variable names
ENV_DATA_DIR = "PLANT_DISEASE_DATA_DIR"
ENV_MODELS_DIR = "PLANT_DISEASE_MODELS_DIR"
ENV_REPORTS_DIR = "PLANT_DISEASE_REPORTS_DIR"
ENV_LOG_LEVEL = "PLANT_DISEASE_LOG_LEVEL"
ENV_SIMULATION_MODE = "PLANT_DISEASE_SIMULATION_MODE"
ENV_N_JOBS = "PLANT_DISEASE_N_JOBS"


def get_path(env_var: str, default: Path) -> Path:
    """
    Retrieve a path from an environment variable or fall back to the default.

    Args:
        env_var: The name of the environment variable.
        default: The default Path to use if the env var is not set.

    Returns:
        A resolved Path object.
    """
    val = os.getenv(env_var)
    if val:
        return Path(val).resolve()
    return default.resolve()


def get_int(env_var: str, default: int) -> int:
    """
    Retrieve an integer from an environment variable or fall back to the default.

    Args:
        env_var: The name of the environment variable.
        default: The default integer to use if the env var is not set.

    Returns:
        The integer value.
    """
    val = os.getenv(env_var)
    if val is not None:
        try:
            return int(val)
        except ValueError:
            return default
    return default


def get_bool(env_var: str, default: bool) -> bool:
    """
    Retrieve a boolean from an environment variable or fall back to the default.

    Args:
        env_var: The name of the environment variable.
        default: The default boolean to use if the env var is not set.

    Returns:
        The boolean value (True for '1', 'true', 'yes', 'on'; False otherwise).
    """
    val = os.getenv(env_var)
    if val is not None:
        return val.lower() in ("1", "true", "yes", "on")
    return default


# Configuration Object
class Config:
    """
    Central configuration object holding all paths and runtime settings.
    """

    # Directories
    DATA_DIR: Path = None
    PROCESSED_DATA_DIR: Path = None
    RAW_DATA_DIR: Path = None
    ARTIFACTS_DIR: Path = None
    MODELS_DIR: Path = None
    REPORTS_DIR: Path = None
    FIGURES_DIR: Path = None
    LOGS_DIR: Path = None

    # Files
    MANIFEST_PATH: Path = None
    CONFIG_PATH: Path = None

    # Runtime Settings
    LOG_LEVEL: str = None
    SIMULATION_MODE: bool = None
    N_JOBS: int = None

    def __init__(self):
        """Initialize configuration from environment variables and defaults."""
        self.DATA_DIR = get_path(ENV_DATA_DIR, DEFAULT_DATA_DIR)
        self.RAW_DATA_DIR = get_path(ENV_DATA_DIR, DEFAULT_RAW_DATA_DIR)
        self.PROCESSED_DATA_DIR = get_path(ENV_DATA_DIR, DEFAULT_PROCESSED_DATA_DIR)
        
        # Ensure processed/raw are subdirs of data if data is customized, 
        # otherwise use defaults relative to project root
        if os.getenv(ENV_DATA_DIR):
            self.RAW_DATA_DIR = self.DATA_DIR / "raw"
            self.PROCESSED_DATA_DIR = self.DATA_DIR / "processed"

        self.ARTIFACTS_DIR = get_path(ENV_DATA_DIR, DEFAULT_ARTIFACTS_DIR)
        self.MODELS_DIR = get_path(ENV_MODELS_DIR, DEFAULT_MODELS_DIR)
        self.REPORTS_DIR = get_path(ENV_REPORTS_DIR, DEFAULT_REPORTS_DIR)
        self.FIGURES_DIR = self.ARTIFACTS_DIR / "figures"
        self.LOGS_DIR = get_path(ENV_DATA_DIR, DEFAULT_LOGS_DIR)

        self.MANIFEST_PATH = get_path(ENV_DATA_DIR, DEFAULT_MANIFEST_PATH)
        self.CONFIG_PATH = DEFAULT_CONFIG_PATH

        self.LOG_LEVEL = os.getenv(ENV_LOG_LEVEL, "INFO")
        self.SIMULATION_MODE = get_bool(ENV_SIMULATION_MODE, False)
        self.N_JOBS = get_int(ENV_N_JOBS, -1)  # -1 usually means use all cores

    def ensure_dirs(self):
        """Create all configured directories if they do not exist."""
        dirs = [
            self.DATA_DIR,
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.ARTIFACTS_DIR,
            self.MODELS_DIR,
            self.REPORTS_DIR,
            self.FIGURES_DIR,
            self.LOGS_DIR,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def __repr__(self):
        return (
            f"Config(DATA_DIR={self.DATA_DIR}, "
            f"MODELS_DIR={self.MODELS_DIR}, "
            f"REPORTS_DIR={self.REPORTS_DIR}, "
            f"SIMULATION_MODE={self.SIMULATION_MODE})"
        )


# Global instance for convenience
config = Config()