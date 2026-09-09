"""
Configuration loader for the llmXive research pipeline.

Manages environment variables and file paths for the project.
Provides a centralized way to access configuration settings.
"""
import os
from typing import Any, Dict, Optional
from pathlib import Path

# Project root path (assumed to be the directory containing 'code/')
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default paths relative to project root
DEFAULT_DATA_DIR = "data"
DEFAULT_CODE_DIR = "code"
DEFAULT_TESTS_DIR = "tests"
DEFAULT_FIGURES_DIR = "figures"

# Subdirectories for processed data and outputs
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
DATA_CLEANED_DIR = "data/cleaned"

# Output filenames
MODEL_RESULTS_FILE = "model_results.json"
PIPELINE_LOG_FILE = "pipeline_run_log.json"
SCATTER_PLOT_FILE = "scatter_plot.png"
RESIDUALS_PLOT_FILE = "residuals.png"

# Environment variable keys
ENV_DATA_DIR = "LLMXIVE_DATA_DIR"
ENV_CODE_DIR = "LLMXIVE_CODE_DIR"
ENV_DEBUG_MODE = "LLMXIVE_DEBUG_MODE"
ENV_LOG_LEVEL = "LLMXIVE_LOG_LEVEL"


class Config:
    """
    Central configuration class for the project.

    Loads settings from environment variables with sensible defaults.
    """

    def __init__(self):
        self._data_dir: Path = self._load_data_dir()
        self._code_dir: Path = self._load_code_dir()
        self._debug: bool = self._load_debug_mode()
        self._log_level: str = self._load_log_level()
        self._figures_dir: Path = self._load_figures_dir()

    def _load_data_dir(self) -> Path:
        """Load data directory path from environment or default."""
        env_path = os.getenv(ENV_DATA_DIR)
        if env_path:
            return Path(env_path)
        return PROJECT_ROOT / DEFAULT_DATA_DIR

    def _load_code_dir(self) -> Path:
        """Load code directory path from environment or default."""
        env_path = os.getenv(ENV_CODE_DIR)
        if env_path:
            return Path(env_path)
        return PROJECT_ROOT / DEFAULT_CODE_DIR

    def _load_debug_mode(self) -> bool:
        """Load debug mode flag from environment."""
        debug_val = os.getenv(ENV_DEBUG_MODE, "false").lower()
        return debug_val in ("true", "1", "yes")

    def _load_log_level(self) -> str:
        """Load log level from environment."""
        return os.getenv(ENV_LOG_LEVEL, "INFO")

    def _load_figures_dir(self) -> Path:
        """Load figures directory path."""
        # Figures are typically stored in data/processed or a dedicated figures dir
        return self._data_dir / DEFAULT_FIGURES_DIR

    @property
    def data_dir(self) -> Path:
        """Return the data directory path."""
        return self._data_dir

    @property
    def code_dir(self) -> Path:
        """Return the code directory path."""
        return self._code_dir

    @property
    def figures_dir(self) -> Path:
        """Return the figures directory path."""
        return self._figures_dir

    @property
    def debug(self) -> bool:
        """Return whether debug mode is enabled."""
        return self._debug

    @property
    def log_level(self) -> str:
        """Return the configured log level."""
        return self._log_level

    @property
    def raw_data_dir(self) -> Path:
        """Return the raw data subdirectory."""
        return self._data_dir / DATA_RAW_DIR

    @property
    def processed_data_dir(self) -> Path:
        """Return the processed data subdirectory."""
        return self._data_dir / DATA_PROCESSED_DIR

    @property
    def cleaned_data_dir(self) -> Path:
        """Return the cleaned data subdirectory."""
        return self._data_dir / DATA_CLEANED_DIR

    @property
    def model_results_path(self) -> Path:
        """Return the full path to the model results file."""
        return self.processed_data_dir / MODEL_RESULTS_FILE

    @property
    def pipeline_log_path(self) -> Path:
        """Return the full path to the pipeline run log file."""
        return self.processed_data_dir / PIPELINE_LOG_FILE

    @property
    def scatter_plot_path(self) -> Path:
        """Return the full path to the scatter plot file."""
        return self.processed_data_dir / SCATTER_PLOT_FILE

    @property
    def residuals_plot_path(self) -> Path:
        """Return the full path to the residuals plot file."""
        return self.processed_data_dir / RESIDUALS_PLOT_FILE

    def ensure_directories_exist(self) -> None:
        """Create all necessary directories if they don't exist."""
        dirs = [
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.cleaned_data_dir,
            self.figures_dir,
            self.code_dir,
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: The configuration key.
            default: Default value if key is not found.

        Returns:
            The configuration value or default.
        """
        mapping = {
            "data_dir": self.data_dir,
            "code_dir": self.code_dir,
            "figures_dir": self.figures_dir,
            "debug": self.debug,
            "log_level": self.log_level,
            "raw_data_dir": self.raw_data_dir,
            "processed_data_dir": self.processed_data_dir,
            "cleaned_data_dir": self.cleaned_data_dir,
            "model_results_path": self.model_results_path,
            "pipeline_log_path": self.pipeline_log_path,
            "scatter_plot_path": self.scatter_plot_path,
            "residuals_plot_path": self.residuals_plot_path,
        }
        return mapping.get(key, default)


# Global config instance
config = Config()


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        The global Config instance.
    """
    return config
