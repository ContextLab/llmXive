"""
Environment configuration management for llmXive pipeline.

Handles loading, validation, and access to environment variables,
specifically managing Hugging Face tokens and other secrets.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv


class EnvConfigError(Exception):
    """Raised when environment configuration is invalid or missing."""
    pass


def load_env_config(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Optional path to .env file. If None, searches in current
                 directory and parent directories.
                
    Returns:
        True if .env file was found and loaded, False otherwise.
        
    Raises:
        EnvConfigError: If the file exists but is unreadable.
    """
    if env_path:
        if not env_path.exists():
            return False
        if not env_path.is_file():
            raise EnvConfigError(f"Env path is not a file: {env_path}")
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Parse manually to avoid dependency on dotenv for basic checks
            # but use load_dotenv for actual loading if available
            if load_dotenv(dotenv_path=env_path):
                return True
        except (IOError, OSError) as e:
            raise EnvConfigError(f"Failed to read env file: {e}")
    else:
        # Try to find .env in current or parent directories
        dotenv_path = find_dotenv()
        if dotenv_path:
            try:
                if load_dotenv(dotenv_path=dotenv_path):
                    return True
            except Exception as e:
                raise EnvConfigError(f"Failed to load env file: {e}")
    
    return False


def get_hf_token(required: bool = False) -> Optional[str]:
    """
    Retrieve the Hugging Face API token.
    
    Args:
        required: If True, raises EnvConfigError when token is missing.
                
    Returns:
        The HF token string if available, None otherwise.
        
    Raises:
        EnvConfigError: If required=True and token is not found.
    """
    # Load env first if not already loaded
    load_env_config()
    
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_TOKEN")
    
    if required and not token:
        raise EnvConfigError(
            "HF_TOKEN is required but not found in environment. "
            "Please set it in a .env file or export it directly."
        )
    
    return token


def validate_env_config(required_vars: list[str]) -> Dict[str, bool]:
    """
    Validate that required environment variables are present.
    
    Args:
        required_vars: List of environment variable names that must be set.
        
    Returns:
        Dictionary mapping variable names to boolean (True if present).
        
    Raises:
        EnvConfigError: If any required variable is missing.
    """
    load_env_config()
    
    results = {}
    missing = []
    
    for var in required_vars:
        present = bool(os.getenv(var))
        results[var] = present
        if not present:
            missing.append(var)
    
    if missing:
        raise EnvConfigError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    
    return results


def create_env_template(output_path: Optional[Path] = None) -> Path:
    """
    Create a .env.template file with placeholders for required variables.
    
    Args:
        output_path: Optional path for the template file. Defaults to 
                    'code/.env.template' if not provided.
                    
    Returns:
        Path to the created template file.
    """
    if output_path is None:
        output_path = Path("code/.env.template")
    
    template_content = """# Hugging Face API Token
# Required for downloading datasets and models from Hugging Face Hub
# Get your token at: https://huggingface.co/settings/tokens
HF_TOKEN=

# Optional: Set to 'true' to skip interactive prompts in CLI tools
SKIP_PROMPTS=

# Optional: Custom cache directory for large models/datasets
HF_HOME=
"""
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    return output_path


def ensure_env_file_exists() -> Path:
    """
    Ensure a .env file exists, creating from template if necessary.
    
    Returns:
        Path to the .env file.
    """
    env_path = Path(".env")
    
    if not env_path.exists():
        template_path = Path("code/.env.template")
        if template_path.exists():
            # Copy template to .env
            with open(template_path, 'r', encoding='utf-8') as src:
                content = src.read()
            # Remove comments for the actual .env file (optional, keeping comments for clarity)
            # Actually, let's keep the comments but add a note
            content = content + "\n# Note: Fill in the values above. Do not commit this file.\n"
            with open(env_path, 'w', encoding='utf-8') as dst:
                dst.write(content)
            return env_path
        else:
            # Create a minimal one
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write("# HF_TOKEN=your_token_here\n")
            return env_path
    
    return env_path