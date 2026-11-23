import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

# Project root relative to this script (assumes script is in code/)
PROJECT_ROOT = Path(__file__).parent.parent

# Default configuration file path
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"

# Required environment variables
REQUIRED_ENV_VARS = {
    "HF_TOKEN": "HuggingFace API token for authenticated dataset access",
    "HF_DATASETS_CACHE": "Optional: Path to cache HuggingFace datasets (defaults to ~/.cache/huggingface)",
}

def load_env_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. Defaults to config/settings.yaml.
        
    Returns:
        Dictionary containing configuration values.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is not valid YAML.
    """
    if config_path is None:
        config_path = CONFIG_PATH
        
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
        
    return config

def setup_huggingface_env(token: Optional[str] = None) -> None:
    """
    Configure HuggingFace environment variables.
    
    This function:
    1. Sets HF_TOKEN from the provided argument or HF_TOKEN environment variable.
    2. Sets HF_DATASETS_CACHE if specified in environment or config.
    3. Validates that HF_TOKEN is present and non-empty.
    
    Args:
        token: Optional HuggingFace token. If not provided, reads from HF_TOKEN env var.
        
    Raises:
        ValueError: If HF_TOKEN is missing or empty.
        RuntimeError: If required environment variables cannot be set.
    """
    # Determine token source
    if token is None:
        token = os.environ.get("HF_TOKEN")
        
    if not token or not token.strip():
        raise ValueError(
            "HF_TOKEN is required but not found. "
            "Please set the HF_TOKEN environment variable or pass it explicitly. "
            "You can obtain a token from https://huggingface.co/settings/tokens"
        )
    
    # Set the token
    os.environ["HF_TOKEN"] = token.strip()
    
    # Set HF_DATASETS_CACHE if not already set
    if "HF_DATASETS_CACHE" not in os.environ:
        default_cache = str(PROJECT_ROOT / "data" / "hf_cache")
        os.environ["HF_DATASETS_CACHE"] = default_cache
    
    # Verify the environment is set
    if not os.environ.get("HF_TOKEN"):
        raise RuntimeError("Failed to set HF_TOKEN environment variable")

def get_dataset_path(dataset_name: str) -> Path:
    """
    Get the local path for a dataset.
    
    This constructs a path under data/datasets/{dataset_name}.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'ultrafeedback', 'dolly').
        
    Returns:
        Path object pointing to the dataset directory.
    """
    return PROJECT_ROOT / "data" / "datasets" / dataset_name

def validate_env_setup(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate that all required environment variables and configurations are set.
    
    Args:
        config: Optional configuration dictionary. If not provided, loads from file.
        
    Returns:
        Dictionary with validation results:
        - 'valid': bool indicating overall validity
        - 'missing_vars': list of missing environment variables
        - 'config_warnings': list of warnings about configuration issues
        
    Raises:
        ValueError: If validation fails and the caller should halt execution.
    """
    if config is None:
        try:
            config = load_env_config()
        except FileNotFoundError:
            config = {}
    
    results = {
        "valid": True,
        "missing_vars": [],
        "config_warnings": []
    }
    
    # Check required environment variables
    for var_name, description in REQUIRED_ENV_VARS.items():
        if var_name not in os.environ:
            results["missing_vars"].append(var_name)
            results["valid"] = False
    
    # Check HF_TOKEN specifically
    if "HF_TOKEN" not in os.environ or not os.environ["HF_TOKEN"].strip():
        results["missing_vars"].append("HF_TOKEN")
        results["valid"] = False
    
    # Check for optional but recommended settings
    if "data" not in config:
        results["config_warnings"].append("No 'data' section found in config")
        
    if "datasets" not in config:
        results["config_warnings"].append("No 'datasets' section found in config")
    
    return results

def main() -> int:
    """
    Main entry point for environment setup and validation.
    
    This function:
    1. Loads configuration from config/settings.yaml
    2. Sets up HuggingFace environment variables
    3. Validates the environment setup
    4. Reports any issues or confirms success
    
    Returns:
        0 if setup is successful, 1 if validation fails.
    """
    print("=== llmXive Environment Setup ===")
    
    # Load configuration
    try:
        config = load_env_config()
        print(f"✓ Loaded configuration from {CONFIG_PATH}")
    except FileNotFoundError as e:
        print(f"⚠ Configuration file not found: {e}")
        print("  Continuing with default settings...")
        config = {}
    
    # Setup HuggingFace environment
    try:
        setup_huggingface_env()
        print("✓ HuggingFace environment configured")
    except ValueError as e:
        print(f"✗ Failed to configure HuggingFace environment: {e}")
        return 1
    
    # Validate environment
    validation_results = validate_env_setup(config)
    
    if validation_results["missing_vars"]:
        print(f"✗ Missing required environment variables: {', '.join(validation_results['missing_vars'])}")
        print("\nPlease set the following environment variables:")
        for var in validation_results["missing_vars"]:
            desc = REQUIRED_ENV_VARS.get(var, "No description")
            print(f"  export {var}=<value>  # {desc}")
        return 1
    
    if validation_results["config_warnings"]:
        print("⚠ Configuration warnings:")
        for warning in validation_results["config_warnings"]:
            print(f"  - {warning}")
    
    print("✓ Environment validation successful")
    
    # Print current settings
    print("\n=== Current Settings ===")
    print(f"HF_TOKEN: {'*' * 8} (set)")
    print(f"HF_DATASETS_CACHE: {os.environ.get('HF_DATASETS_CACHE')}")
    print(f"Dataset root: {PROJECT_ROOT / 'data' / 'datasets'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
