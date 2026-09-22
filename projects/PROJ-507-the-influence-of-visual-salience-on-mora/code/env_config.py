"""
Environment variable management for dataset paths and API keys.

This module provides a centralized way to manage environment variables
required for the project, including dataset paths and API keys.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)


class EnvironmentConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass


@dataclass
class EnvConfig:
    """
    Configuration container for all environment variables.

    Attributes:
        DATA_RAW_PATH: Path to raw data directory
        DATA_PROCESSED_PATH: Path to processed data directory
        DATA_SURVEY_PATH: Path to survey data directory
        DATA_SYNTH_PATH: Path to synthetic data directory
        HF_TOKEN: Hugging Face API token
        MORALD_URL: URL for MoralD dataset
        VISUAL_GENOME_URL: URL for Visual Genome dataset
        VERIFIED_DATA_SOURCE: Verified data source override
        CLIP_MODEL_NAME: Name of CLIP model to use
        SEED: Random seed for reproducibility
    """
    DATA_RAW_PATH: str = field(default="data/raw")
    DATA_PROCESSED_PATH: str = field(default="data/processed")
    DATA_SURVEY_PATH: str = field(default="data/survey")
    DATA_SYNTH_PATH: str = field(default="data/synth")
    HF_TOKEN: Optional[str] = None
    MORALD_URL: str = field(default="https://huggingface.co/datasets/morald")
    VISUAL_GENOME_URL: str = field(default="https://huggingface.co/datasets/visual_genome")
    VERIFIED_DATA_SOURCE: Optional[str] = None
    CLIP_MODEL_NAME: str = field(default="openai/clip-vit-base-patch32")
    SEED: int = field(default=42)
    MIN_PRECISION: str = field(default="0.1")
    ALLOW_SYNTHETIC: bool = field(default=False)

    def __post_init__(self):
        """Validate and set environment variables from dataclass attributes."""
        # Convert paths to absolute paths relative to project root
        project_root = Path(__file__).parent.parent
        self.DATA_RAW_PATH = str(project_root / self.DATA_RAW_PATH)
        self.DATA_PROCESSED_PATH = str(project_root / self.DATA_PROCESSED_PATH)
        self.DATA_SURVEY_PATH = str(project_root / self.DATA_SURVEY_PATH)
        self.DATA_SYNTH_PATH = str(project_root / self.DATA_SYNTH_PATH)

        # Set environment variables for other modules to access
        os.environ['DATA_RAW_PATH'] = self.DATA_RAW_PATH
        os.environ['DATA_PROCESSED_PATH'] = self.DATA_PROCESSED_PATH
        os.environ['DATA_SURVEY_PATH'] = self.DATA_SURVEY_PATH
        os.environ['DATA_SYNTH_PATH'] = self.DATA_SYNTH_PATH
        os.environ['HF_TOKEN'] = self.HF_TOKEN or ""
        os.environ['MORALD_URL'] = self.MORALD_URL
        os.environ['VISUAL_GENOME_URL'] = self.VISUAL_GENOME_URL
        if self.VERIFIED_DATA_SOURCE:
            os.environ['VERIFIED_DATA_SOURCE'] = self.VERIFIED_DATA_SOURCE
        os.environ['CLIP_MODEL_NAME'] = self.CLIP_MODEL_NAME
        os.environ['SEED'] = str(self.SEED)
        os.environ['MIN_PRECISION'] = self.MIN_PRECISION
        os.environ['ALLOW_SYNTHETIC'] = str(self.ALLOW_SYNTHETIC).lower()


def get_config() -> EnvConfig:
    """
    Load configuration from environment variables.

    Returns:
        EnvConfig: Configuration object with values from environment or defaults.
    """
    # Read from environment variables with fallback to defaults
    config = EnvConfig(
        DATA_RAW_PATH=os.getenv('DATA_RAW_PATH', 'data/raw'),
        DATA_PROCESSED_PATH=os.getenv('DATA_PROCESSED_PATH', 'data/processed'),
        DATA_SURVEY_PATH=os.getenv('DATA_SURVEY_PATH', 'data/survey'),
        DATA_SYNTH_PATH=os.getenv('DATA_SYNTH_PATH', 'data/synth'),
        HF_TOKEN=os.getenv('HF_TOKEN'),
        MORALD_URL=os.getenv('MORALD_URL', 'https://huggingface.co/datasets/morald'),
        VISUAL_GENOME_URL=os.getenv('VISUAL_GENOME_URL', 'https://huggingface.co/datasets/visual_genome'),
        VERIFIED_DATA_SOURCE=os.getenv('VERIFIED_DATA_SOURCE'),
        CLIP_MODEL_NAME=os.getenv('CLIP_MODEL_NAME', 'openai/clip-vit-base-patch32'),
        SEED=int(os.getenv('SEED', '42')),
        MIN_PRECISION=os.getenv('MIN_PRECISION', '0.1'),
        ALLOW_SYNTHETIC=os.getenv('ALLOW_SYNTHETIC', 'False').lower() == 'true'
    )
    return config


def validate_environment(config: Optional[EnvConfig] = None) -> Dict[str, Any]:
    """
    Validate that all required environment variables are set correctly.

    Args:
        config: Optional EnvConfig object. If None, loads from environment.

    Returns:
        Dict with validation results.

    Raises:
        EnvironmentConfigError: If required variables are missing or invalid.
    """
    if config is None:
        config = get_config()

    issues = []
    warnings = []

    # Check required paths exist
    for path_name, path_val in [
        ('DATA_RAW_PATH', config.DATA_RAW_PATH),
        ('DATA_PROCESSED_PATH', config.DATA_PROCESSED_PATH),
        ('DATA_SURVEY_PATH', config.DATA_SURVEY_PATH),
        ('DATA_SYNTH_PATH', config.DATA_SYNTH_PATH),
    ]:
        path_obj = Path(path_val)
        if not path_obj.exists():
            issues.append(f"{path_name} does not exist: {path_val}")
        elif not path_obj.is_dir():
            issues.append(f"{path_name} is not a directory: {path_val}")

    # Check API keys if needed
    if not config.HF_TOKEN:
        warnings.append("HF_TOKEN not set. Some datasets may require authentication.")

    # Check URLs
    if not config.MORALD_URL or not config.MORALD_URL.startswith(('http://', 'https://')):
        issues.append(f"Invalid MORALD_URL: {config.MORALD_URL}")

    if not config.VISUAL_GENOME_URL or not config.VISUAL_GENOME_URL.startswith(('http://', 'https://')):
        issues.append(f"Invalid VISUAL_GENOME_URL: {config.VISUAL_GENOME_URL}")

    # Check seed
    if config.SEED < 0:
        issues.append(f"Invalid SEED (must be non-negative): {config.SEED}")

    # Check precision
    try:
        float(config.MIN_PRECISION)
    except ValueError:
        issues.append(f"Invalid MIN_PRECISION (must be numeric): {config.MIN_PRECISION}")

    result = {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'config': {
            'DATA_RAW_PATH': config.DATA_RAW_PATH,
            'DATA_PROCESSED_PATH': config.DATA_PROCESSED_PATH,
            'DATA_SURVEY_PATH': config.DATA_SURVEY_PATH,
            'DATA_SYNTH_PATH': config.DATA_SYNTH_PATH,
            'HF_TOKEN': '***' if config.HF_TOKEN else None,
            'MORALD_URL': config.MORALD_URL,
            'VISUAL_GENOME_URL': config.VISUAL_GENOME_URL,
            'VERIFIED_DATA_SOURCE': config.VERIFIED_DATA_SOURCE,
            'CLIP_MODEL_NAME': config.CLIP_MODEL_NAME,
            'SEED': config.SEED,
            'MIN_PRECISION': config.MIN_PRECISION,
            'ALLOW_SYNTHETIC': config.ALLOW_SYNTHETIC,
        }
    }

    if issues:
        raise EnvironmentConfigError(f"Environment configuration errors: {issues}")

    return result


def setup_env_file_example(output_path: Optional[str] = None) -> None:
    """
    Generate an example .env file with all required variables.

    Args:
        output_path: Path to write the example .env file. Defaults to project root.
    """
    if output_path is None:
        output_path = str(Path(__file__).parent.parent / '.env.example')

    content = """# Environment Configuration for Visual Salience Project
# Copy this file to .env and fill in your values

# Data Paths (relative to project root)
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed
DATA_SURVEY_PATH=data/survey
DATA_SYNTH_PATH=data/synth

# API Keys
HF_TOKEN=your_huggingface_token_here

# Dataset URLs
MORALD_URL=https://huggingface.co/datasets/morald
VISUAL_GENOME_URL=https://huggingface.co/datasets/visual_genome

# Verified Data Source (optional, overrides default URLs)
# VERIFIED_DATA_SOURCE=your_verified_source

# Model Configuration
CLIP_MODEL_NAME=openai/clip-vit-base-patch32

# Reproducibility
SEED=42

# Analysis Configuration
MIN_PRECISION=0.1

# Synthetic Data Allowance (for testing only)
ALLOW_SYNTHETIC=False
"""
    with open(output_path, 'w') as f:
        f.write(content)

    logger.info(f"Example .env file created at: {output_path}")


def main():
    """Main function to demonstrate environment configuration."""
    import argparse

    parser = argparse.ArgumentParser(description='Environment Configuration Utility')
    parser.add_argument('--validate', action='store_true', help='Validate current environment')
    parser.add_argument('--generate-example', action='store_true', help='Generate example .env file')
    parser.add_argument('--show-config', action='store_true', help='Show current configuration')

    args = parser.parse_args()

    if args.generate_example:
        setup_env_file_example()
        return

    if args.show_config:
        config = get_config()
        print("Current Configuration:")
        print(f"  DATA_RAW_PATH: {config.DATA_RAW_PATH}")
        print(f"  DATA_PROCESSED_PATH: {config.DATA_PROCESSED_PATH}")
        print(f"  DATA_SURVEY_PATH: {config.DATA_SURVEY_PATH}")
        print(f"  DATA_SYNTH_PATH: {config.DATA_SYNTH_PATH}")
        print(f"  HF_TOKEN: {'***' if config.HF_TOKEN else 'Not set'}")
        print(f"  MORALD_URL: {config.MORALD_URL}")
        print(f"  VISUAL_GENOME_URL: {config.VISUAL_GENOME_URL}")
        print(f"  VERIFIED_DATA_SOURCE: {config.VERIFIED_DATA_SOURCE or 'Not set'}")
        print(f"  CLIP_MODEL_NAME: {config.CLIP_MODEL_NAME}")
        print(f"  SEED: {config.SEED}")
        print(f"  MIN_PRECISION: {config.MIN_PRECISION}")
        print(f"  ALLOW_SYNTHETIC: {config.ALLOW_SYNTHETIC}")
        return

    if args.validate:
        try:
            result = validate_environment()
            print("Environment Validation:")
            print(f"  Valid: {result['valid']}")
            if result['issues']:
                print("  Issues:")
                for issue in result['issues']:
                    print(f"    - {issue}")
            if result['warnings']:
                print("  Warnings:")
                for warning in result['warnings']:
                    print(f"    - {warning}")
        except EnvironmentConfigError as e:
            print(f"Environment Configuration Error: {e}")
            return 1
        return 0

    # Default: show configuration
    main()


if __name__ == '__main__':
    import sys
    sys.exit(main())