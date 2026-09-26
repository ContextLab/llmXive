"""
Environment configuration management module.

This module provides a structured way to handle environment variables
for the visual salience study pipeline. It includes validation,
default values, and a mechanism to generate .env.example files.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import logging

from logging_config import setup_logging, get_logger

# Initialize logger
logger = get_logger(__name__)

class EnvironmentConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass

@dataclass
class EnvConfig:
    """
    Data class to hold all environment configuration values.
    
    Attributes:
        visual_genome_url: Primary dataset source URL or ID
        visual_genome_fallback_url: Secondary dataset fallback URL
        survey_api_key: API key for survey deployment
        survey_platform: Survey platform type (prolific, qualtrics, mturk)
        verified_data_source: Verified source injection path
        random_seed: Random seed for reproducibility
        log_level: Logging level
        min_precision: Minimum precision threshold for CI
        human_coding_raw_path: Path to raw human coding annotations
        min_annotators: Minimum number of annotators required
        min_kappa: Minimum Cohen's Kappa threshold
        min_ambiguity: Minimum mean ambiguity score
        manipulation_config_path: Path to manipulation config YAML
        target_region: Target region for salience manipulation
        luminance_levels: Luminance levels for manipulation
        hf_token: HuggingFace API token
        aws_access_key_id: AWS access key
        aws_secret_access_key: AWS secret key
        mock_mode: Enable mock mode for local testing
        allow_synthetic_analysis: Allow synthetic data analysis
    """
    visual_genome_url: str = "morald"
    visual_genome_fallback_url: str = "visual_genome"
    survey_api_key: str = ""
    survey_platform: str = "prolific"
    verified_data_source: str = ""
    random_seed: int = 42
    log_level: str = "INFO"
    min_precision: str = "0.1"
    human_coding_raw_path: str = "data/raw/human_coding/"
    min_annotators: int = 3
    min_kappa: float = 0.6
    min_ambiguity: float = 3.5
    manipulation_config_path: str = "config/manipulation.yaml"
    target_region: str = "auto"
    luminance_levels: str = "low,medium,high"
    hf_token: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    mock_mode: bool = False
    allow_synthetic_analysis: bool = False

def get_config() -> EnvConfig:
    """
    Load environment configuration from environment variables.
    
    Returns:
        EnvConfig: Configuration object populated from environment variables.
    """
    return EnvConfig(
        visual_genome_url=os.getenv("VISUAL_GENOME_URL", "morald"),
        visual_genome_fallback_url=os.getenv("VISUAL_GENOME_FALLBACK_URL", "visual_genome"),
        survey_api_key=os.getenv("SURVEY_API_KEY", ""),
        survey_platform=os.getenv("SURVEY_PLATFORM", "prolific"),
        verified_data_source=os.getenv("VERIFIED_DATA_SOURCE", ""),
        random_seed=int(os.getenv("RANDOM_SEED", "42")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        min_precision=os.getenv("MIN_PRECISION", "0.1"),
        human_coding_raw_path=os.getenv("HUMAN_CODING_RAW_PATH", "data/raw/human_coding/"),
        min_annotators=int(os.getenv("MIN_ANNOTATORS", "3")),
        min_kappa=float(os.getenv("MIN_KAPPA", "0.6")),
        min_ambiguity=float(os.getenv("MIN_AMBIGUITY", "3.5")),
        manipulation_config_path=os.getenv("MANIPULATION_CONFIG_PATH", "config/manipulation.yaml"),
        target_region=os.getenv("TARGET_REGION", "auto"),
        luminance_levels=os.getenv("LUMINANCE_LEVELS", "low,medium,high"),
        hf_token=os.getenv("HF_TOKEN", ""),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        mock_mode=os.getenv("MOCK_MODE", "false").lower() == "true",
        allow_synthetic_analysis=os.getenv("ALLOW_SYNTHETIC_ANALYSIS", "false").lower() == "true"
    )

def validate_environment(config: Optional[EnvConfig] = None) -> List[str]:
    """
    Validate that required environment variables are set.
    
    Args:
        config: Optional EnvConfig object. If None, loads from environment.
    
    Returns:
        List[str]: List of validation error messages. Empty if valid.
    
    Raises:
        EnvironmentConfigError: If critical variables are missing.
    """
    if config is None:
        config = get_config()
    
    errors = []
    
    # Check for critical variables
    if not config.survey_api_key and not config.mock_mode:
        errors.append("SURVEY_API_KEY is not set. Set MOCK_MODE=true for local testing or provide a valid API key.")
    
    if config.min_precision.lower() == "deferred":
        errors.append("MIN_PRECISION is set to 'deferred'. Analysis will halt until a pre-registered value is provided.")
    
    # Log warnings for optional but recommended variables
    if not config.hf_token:
        logger.warning("HF_TOKEN is not set. Some HuggingFace datasets may not be accessible.")
    
    if not config.aws_access_key_id or not config.aws_secret_access_key:
        logger.warning("AWS credentials are not set. AWS-based data storage will not be available.")
    
    if errors:
        logger.error("Environment validation failed with the following errors:")
        for error in errors:
            logger.error(f"  - {error}")
        raise EnvironmentConfigError("Environment validation failed. See logs for details.")
    
    logger.info("Environment validation passed.")
    return []

def setup_env_file_example(output_path: Optional[str] = None) -> Path:
    """
    Generate a .env.example file with all required variables.
    
    Args:
        output_path: Optional path to write the file. Defaults to project root .env.example.
    
    Returns:
        Path: Path to the generated .env.example file.
    """
    if output_path is None:
        output_path = Path(".env.example")
    else:
        output_path = Path(output_path)
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = """# Environment Configuration for Visual Salience Study
# Copy this file to .env and fill in the actual values before running the pipeline.

# -----------------------------------------------------------------------------
# Dataset Configuration
# -----------------------------------------------------------------------------
# Primary dataset source (MoralD) - URL or HuggingFace dataset ID
# If using a direct download URL, set VISUAL_GENOME_URL to that URL.
# If using HuggingFace datasets, set this to the dataset ID (e.g., "morald").
VISUAL_GENOME_URL=morald

# Secondary dataset fallback (Visual Genome) - URL or HuggingFace dataset ID
# Used only if the primary source is unavailable.
VISUAL_GENOME_FALLBACK_URL=visual_genome

# -----------------------------------------------------------------------------
# Survey API Configuration
# -----------------------------------------------------------------------------
# API key for survey deployment platform (e.g., Prolific, Qualtrics, MTurk)
# Required for T023c/T024b (Real Survey Deployment)
SURVEY_API_KEY=your_survey_api_key_here

# Survey platform type: 'prolific', 'qualtrics', 'mturk'
SURVEY_PLATFORM=prolific

# -----------------------------------------------------------------------------
# Verified Data Source Injection
# -----------------------------------------------------------------------------
# If set, this overrides default dataset URLs with a verified source package/recipe.
# Format: "package_name:recipe_name" or "hf_hub_download:path/to/file"
# Example: VERIFIED_DATA_SOURCE=huggingface_hub:morald_subset_v1
# If empty, the pipeline will attempt to fetch from VISUAL_GENOME_URL.
VERIFIED_DATA_SOURCE=

# -----------------------------------------------------------------------------
# Reproducibility & Logging
# -----------------------------------------------------------------------------
# Random seed for all stochastic operations (default: 42)
RANDOM_SEED=42

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# -----------------------------------------------------------------------------
# Analysis Configuration
# -----------------------------------------------------------------------------
# Minimum precision threshold for confidence intervals (SC-005)
# If set to 'deferred', the pipeline will halt analysis until pre-registered value is provided.
MIN_PRECISION=0.1

# -----------------------------------------------------------------------------
# Human Coding Configuration
# -----------------------------------------------------------------------------
# Path to raw human coding annotations (CSV/JSON)
HUMAN_CODING_RAW_PATH=data/raw/human_coding/

# Minimum number of independent annotators required per scenario
MIN_ANNOTATORS=3

# Minimum Cohen's Kappa threshold for scenario inclusion
MIN_KAPPA=0.6

# Minimum mean ambiguity score for scenario inclusion
MIN_AMBIGUITY=3.5

# -----------------------------------------------------------------------------
# Manipulation Configuration
# -----------------------------------------------------------------------------
# Path to manipulation config YAML (generated by T016a)
MANIPULATION_CONFIG_PATH=config/manipulation.yaml

# Target region for salience manipulation (bounding box logic)
# Format: "x1,y1,x2,y2" or "center" for automatic detection
TARGET_REGION=auto

# Luminance levels for manipulation
LUMINANCE_LEVELS=low,medium,high

# -----------------------------------------------------------------------------
# Security & Access
# -----------------------------------------------------------------------------
# API keys for external services (e.g., HuggingFace, AWS S3)
HF_TOKEN=your_huggingface_token_here
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# -----------------------------------------------------------------------------
# Debugging & Development
# -----------------------------------------------------------------------------
# Enable mock mode for local testing (T024b, T015c1)
# Set to 'true' to use synthetic data paths instead of real data
MOCK_MODE=false

# Allow synthetic data analysis (overrides T063 check)
ALLOW_SYNTHETIC_ANALYSIS=false
"""
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Generated .env.example file at: {output_path}")
    except IOError as e:
        logger.error(f"Failed to write .env.example file: {e}")
        raise EnvironmentConfigError(f"Failed to write .env.example file: {e}")
    
    return output_path

def main():
    """
    Main entry point for the env_config module.
    
    This function validates the current environment and generates
    a .env.example file if it doesn't exist.
    """
    setup_logging()
    
    logger.info("=== Environment Configuration Check ===")
    
    # Generate .env.example if it doesn't exist
    env_example_path = Path(".env.example")
    if not env_example_path.exists():
        logger.info("Generating .env.example file...")
        setup_env_file_example()
        logger.info(".env.example file generated successfully.")
    else:
        logger.info(".env.example file already exists.")
    
    # Validate current environment
    try:
        config = get_config()
        validate_environment(config)
        logger.info("Environment validation successful.")
    except EnvironmentConfigError as e:
        logger.error(f"Environment validation failed: {e}")
        return 1
    
    logger.info("=== Environment Configuration Check Complete ===")
    return 0

if __name__ == "__main__":
    exit(main())