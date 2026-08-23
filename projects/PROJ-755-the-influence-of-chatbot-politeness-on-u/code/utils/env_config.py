"""
Environment configuration management for the llmXive pipeline.

Handles loading, validation, and template creation for .env files,
specifically managing the HF_TOKEN required for Hugging Face operations.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv


class EnvConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass


def load_env_config(env_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Optional path to the .env file. If None, searches in 
                  current directory and parent directories.
                  
    Returns:
        Dictionary of loaded environment variables.
        
    Raises:
        EnvConfigError: If the .env file cannot be loaded.
    """
    try:
        if env_path:
            if not env_path.exists():
                raise EnvConfigError(f"Environment file not found: {env_path}")
            # Load from specific path
            load_dotenv(dotenv_path=str(env_path))
        else:
            # Load from default location
            found = find_dotenv()
            if not found:
                # If no .env found, return empty dict but don't error yet
                # as some vars might be set in the shell
                return {}
            load_dotenv()
        
        return dict(os.environ)
    except Exception as e:
        raise EnvConfigError(f"Failed to load environment config: {e}")


def get_hf_token() -> Optional[str]:
    """
    Retrieve the Hugging Face token from the environment.
    
    Returns:
        The HF_TOKEN string if present, None otherwise.
        
    Raises:
        EnvConfigError: If HF_TOKEN is required but missing/empty.
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        # Check if we are in a context where token is strictly required
        # For now, return None and let downstream components handle the error
        # or raise a specific error if the pipeline requires it.
        return None
    return token.strip()


def validate_env_config(required_vars: list[str]) -> Dict[str, bool]:
    """
    Validate that required environment variables are present.
    
    Args:
        required_vars: List of variable names that must be set.
        
    Returns:
        Dictionary mapping variable names to boolean (True if present).
        
    Raises:
        EnvConfigError: If any required variable is missing.
    """
    results = {}
    missing = []
    
    for var in required_vars:
        is_present = bool(os.getenv(var))
        results[var] = is_present
        if not is_present:
            missing.append(var)
            
    if missing:
        raise EnvConfigError(f"Missing required environment variables: {', '.join(missing)}")
        
    return results


def create_env_template(output_path: Optional[Path] = None) -> Path:
    """
    Create a .env.example template file if it doesn't exist.
    
    Args:
        output_path: Optional path for the template file. Defaults to 
                     project root/.env.example.
                     
    Returns:
        Path to the created template file.
    """
    if output_path is None:
        output_path = Path(".env.example")
        
    if output_path.exists():
        return output_path
        
    template_content = """# Hugging Face Access Token
# Required for downloading datasets and models from the Hugging Face Hub.
# Get your token at: https://huggingface.co/settings/tokens
# 
# Instructions:
# 1. Copy this file to .env in the project root.
# 2. Replace 'YOUR_HF_TOKEN_HERE' with your actual token.
# 3. Do not commit the .env file to version control.
HF_TOKEN=YOUR_HF_TOKEN_HERE
"""
    output_path.write_text(template_content)
    return output_path


def ensure_env_file_exists() -> Path:
    """
    Ensure .env file exists, creating a template if necessary.
    
    Returns:
        Path to the .env file.
        
    Raises:
        EnvConfigError: If .env file cannot be created.
    """
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    if not env_path.exists():
        if example_path.exists():
            # Copy example to .env
            env_path.write_text(example_path.read_text())
        else:
            # Create template
            create_env_template(example_path)
            # Copy example to .env
            env_path.write_text(example_path.read_text())
            
    return env_path