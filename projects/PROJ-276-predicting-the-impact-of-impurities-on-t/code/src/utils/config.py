"""
Configuration management for the MgB2 Impurity Impact project.

Handles environment variable loading, API key retrieval, and project root detection.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json
import requests
from .logging import get_project_logger

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_env_file(env_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, looks for .env in project root.
        
    Returns:
        Dictionary of key-value pairs from the file.
        
    Raises:
        ConfigError: If the file is not found or cannot be parsed.
    """
    logger = get_project_logger()
    
    if env_path is None:
        project_root = get_project_root()
        env_path = str(project_root / ".env")
    
    env_vars = {}
    
    if not os.path.exists(env_path):
        logger.warning(f".env file not found at {env_path}. Using system environment variables.")
        return env_vars
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
                    
        logger.info(f"Loaded configuration from {env_path}")
    except Exception as e:
        raise ConfigError(f"Failed to load .env file: {e}")
        
    return env_vars

def get_api_key(key_name: str, env_vars: Optional[Dict[str, str]] = None) -> str:
    """
    Retrieve an API key from environment variables or .env file.
    
    Args:
        key_name: The name of the environment variable (e.g., 'MATERIALS_PROJECT_API_KEY').
        env_vars: Optional pre-loaded environment variables. If None, loads from .env.
        
    Returns:
        The API key string.
        
    Raises:
        ConfigError: If the key is not found in environment or .env file.
    """
    logger = get_project_logger()
    
    # First check system environment
    if key_name in os.environ:
        logger.debug(f"Found {key_name} in system environment")
        return os.environ[key_name]
    
    # Then check .env file
    if env_vars is None:
        env_vars = load_env_file()
        
    if key_name in env_vars:
        logger.debug(f"Found {key_name} in .env file")
        return env_vars[key_name]
        
    raise ConfigError(f"API key '{key_name}' not found in environment variables or .env file.")

def get_materials_project_api_key() -> str:
    """
    Retrieve the Materials Project API key.
    
    Returns:
        The Materials Project API key.
        
    Raises:
        ConfigError: If the key is not configured.
    """
    return get_api_key("MATERIALS_PROJECT_API_KEY")

def get_huggingface_token() -> str:
    """
    Retrieve the HuggingFace token.
    
    Returns:
        The HuggingFace token.
        
    Raises:
        ConfigError: If the token is not configured.
    """
    return get_api_key("HUGGINGFACE_TOKEN")

def validate_materials_project_connection(api_key: Optional[str] = None) -> bool:
    """
    Validate the connection to the Materials Project API.
    
    Args:
        api_key: Optional API key. If None, retrieves from config.
        
    Returns:
        True if connection is valid, False otherwise.
        
    Raises:
        ConfigError: If no API key is provided or found.
    """
    logger = get_project_logger()
    
    if api_key is None:
        try:
            api_key = get_materials_project_api_key()
        except ConfigError:
            logger.error("Materials Project API key not configured. Cannot validate connection.")
            return False
    
    try:
        # Test connection with a simple endpoint
        url = "https://api.materialsproject.org/v2/materials/MP-123"
        headers = {"X-API-Key": api_key}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info("Materials Project API connection validated successfully.")
            return True
        elif response.status_code == 401:
            logger.error("Materials Project API key is invalid (401 Unauthorized).")
            return False
        else:
            logger.warning(f"Materials Project API returned status {response.status_code}.")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Materials Project API: {e}")
        return False

def get_project_root() -> Path:
    """
    Determine the project root directory.
    
    Looks for a marker file or directory to identify the root.
    Assumes the project root contains 'src', 'tests', 'data', etc.
    
    Returns:
        Path to the project root.
    """
    # Start from current working directory
    current = Path.cwd()
    
    # Look for markers going up the tree
    markers = ['.git', 'pyproject.toml', 'setup.py', 'README.md']
    
    while current != current.parent:
        if any(current / marker for marker in markers):
            return current
        current = current.parent
        
    # Fallback: assume current directory is root
    return Path.cwd()

def get_config_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current configuration.
    
    Returns:
        Dictionary containing configuration status (without exposing actual keys).
    """
    project_root = get_project_root()
    env_path = project_root / ".env"
    
    # Check which keys are configured
    keys_to_check = [
        "MATERIALS_PROJECT_API_KEY",
        "HUGGINGFACE_TOKEN"
    ]
    
    configured_keys = []
    missing_keys = []
    
    for key in keys_to_check:
        if key in os.environ or (env_path.exists() and key in load_env_file(str(env_path))):
            configured_keys.append(key)
        else:
            missing_keys.append(key)
    
    return {
        "project_root": str(project_root),
        "env_file_exists": env_path.exists(),
        "configured_keys": configured_keys,
        "missing_keys": missing_keys,
        "total_configured": len(configured_keys),
        "total_required": len(keys_to_check)
    }

def main():
    """
    Main entry point for configuration validation and summary.
    """
    logger = get_project_logger()
    logger.info("Running configuration validation...")
    
    summary = get_config_summary()
    
    print("\n=== Configuration Summary ===")
    print(f"Project Root: {summary['project_root']}")
    print(f".env File Exists: {summary['env_file_exists']}")
    print(f"Configured Keys ({summary['total_configured']}): {', '.join(summary['configured_keys'])}")
    if summary['missing_keys']:
        print(f"Missing Keys ({len(summary['missing_keys'])}): {', '.join(summary['missing_keys'])}")
    print("=============================\n")
    
    # Validate Materials Project connection if key is available
    if "MATERIALS_PROJECT_API_KEY" in summary['configured_keys']:
        logger.info("Validating Materials Project connection...")
        if validate_materials_project_connection():
            print("✓ Materials Project API: Connected")
        else:
            print("✗ Materials Project API: Connection failed or invalid key")
    else:
        print("⚠ Materials Project API: Key not configured")
        
    # Validate HuggingFace token presence
    if "HUGGINGFACE_TOKEN" in summary['configured_keys']:
        print("✓ HuggingFace Token: Configured")
    else:
        print("⚠ HuggingFace Token: Not configured")
        
    logger.info("Configuration validation complete.")

if __name__ == "__main__":
    main()
