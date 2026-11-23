"""
Environment configuration management for CPU-only execution flags.

This module provides a centralized configuration system to manage
environment-specific settings, with explicit support for CPU-only
execution mode.
"""

import os
import sys
from typing import Dict, Any, Optional
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """
    Configuration class for managing environment settings.

    Attributes:
        cpu_only (bool): Flag to enforce CPU-only execution.
        device (str): Target device ('cpu' or 'cuda').
        num_threads (int): Number of threads for CPU execution.
        verbose (bool): Enable verbose logging.
        config_path (Path): Path to the configuration file.
    """

    def __init__(
        self,
        cpu_only: bool = True,
        num_threads: int = 4,
        verbose: bool = False,
        config_path: Optional[Path] = None
    ):
        """
        Initialize the environment configuration.

        Args:
            cpu_only: If True, forces execution on CPU. Default is True.
        num_threads: Number of threads for CPU operations.
        verbose: Enable detailed logging.
        config_path: Optional path to a JSON configuration file.
        """
        self.cpu_only = cpu_only
        self.num_threads = num_threads
        self.verbose = verbose
        self.config_path = config_path or Path("config/environment.json")

        # Determine device based on cpu_only flag
        self.device = "cpu" if self.cpu_only else "cuda"

        # Apply CPU thread constraints if in CPU mode
        if self.cpu_only:
            self._configure_cpu_threads()

        logger.info(f"EnvironmentConfig initialized: cpu_only={self.cpu_only}, device={self.device}")

    def _configure_cpu_threads(self) -> None:
        """
        Configure CPU thread limits for optimal performance.

        Sets environment variables for popular libraries to respect
        the configured thread count.
        """
        os.environ["OMP_NUM_THREADS"] = str(self.num_threads)
        os.environ["MKL_NUM_THREADS"] = str(self.num_threads)
        os.environ["OPENBLAS_NUM_THREADS"] = str(self.num_threads)
        os.environ["VECLIB_MAXIMUM_THREADS"] = str(self.num_threads)
        os.environ["NUMEXPR_NUM_THREADS"] = str(self.num_threads)

        # Explicitly disable CUDA if cpu_only is True
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

        logger.debug(f"CPU threads configured: {self.num_threads}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "cpu_only": self.cpu_only,
            "device": self.device,
            "num_threads": self.num_threads,
            "verbose": self.verbose,
            "config_path": str(self.config_path)
        }

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save the current configuration to a JSON file.

        Args:
            path: Optional path to save the config. Defaults to config_path.
        """
        save_path = path or self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Configuration saved to {save_path}")

    @classmethod
    def load(cls, path: Path) -> 'EnvironmentConfig':
        """
        Load configuration from a JSON file.

        Args:
            path: Path to the configuration file.

        Returns:
            An instance of EnvironmentConfig.
        """
        if not path.exists():
            logger.warning(f"Config file not found at {path}. Using defaults.")
            return cls()

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(
            cpu_only=data.get("cpu_only", True),
            num_threads=data.get("num_threads", 4),
            verbose=data.get("verbose", False),
            config_path=path
        )

    def validate(self) -> bool:
        """
        Validate the current configuration state.

        Checks for consistency and potential conflicts.

        Returns:
            True if valid, False otherwise.
        """
        if not self.cpu_only and self.device != "cuda":
            logger.warning("cpu_only is False but device is not set to cuda.")
            return False

        if self.num_threads < 1:
            logger.error("num_threads must be at least 1.")
            return False

        return True


def get_env_config(config_path: Optional[Path] = None) -> EnvironmentConfig:
    """
    Factory function to retrieve the environment configuration.

    Checks for environment variables first, then falls back to file loading.

    Args:
        config_path: Optional path to override the default config file.

    Returns:
        An initialized EnvironmentConfig instance.
    """
    # Check for environment variable override
    cpu_only_env = os.getenv("LLMXIVE_CPU_ONLY", "true").lower()
    cpu_only = cpu_only_env in ("true", "1", "yes")

    num_threads_env = os.getenv("LLMXIVE_NUM_THREADS", "4")
    try:
        num_threads = int(num_threads_env)
    except ValueError:
        num_threads = 4
        logger.warning(f"Invalid LLMXIVE_NUM_THREADS value '{num_threads_env}', defaulting to 4.")

    verbose_env = os.getenv("LLMXIVE_VERBOSE", "false").lower()
    verbose = verbose_env in ("true", "1", "yes")

    path = config_path
    if path is None:
        # Check for config file path in env
        path_str = os.getenv("LLMXIVE_CONFIG_PATH")
        if path_str:
            path = Path(path_str)

    config = EnvironmentConfig(
        cpu_only=cpu_only,
        num_threads=num_threads,
        verbose=verbose,
        config_path=path
    )

    if not config.validate():
        logger.error("Configuration validation failed.")
        # In a strict pipeline, we might raise here, but for now we return the config
        # with the understanding that it may need manual correction.

    return config


def main() -> None:
    """
    Main entry point for the environment configuration script.

    Demonstrates loading, saving, and validating the configuration.
    """
    logger.info("Starting Environment Configuration Manager.")

    # Load or create config
    config = get_env_config()

    # Display current settings
    print("\nCurrent Environment Configuration:")
    print("-" * 30)
    for key, value in config.to_dict().items():
        if key != "config_path": # Avoid printing path in summary unless needed
            print(f"{key}: {value}")
    print("-" * 30)

    # Validate
    if config.validate():
        print("Configuration is valid.")
    else:
        print("Configuration validation failed.")
        sys.exit(1)

    # Save to default location for demonstration
    try:
        config.save()
        print(f"Configuration saved to {config.config_path}")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        sys.exit(1)

    # Verify device setting
    if config.cpu_only:
        print("CPU-Only Mode is ACTIVE. CUDA operations are disabled.")
    else:
        print("GPU Mode is enabled. Ensure CUDA is available.")

    logger.info("Environment Configuration Manager finished.")


if __name__ == "__main__":
    main()
