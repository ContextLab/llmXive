"""
Configuration loader for the llmXive project.

Loads environment variables from .env files (if available) and provides
validated access to project configuration paths and tokens.
"""
import os
from pathlib import Path
from typing import Optional


class ConfigError(Exception):
    """Raised when configuration loading fails."""
    pass


def load_env_file(env_path: Optional[Path] = None) -> None:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to the .env file. If None, looks for .env in the
                  project root or current working directory.
    """
    # Try to find .env in common locations if not explicitly provided
    if env_path is None:
        project_root = Path(__file__).resolve().parent.parent
        env_candidates = [
            project_root / '.env',
            Path.cwd() / '.env',
        ]
        # Look for .env file and load it manually if python-dotenv is missing
        for candidate in env_candidates:
            if candidate.exists():
                with open(candidate, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, _, value = line.partition('=')
                            os.environ[key.strip()] = value.strip('"').strip("'")
                return
    else:
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        os.environ[key.strip()] = value.strip('"').strip("'")


# Initialize configuration by loading .env if present
load_env_file()


class Config:
    """
    Centralized configuration management.

    Provides access to environment variables with defaults and validation.
    """

    # Environment variable names
    HF_TOKEN_KEY = "HF_TOKEN"
    DATA_PATH_KEY = "DATA_PATH"
    MODEL_PATH_KEY = "MODEL_PATH"

    # Default values
    DEFAULT_DATA_PATH = "./data"
    DEFAULT_MODEL_PATH = "./models"

    def __init__(self):
        """Load configuration from environment variables."""
        self._hf_token: Optional[str] = None
        self._data_path: Path = Path(self.DEFAULT_DATA_PATH)
        self._model_path: Path = Path(self.DEFAULT_MODEL_PATH)

        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load configuration values from environment variables."""
        # HuggingFace Token
        hf_token = os.getenv(self.HF_TOKEN_KEY)
        if hf_token:
            self._hf_token = hf_token.strip()

        # Data Path
        data_path_str = os.getenv(self.DATA_PATH_KEY)
        if data_path_str:
            self._data_path = Path(data_path_str)

        # Model Path
        model_path_str = os.getenv(self.MODEL_PATH_KEY)
        if model_path_str:
            self._model_path = Path(model_path_str)

    @property
    def hf_token(self) -> Optional[str]:
        """
        Get the HuggingFace API token.

        Returns:
            The token string or None if not set.
        """
        return self._hf_token

    @property
    def data_path(self) -> Path:
        """
        Get the data directory path.

        Returns:
            Absolute Path object for the data directory.
        """
        if self._data_path.is_absolute():
            return self._data_path
        # Resolve relative to project root
        project_root = Path(__file__).resolve().parent.parent
        return (project_root / self._data_path).resolve()

    @property
    def model_path(self) -> Path:
        """
        Get the model directory path or model ID.

        Returns:
            Absolute Path object if local, or the string model ID if remote.
        """
        if self._model_path.is_absolute():
            return self._model_path
        # Resolve relative to project root
        project_root = Path(__file__).resolve().parent.parent
        return (project_root / self._model_path).resolve()

    def ensure_data_dir(self) -> Path:
        """
        Ensure the data directory exists.

        Returns:
            The Path to the data directory.
        """
        self.data_path.mkdir(parents=True, exist_ok=True)
        return self.data_path

    def ensure_model_dir(self) -> Path:
        """
        Ensure the model directory exists.

        Returns:
            The Path to the model directory.
        """
        self.model_path.mkdir(parents=True, exist_ok=True)
        return self.model_path