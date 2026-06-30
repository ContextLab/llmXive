"""
Environment configuration management for the Visual Detail and False Memory project.

This module provides centralized configuration loading from environment variables
and a default configuration dictionary. It ensures all required paths and settings
are available throughout the application.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """
    Centralized configuration manager.

    Loads settings from environment variables with sensible defaults.
    All paths are resolved relative to the project root.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            project_root: Path to project root. If None, defaults to the
                         directory containing this module's parent (code/).
        """
        self._project_root = project_root or Path(__file__).resolve().parent.parent
        self._config: Dict[str, Any] = self._load_config()

    @property
    def project_root(self) -> Path:
        """Return the project root directory."""
        return self._project_root

    @property
    def data_dir(self) -> Path:
        """Return the base data directory."""
        return self.project_root / "data"

    @property
    def stimuli_dir(self) -> Path:
        """Return the stimuli directory."""
        return self.data_dir / "stimuli"

    @property
    def stimuli_metadata_dir(self) -> Path:
        """Return the stimuli metadata directory."""
        return self.data_dir / "stimuli_metadata"

    @property
    def responses_dir(self) -> Path:
        """Return the responses directory."""
        return self.data_dir / "responses"

    @property
    def processed_dir(self) -> Path:
        """Return the processed data directory."""
        return self.data_dir / "processed"

    @property
    def ethics_dir(self) -> Path:
        """Return the ethics directory."""
        return self.data_dir / "ethics"

    @property
    def logs_dir(self) -> Path:
        """Return the logs directory (within data)."""
        return self.data_dir / "logs"

    @property
    def figures_dir(self) -> Path:
        """Return the figures directory."""
        return self.data_dir / "figures"

    @property
    def code_dir(self) -> Path:
        """Return the code directory."""
        return self.project_root / "code"

    @property
    def test_dir(self) -> Path:
        """Return the tests directory."""
        return self.project_root / "tests"

    # Environment-based settings
    @property
    def log_level(self) -> str:
        """Return the logging level (default: INFO)."""
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def debug_mode(self) -> bool:
        """Return whether debug mode is enabled."""
        return os.getenv("DEBUG_MODE", "false").lower() == "true"

    @property
    def mock_mode(self) -> bool:
        """
        Return whether to use mock/synthetic data generation.
        Defaults to True as per plan.md instructions.
        """
        return os.getenv("MOCK_MODE", "true").lower() == "true"

    @property
    def visual_genome_url(self) -> Optional[str]:
        """Return the Visual Genome dataset URL if set, else None."""
        url = os.getenv("VISUAL_GENOME_URL")
        return url if url else None

    @property
    def output_format(self) -> str:
        """Return the output format for processed data (default: json)."""
        return os.getenv("OUTPUT_FORMAT", "json").lower()

    @property
    def random_seed(self) -> int:
        """Return the random seed for reproducibility (default: 42)."""
        return int(os.getenv("RANDOM_SEED", "42"))

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: The configuration key.
            default: Default value if key not found.

        Returns:
            The configuration value or default.
        """
        return self._config.get(key, default)

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.

        Returns:
            Dictionary of configuration values.
        """
        return {
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "stimuli_dir": str(self.stimuli_dir),
            "stimuli_metadata_dir": str(self.stimuli_metadata_dir),
            "responses_dir": str(self.responses_dir),
            "processed_dir": str(self.processed_dir),
            "ethics_dir": str(self.ethics_dir),
            "logs_dir": str(self.logs_dir),
            "figures_dir": str(self.figures_dir),
            "code_dir": str(self.code_dir),
            "test_dir": str(self.test_dir),
            "log_level": self.log_level,
            "debug_mode": self.debug_mode,
            "mock_mode": self.mock_mode,
            "visual_genome_url": self.visual_genome_url,
            "output_format": self.output_format,
            "random_seed": self.random_seed,
        }

    def ensure_dirs_exist(self) -> None:
        """
        Ensure all required data directories exist.

        Creates directories if they don't exist.
        """
        dirs = [
            self.stimuli_dir,
            self.stimuli_metadata_dir,
            self.responses_dir,
            self.processed_dir,
            self.ethics_dir,
            self.logs_dir,
            self.figures_dir,
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)


# Singleton instance for easy access
_config_instance: Optional[Config] = None


def get_config(project_root: Optional[Path] = None) -> Config:
    """
    Get the singleton configuration instance.

    Args:
        project_root: Optional project root override.

    Returns:
        The Config instance.
    """
    global _config_instance
    if _config_instance is None or (
        project_root and _config_instance.project_root != project_root
    ):
        _config_instance = Config(project_root)
    return _config_instance


def main() -> None:
    """
    CLI entry point to display current configuration.

    Useful for debugging environment setup.
    """
    config = get_config()

    print("=== Project Configuration ===")
    print(f"Project Root: {config.project_root}")
    print(f"Data Directory: {config.data_dir}")
    print(f"Stimuli Directory: {config.stimuli_dir}")
    print(f"Stimuli Metadata: {config.stimuli_metadata_dir}")
    print(f"Responses Directory: {config.responses_dir}")
    print(f"Processed Directory: {config.processed_dir}")
    print(f"Ethics Directory: {config.ethics_dir}")
    print(f"Logs Directory: {config.logs_dir}")
    print(f"Figures Directory: {config.figures_dir}")
    print(f"Log Level: {config.log_level}")
    print(f"Debug Mode: {config.debug_mode}")
    print(f"Mock Mode: {config.mock_mode}")
    print(f"Random Seed: {config.random_seed}")
    print(f"Visual Genome URL: {config.visual_genome_url or 'Not set (using mock)'}")
    print(f"Output Format: {config.output_format}")

    print("\n=== Ensuring directories exist... ===")
    config.ensure_dirs_exist()
    print("All directories ready.")


if __name__ == "__main__":
    main()