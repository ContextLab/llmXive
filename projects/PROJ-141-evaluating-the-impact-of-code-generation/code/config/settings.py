"""
Environment Configuration Management for API keys, dataset paths, and IRB settings.

This module provides centralized configuration management for the experiment.
It loads settings from environment variables with sensible defaults.

Configuration is organized into sections:
- Database: SQLite path and settings
- Datasets: Paths to HumanEval and Codeforces datasets
- IRB: Institutional Review Board approval settings
- Models: Configuration for code generation models
- Logging: Log file paths and levels
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime


def get_env_var(name: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Get environment variable with optional default and required flag.

    Args:
        name: Environment variable name
        default: Default value if not set
        required: If True, raise error when not set

    Returns:
        Environment variable value or default

    Raises:
        ValueError: If required and not set
    """
    value = os.getenv(name, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{name}' is not set")
    return value if value else ""


def get_config() -> Dict[str, Any]:
    """
    Get complete configuration dictionary.

    Returns:
        Dictionary with all configuration sections
    """
    return {
        'database': get_database_config(),
        'datasets': get_datasets_config(),
        'irb': load_irb_config(),
        'models': get_models_config(),
        'logging': get_logging_config(),
        'experiment': get_experiment_config()
    }


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration.

    Returns:
        Dictionary with database settings
    """
    return {
        'path': get_env_var('DATABASE_PATH', 'data/experiment.db'),
        'pool_size': int(get_env_var('DB_POOL_SIZE', '5')),
        'timeout': int(get_env_var('DB_TIMEOUT', '30'))
    }


def get_datasets_config() -> Dict[str, Any]:
    """
    Get dataset configuration.

    Returns:
        Dictionary with dataset paths and settings
    """
    return {
        'humaneval': {
            'path': get_env_var('HUMANEVAL_PATH', 'data/humaneval'),
            'url': get_env_var('HUMANEVAL_URL', 'https://huggingface.co/datasets/openai_humaneval/resolve/main/human_eval.jsonl'),
            'commit_hash': get_env_var('HUMANEVAL_COMMIT', None)
        },
        'codeforces': {
            'path': get_env_var('CODEFORCES_PATH', 'data/codeforces'),
            'url': get_env_var('CODEFORCES_URL', None),
            'commit_hash': get_env_var('CODEFORCES_COMMIT', None)
        },
        'output_dir': get_env_var('DATASET_OUTPUT_DIR', 'data/processed')
    }


def load_irb_config() -> Dict[str, Any]:
    """
    Load IRB (Institutional Review Board) configuration.

    This includes approval ID, expiration date, and consent form version.

    Returns:
        Dictionary with IRB settings
    """
    return {
        'irb_approval_id': get_env_var('IRB_APPROVAL_ID', 'IRB-2024-001'),
        'expected_irb_approval_id': get_env_var('EXPECTED_IRB_APPROVAL_ID', 'IRB-2024-001'),
        'irb_expiry_date': get_env_var('IRB_EXPIRY_DATE', '2025-12-31T23:59:59'),
        'consent_form_version': get_env_var('CONSENT_FORM_VERSION', datetime.now().strftime("%Y%m%d")),
        'data_retention_period_years': int(get_env_var('DATA_RETENTION_YEARS', '5')),
        'encryption_key': get_env_var('CODEX_ENCRYPTION_KEY', None)
    }


def get_models_config() -> Dict[str, Any]:
    """
    Get model configuration.

    Returns:
        Dictionary with model settings
    """
    return {
        'starcoder': {
            'path': get_env_var('STARCODER_PATH', 'models/starcoder'),
            'max_length': int(get_env_var('STARCODER_MAX_LENGTH', '512')),
            'temperature': float(get_env_var('STARCODER_TEMPERATURE', '0.7'))
        },
        'jacotext': {
            'path': get_env_var('JACOTEXT_PATH', 'models/jacotext'),
            'max_length': int(get_env_var('JACOTEXT_MAX_LENGTH', '512')),
            'temperature': float(get_env_var('JACOTEXT_TEMPERATURE', '0.7'))
        },
        'fallback_model': get_env_var('FALLBACK_MODEL', 'starcoder'),
        'cpu_only': get_env_var('CPU_ONLY', 'true').lower() == 'true'
    }


def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration.

    Returns:
        Dictionary with logging settings
    """
    return {
        'level': get_env_var('LOG_LEVEL', 'INFO'),
        'experiment_log': get_env_var('EXPERIMENT_LOG_PATH', 'logs/experiment.log'),
        'consent_log': get_env_var('CONSENT_LOG_PATH', 'logs/consent.log'),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }


def get_experiment_config() -> Dict[str, Any]:
    """
    Get experiment-specific configuration.

    Returns:
        Dictionary with experiment settings
    """
    return {
        'session_timeout_minutes': int(get_env_var('SESSION_TIMEOUT', '60')),
        'problem_timeout_seconds': int(get_env_var('PROBLEM_TIMEOUT', '300')),
        'max_attempts_per_problem': int(get_env_var('MAX_ATTEMPTS', '3')),
        'random_seed': int(get_env_var('RANDOM_SEED', '42')),
        'counterbalance_enabled': get_env_var('COUNTERBALANCE', 'true').lower() == 'true'
    }


def validate_config() -> bool:
    """
    Validate that all required configuration is present.

    Returns:
        True if valid, False otherwise
    """
    try:
        config = get_config()
        # Check required fields
        if not config['database']['path']:
            print("Error: Database path not configured")
            return False

        if not config['irb']['expected_irb_approval_id']:
            print("Error: Expected IRB approval ID not configured")
            return False

        return True
    except Exception as e:
        print(f"Configuration validation error: {e}")
        return False


def main():
    """
    Main function to display current configuration.
    Useful for debugging and verification.
    """
    print("=== Project Configuration ===\n")

    config = get_config()

    print("Database:")
    for key, value in config['database'].items():
        print(f"  {key}: {value}")

    print("\nDatasets:")
    for dataset, settings in config['datasets'].items():
        print(f"  {dataset}:")
        for key, value in settings.items():
            print(f"    {key}: {value}")

    print("\nIRB:")
    for key, value in config['irb'].items():
        # Mask sensitive values
        if 'key' in key.lower():
            value = "***" if value else None
        print(f"  {key}: {value}")

    print("\nModels:")
    for model, settings in config['models'].items():
        print(f"  {model}:")
        for key, value in settings.items():
            print(f"    {key}: {value}")

    print("\nLogging:")
    for key, value in config['logging'].items():
        print(f"  {key}: {value}")

    print("\nExperiment:")
    for key, value in config['experiment'].items():
        print(f"  {key}: {value}")

    print("\n=== Configuration Validation ===")
    if validate_config():
        print("Configuration is valid.")
    else:
        print("Configuration validation failed!")


if __name__ == "__main__":
    main()