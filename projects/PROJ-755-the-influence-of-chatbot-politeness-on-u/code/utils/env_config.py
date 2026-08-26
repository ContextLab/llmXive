"""
Environment configuration management utilities.
Handles loading .env files, validating required variables, and providing access to them.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv


class EnvConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass


def load_env_config(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, searches in the current directory.
        
    Returns:
        Dictionary of loaded environment variables.
        
    Raises:
        EnvConfigError: If the .env file cannot be read.
    """
    if env_path is None:
        env_path = Path(find_dotenv())
        
    if not env_path.exists():
        # If no .env file exists, return empty dict (some vars might be in system env)
        return {}
        
    try:
        load_dotenv(str(env_path), override=True)
        return {k: v for k, v in os.environ.items() if v is not None}
    except Exception as e:
        raise EnvConfigError(f"Failed to load environment config from {env_path}: {e}")


def get_hf_token(required: bool = True) -> Optional[str]:
    """
    Retrieve the Hugging Face token from environment variables.
    
    Args:
        required: If True, raises an error if the token is missing.
                
    Returns:
        The HF_TOKEN value if found, None otherwise.
        
    Raises:
        EnvConfigError: If required=True and token is missing.
    """
    token = os.getenv("HF_TOKEN")
    
    if required and not token:
        raise EnvConfigError(
            "HF_TOKEN is not set. Please set it in your .env file or environment. "
            "See code/.env.example for instructions."
        )
        
    return token


def validate_env_config(required_vars: list[str]) -> Dict[str, bool]:
    """
    Validate that all required environment variables are present and non-empty.
    
    Args:
        required_vars: List of variable names that must be present.
        
    Returns:
        Dictionary mapping variable names to boolean (True if valid).
        
    Raises:
        EnvConfigError: If any required variable is missing or empty.
    """
    results = {}
    missing = []
    
    for var in required_vars:
        val = os.getenv(var)
        is_valid = bool(val)
        results[var] = is_valid
        if not is_valid:
            missing.append(var)
            
    if missing:
        raise EnvConfigError(
            f"Missing or empty required environment variables: {', '.join(missing)}. "
            "Please update your .env file."
        )
        
    return results


def create_env_template(output_path: Path, template_vars: Dict[str, str]) -> None:
    """
    Create a .env.example file with placeholder values.
    
    Args:
        output_path: Where to write the template file.
        template_vars: Dictionary of variable names to placeholder descriptions.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        f"# {output_path.name}",
        "# Auto-generated environment variable template.",
        "# Copy this file to .env and fill in your values.",
        ""
    ]
    
    for var, description in template_vars.items():
        lines.append(f"# {description}")
        lines.append(f"{var}=")
        lines.append("")
        
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def ensure_env_file_exists(env_path: Optional[Path] = None) -> Path:
    """
    Ensure the .env file exists. If not, copy from .env.example.
    
    Args:
        env_path: Path to the .env file.
        
    Returns:
        Path to the existing or newly created .env file.
    """
    if env_path is None:
        env_path = Path(".env")
        
    env_example = Path(".env.example")
    
    if not env_path.exists():
        if env_example.exists():
            # Copy template to .env
            with open(env_example, 'r') as src:
                content = src.read()
            with open(env_path, 'w') as dst:
                dst.write(content)
            return env_path
        else:
            # No template found, create empty one
            with open(env_path, 'w') as f:
                f.write("# Environment variables\n")
            return env_path
            
    return env_path
