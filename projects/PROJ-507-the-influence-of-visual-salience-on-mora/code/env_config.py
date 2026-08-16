"""
Environment variable management for dataset paths and API keys.

This module provides a centralized configuration system for managing
environment variables required by the project, including dataset paths
and API keys. It enforces strict validation to ensure all required
variables are present before execution.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class EnvironmentConfigError(Exception):
    """Raised when environment configuration is invalid or missing required variables."""
    pass


class EnvConfig:
    """
    Container for validated environment configuration.

    Attributes:
        dataset_path (Path): Path to the raw dataset directory.
        api_keys (Dict[str, str]): Dictionary of API keys required by the project.
        log_level (str): Logging level configuration.
        debug_mode (bool): Whether debug mode is enabled.
    """

    def __init__(
        self,
        dataset_path: Path,
        api_keys: Dict[str, str],
        log_level: str = "INFO",
        debug_mode: bool = False
    ):
        self.dataset_path = dataset_path
        self.api_keys = api_keys
        self.log_level = log_level
        self.debug_mode = debug_mode

    def get_api_key(self, service_name: str) -> str:
        """
        Retrieve an API key for a specific service.

        Args:
            service_name: The name of the service (e.g., 'HUGGINGFACE_TOKEN').

        Returns:
            The API key string.

        Raises:
            EnvironmentConfigError: If the key is not found.
        """
        if service_name not in self.api_keys:
            raise EnvironmentConfigError(
                f"API key '{service_name}' not found in environment configuration."
            )
        return self.api_keys[service_name]

    def validate_paths(self) -> None:
        """
        Validate that all configured paths exist.

        Raises:
            EnvironmentConfigError: If a required path does not exist.
        """
        if not self.dataset_path.exists():
            raise EnvironmentConfigError(
                f"Dataset path does not exist: {self.dataset_path}"
            )
        if not self.dataset_path.is_dir():
            raise EnvironmentConfigError(
                f"Dataset path is not a directory: {self.dataset_path}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary (excluding sensitive keys if needed)."""
        return {
            "dataset_path": str(self.dataset_path),
            "api_keys": self.api_keys,  # Note: In production, consider masking these
            "log_level": self.log_level,
            "debug_mode": self.debug_mode
        }


# Default configuration keys
REQUIRED_ENV_VARS = [
    "DATASET_PATH",
    "HUGGINGFACE_TOKEN",
    "LOG_LEVEL"
]

OPTIONAL_ENV_VARS = [
    "DEBUG_MODE"
]

# Default values for optional variables
DEFAULTS = {
    "LOG_LEVEL": "INFO",
    "DEBUG_MODE": "False"
}


def get_config() -> EnvConfig:
    """
    Load and validate environment configuration.

    Returns:
        EnvConfig: Validated configuration object.

    Raises:
        EnvironmentConfigError: If required environment variables are missing.
    """
    # Check required variables
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentConfigError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    # Load dataset path
    dataset_path_str = os.getenv("DATASET_PATH")
    dataset_path = Path(dataset_path_str).resolve()

    # Load API keys
    api_keys = {
        "HUGGINGFACE_TOKEN": os.getenv("HUGGINGFACE_TOKEN", "")
    }

    # Load optional variables
    log_level = os.getenv("LOG_LEVEL", DEFAULTS["LOG_LEVEL"])
    debug_mode_str = os.getenv("DEBUG_MODE", DEFAULTS["DEBUG_MODE"])
    debug_mode = debug_mode_str.lower() in ("true", "1", "yes")

    return EnvConfig(
        dataset_path=dataset_path,
        api_keys=api_keys,
        log_level=log_level,
        debug_mode=debug_mode
    )


def validate_environment() -> bool:
    """
    Validate that all required environment variables are set.

    Returns:
        True if all required variables are present, False otherwise.
    """
    try:
        get_config()
        return True
    except EnvironmentConfigError:
        return False


def setup_env_file_example(output_path: Optional[str] = None) -> None:
    """
    Generate an example .env file with all required and optional variables.

    Args:
        output_path: Path to write the example .env file. Defaults to '.env.example' in project root.
    """
    if output_path is None:
        output_path = str(Path(__file__).parent.parent / ".env.example")

    content = """# Environment Configuration for llmXive Project
# Copy this file to .env and fill in your values

# Dataset Configuration
DATASET_PATH=/path/to/your/dataset

# API Keys
HUGGINGFACE_TOKEN=your_huggingface_token_here

# Logging Configuration
LOG_LEVEL=INFO

# Debug Mode
DEBUG_MODE=False
"""
    Path(output_path).write_text(content)
    print(f"Example .env file created at: {output_path}")
    print("Please copy to .env and update with your actual values.")