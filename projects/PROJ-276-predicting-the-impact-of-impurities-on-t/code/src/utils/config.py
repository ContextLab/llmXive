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
        env_path: Path to .env file. If None, defaults to project root/.env
        
    Returns:
        Dictionary of environment variables
        
    Raises:
        ConfigError: If file cannot be read or parsed
    """
    logger = get_project_logger()
    
    if env_path is None:
        project_root = get_project_root()
        env_path = project_root / ".env"
    else:
        env_path = Path(env_path)
        
    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}")
        return {}
        
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=VALUE
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key:
                        env_vars[key] = value
                        # Also set in actual environment
                        os.environ[key] = value
        logger.info(f"Loaded {len(env_vars)} variables from {env_path}")
    except Exception as e:
        raise ConfigError(f"Failed to load environment file {env_path}: {e}")
        
    return env_vars

def get_api_key(service_name: str, env_key: Optional[str] = None) -> str:
    """
    Retrieve an API key from environment variables.
    
    Args:
        service_name: Name of the service (for error messaging)
        env_key: Specific environment variable name. If None, uses SERVICE_NAME_API_KEY
                
    Returns:
        The API key string
        
    Raises:
        ConfigError: If the key is not found
    """
    if env_key is None:
        env_key = f"{service_name.upper()}_API_KEY"
        
    api_key = os.environ.get(env_key)
    
    if not api_key:
        raise ConfigError(
            f"API key for {service_name} not found. "
            f"Please set the {env_key} environment variable."
        )
        
    return api_key

def get_materials_project_api_key() -> str:
    """
    Retrieve the Materials Project API key.
    
    Returns:
        The Materials Project API key
        
    Raises:
        ConfigError: If the key is not found
    """
    return get_api_key("materials_project", "MP_API_KEY")

def get_huggingface_token() -> str:
    """
    Retrieve the HuggingFace token.
    
    Returns:
        The HuggingFace token
        
    Raises:
        ConfigError: If the token is not found
    """
    return get_api_key("huggingface", "HF_TOKEN")

def validate_materials_project_connection(api_key: Optional[str] = None) -> bool:
    """
    Validate connection to Materials Project API.
    
    Args:
        api_key: Optional API key. If None, retrieves from environment
                
    Returns:
        True if connection is valid, False otherwise
        
    Raises:
        ConfigError: If API key is missing
    """
    logger = get_project_logger()
    
    if api_key is None:
        try:
            api_key = get_materials_project_api_key()
        except ConfigError:
            logger.error("Materials Project API key not configured")
            return False
            
    # Test endpoint - Materials Project API v2
    # Using a simple materials query to validate
    url = "https://api.materialsproject.org/v2/documents/materials/mp-100"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info("Materials Project API connection validated successfully")
            return True
        elif response.status_code == 401:
            logger.error("Materials Project API key is invalid (401 Unauthorized)")
            return False
        else:
            logger.warning(f"Materials Project API returned status {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        logger.error("Materials Project API connection timed out")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Materials Project API connection failed: {e}")
        return False

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path object pointing to project root
    """
    # Assume project root is 4 levels up from this file
    # code/src/utils/config.py -> code/ -> project root
    return Path(__file__).resolve().parent.parent.parent.parent

def get_config_summary() -> Dict[str, Any]:
    """
    Generate a summary of current configuration status.
    
    Returns:
        Dictionary containing configuration status for all services
    """
    summary = {
        "project_root": str(get_project_root()),
        "environment_loaded": bool(os.environ.get("MP_API_KEY") or os.environ.get("HF_TOKEN")),
        "services": {}
    }
    
    # Check Materials Project
    mp_key = os.environ.get("MP_API_KEY")
    summary["services"]["materials_project"] = {
        "configured": bool(mp_key),
        "key_present": bool(mp_key),
        "key_masked": f"{mp_key[:4]}...{mp_key[-4:]}" if mp_key and len(mp_key) > 8 else "N/A"
    }
    
    # Check HuggingFace
    hf_token = os.environ.get("HF_TOKEN")
    summary["services"]["huggingface"] = {
        "configured": bool(hf_token),
        "key_present": bool(hf_token),
        "key_masked": f"{hf_token[:4]}...{hf_token[-4:]}" if hf_token and len(hf_token) > 8 else "N/A"
    }
    
    return summary

def main():
    """Main entry point for config module testing."""
    print("=== llmXive Configuration Module ===")
    print(f"Project Root: {get_project_root()}")
    print(f"\nConfiguration Summary:")
    print(json.dumps(get_config_summary(), indent=2))
    
    print("\n=== Validating Materials Project Connection ===")
    if os.environ.get("MP_API_KEY"):
        is_valid = validate_materials_project_connection()
        print(f"Connection Valid: {is_valid}")
    else:
        print("MP_API_KEY not set in environment")
        
    print("\n=== Environment Variables Loaded ===")
    for key in ["MP_API_KEY", "HF_TOKEN"]:
        value = os.environ.get(key)
        if value:
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "N/A"
            print(f"{key}: {masked}")
        else:
            print(f"{key}: Not set")

if __name__ == "__main__":
    main()
