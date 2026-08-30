"""
Environment configuration management for API keys.
Loads API keys from .env file and provides secure access.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def load_dotenv_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, looks for .env in project root.
        
    Returns:
        Dictionary of loaded environment variables.
        
    Raises:
        FileNotFoundError: If the .env file does not exist.
    """
    if env_path is None:
        # Default to .env in project root (parent of code/)
        env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        # Check for .env in current working directory as fallback
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            env_path = cwd_env
        else:
            raise FileNotFoundError(
                f"Environment file not found at {env_path} or {Path.cwd() / '.env'}. "
                "Please create a .env file with your API keys."
            )
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                env_vars[key] = value
                # Set in os.environ for standard access
                os.environ[key] = value
    
    logger.info(f"Loaded {len(env_vars)} environment variables from {env_path}")
    return env_vars

def get_api_key(service: str) -> str:
    """
    Retrieve an API key from environment variables.
    
    Args:
        service: Service name ('MP' for Materials Project, 'NREL' for NREL).
        
    Returns:
        The API key string.
        
    Raises:
        KeyError: If the API key is not found in environment variables.
    """
    key_mapping = {
        'MP': 'MP_API_KEY',
        'MATERIALS_PROJECT': 'MP_API_KEY',
        'NREL': 'NREL_API_KEY'
    }
    
    env_var_name = key_mapping.get(service.upper())
    if not env_var_name:
        raise KeyError(f"Unknown service: {service}. Supported: {list(key_mapping.keys())}")
    
    api_key = os.environ.get(env_var_name)
    
    if not api_key:
        raise KeyError(
            f"API key for {service} not found in environment. "
            f"Please set {env_var_name} in your .env file."
        )
    
    return api_key

def validate_environment(required_services: list = None) -> Dict[str, bool]:
    """
    Validate that required API keys are present in the environment.
    
    Args:
        required_services: List of service names to validate. Defaults to all known services.
        
    Returns:
        Dictionary mapping service names to validation status (True/False).
    """
    if required_services is None:
        required_services = ['MP', 'NREL']
    
    validation_results = {}
    
    for service in required_services:
        try:
            get_api_key(service)
            validation_results[service] = True
            logger.info(f"API key for {service} is present and valid.")
        except KeyError as e:
            validation_results[service] = False
            logger.warning(f"API key validation failed for {service}: {e}")
    
    return validation_results

def main():
    """Main entry point for environment configuration validation."""
    logger.info("Validating environment configuration...")
    
    try:
        load_dotenv_file()
    except FileNotFoundError as e:
        logger.error(str(e))
        print("Please create a .env file with your API keys. See code/.env.example for template.")
        return 1
    
    validation_results = validate_environment()
    
    all_valid = all(validation_results.values())
    
    print("\nEnvironment Validation Results:")
    print("-" * 40)
    for service, is_valid in validation_results.items():
        status = "✓ VALID" if is_valid else "✗ MISSING"
        print(f"{service:20} {status}")
    print("-" * 40)
    
    if all_valid:
        print("All required API keys are configured.")
        return 0
    else:
        print("Some API keys are missing. Please update your .env file.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
