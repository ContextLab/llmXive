"""
Environment variable management for dataset paths and API keys.

This module provides a centralized way to manage environment variables
required for the project, including dataset paths, API keys, and configuration
flags. It ensures that all required environment variables are set before
proceeding with data operations.

Usage:
    from env_config import get_config, validate_environment

    config = get_config()
    validate_environment()
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


class EnvironmentConfigError(Exception):
    """Raised when environment configuration is invalid or missing required variables."""
    pass


@dataclass
class EnvConfig:
    """
    Configuration container for environment variables.

    Attributes:
        visual_genome_path: Path to the Visual Genome dataset directory
        morald_path: Path to the MoralD dataset directory
        huggingface_token: Hugging Face API token for authenticated downloads
        survey_api_key: API key for survey platforms (Prolific, Qualtrics, etc.)
        verified_data_source: Override for verified data source injection
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        seed: Random seed for reproducibility
        allow_synthetic: Flag to allow synthetic data fallback (default: False)
    """
    visual_genome_path: Optional[str] = None
    morald_path: Optional[str] = None
    huggingface_token: Optional[str] = None
    survey_api_key: Optional[str] = None
    verified_data_source: Optional[str] = None
    log_level: str = "INFO"
    seed: int = 42
    allow_synthetic: bool = False

    # Derived paths
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_raw_dir: Path = field(default_factory=lambda: Path("data/raw"))
    data_processed_dir: Path = field(default=lambda: Path("data/processed"))
    data_survey_dir: Path = field(default=lambda: Path("data/survey"))
    data_synth_dir: Path = field(default=lambda: Path("data/synth"))
    config_dir: Path = field(default=lambda: Path("config"))
    figures_dir: Path = field(default=lambda: Path("figures"))

    def __post_init__(self):
        """Initialize derived paths based on project root."""
        self.data_raw_dir = self.project_root / self.data_raw_dir
        self.data_processed_dir = self.project_root / self.data_processed_dir
        self.data_survey_dir = self.project_root / self.data_survey_dir
        self.data_synth_dir = self.project_root / self.data_synth_dir
        self.config_dir = self.project_root / self.config_dir
        self.figures_dir = self.project_root / self.figures_dir


# Singleton instance
_config_instance: Optional[EnvConfig] = None


def get_config() -> EnvConfig:
    """
    Get the singleton EnvConfig instance.

    Returns:
        EnvConfig: The configuration instance with all environment variables loaded.

    Raises:
        EnvironmentConfigError: If the configuration has not been initialized.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = _load_config_from_env()
    return _config_instance


def _load_config_from_env() -> EnvConfig:
    """
    Load configuration from environment variables.

    Returns:
        EnvConfig: Configuration object populated from environment variables.
    """
    return EnvConfig(
        visual_genome_path=os.getenv("VISUAL_GENOME_PATH"),
        morald_path=os.getenv("MORALD_PATH"),
        huggingface_token=os.getenv("HUGGINGFACE_TOKEN"),
        survey_api_key=os.getenv("SURVEY_API_KEY"),
        verified_data_source=os.getenv("VERIFIED_DATA_SOURCE"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        seed=int(os.getenv("RANDOM_SEED", "42")),
        allow_synthetic=os.getenv("ALLOW_SYNTHETIC", "false").lower() == "true"
    )


def validate_environment(required_vars: Optional[List[str]] = None) -> None:
    """
    Validate that all required environment variables are set.

    Args:
        required_vars: Optional list of specific variables to check. If None,
                      checks all variables that are marked as required by default.

    Raises:
        EnvironmentConfigError: If any required variable is missing.
    """
    if required_vars is None:
        # Default required variables for core functionality
        required_vars = ["HUGGINGFACE_TOKEN"]

    missing_vars = []
    for var in required_vars:
        if os.getenv(var) is None:
            missing_vars.append(var)

    if missing_vars:
        raise EnvironmentConfigError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            f"Please set these variables before running the pipeline. "
            f"See .env.example for a template."
        )


def setup_env_file_example(output_path: Optional[str] = None) -> Path:
    """
    Create an .env.example file with all available environment variables.

    Args:
        output_path: Path to write the example file. Defaults to project root/.env.example

    Returns:
        Path: The path to the created file.
    """
    if output_path is None:
        output_path = str(Path(__file__).parent.parent / ".env.example")

    content = """# Environment Configuration for Visual Salience Research
# Copy this file to .env and fill in your values

# Dataset Paths
VISUAL_GENOME_PATH=
MORALD_PATH=

# API Keys
HUGGINGFACE_TOKEN=
SURVEY_API_KEY=

# Configuration
VERIFIED_DATA_SOURCE=
LOG_LEVEL=INFO
RANDOM_SEED=42
ALLOW_SYNTHETIC=false

# Note: Do not commit your .env file to version control
"""

    Path(output_path).write_text(content)
    return Path(output_path)


def main():
    """
    Main entry point for testing environment configuration.
    """
    import logging
    from logging_config import setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Create example .env file
        env_example_path = setup_env_file_example()
        logger.info(f"Created .env.example at: {env_example_path}")

        # Load and display configuration
        config = get_config()
        logger.info("Environment configuration loaded successfully:")
        logger.info(f"  Visual Genome Path: {config.visual_genome_path}")
        logger.info(f"  MoralD Path: {config.morald_path}")
        logger.info(f"  HuggingFace Token: {'***' if config.huggingface_token else 'Not set'}")
        logger.info(f"  Survey API Key: {'***' if config.survey_api_key else 'Not set'}")
        logger.info(f"  Verified Data Source: {config.verified_data_source}")
        logger.info(f"  Log Level: {config.log_level}")
        logger.info(f"  Random Seed: {config.seed}")
        logger.info(f"  Allow Synthetic: {config.allow_synthetic}")
        logger.info(f"  Project Root: {config.project_root}")

        # Validate required variables
        try:
            validate_environment(["HUGGINGFACE_TOKEN"])
            logger.info("All required environment variables are set.")
        except EnvironmentConfigError as e:
            logger.warning(f"Environment validation warning: {e}")
            logger.info("This is expected if running without full configuration.")

    except EnvironmentConfigError as e:
        logger.error(f"Environment configuration error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())