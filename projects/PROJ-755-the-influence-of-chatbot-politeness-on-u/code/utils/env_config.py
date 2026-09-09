"""
Environment configuration utilities.

Handles loading, validation, and template creation for project environment variables.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv
import logging

logger = logging.getLogger(__name__)

class EnvConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass

def load_env_config(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load environment variables from .env file.
    
    Args:
        project_root: Path to the project root directory. Defaults to current working directory.
        
    Returns:
        Dictionary of loaded environment variables.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Loaded environment from {env_path}")
    else:
        logger.warning(f"No .env file found at {env_path}")
    
    return dict(os.environ)

def get_hf_token(project_root: Optional[Path] = None) -> Optional[str]:
    """
    Retrieve the Hugging Face token from environment variables.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        The HF_TOKEN value or None if not found.
    """
    load_env_config(project_root)
    return os.getenv("HF_TOKEN")

def validate_env_config(project_root: Optional[Path] = None) -> bool:
    """
    Validate that required environment variables are set.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        True if validation passes.
        
    Raises:
        EnvConfigError: If required variables are missing.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    # Check for required variables
    required_vars = ["HF_TOKEN"]
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        raise EnvConfigError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please update your .env file or set them in your CI environment."
        )
    
    logger.info("Environment configuration validated successfully.")
    return True

def create_env_template(project_root: Optional[Path] = None) -> Path:
    """
    Create a .env.example template file.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        Path to the created template file.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    template_path = project_root / ".env.example"
    content = """# Hugging Face API Token
# Required for downloading datasets and models (e.g., jfiedler/politeness-bert)
# Get your token at: https://huggingface.co/settings/tokens
# 
# SECURITY NOTE:
# This file is a template for local development only.
# DO NOT commit actual secrets to version control.
# In CI/CD (GitHub Actions), inject this value via repository secrets/environment variables.
HF_TOKEN=
"""
    
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Created environment template: {template_path}")
    return template_path

def ensure_env_file_exists(project_root: Optional[Path] = None) -> Path:
    """
    Ensure a .env file exists by copying from .env.example if necessary.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        Path to the .env file.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    env_path = project_root / ".env"
    env_example_path = project_root / ".env.example"
    
    if not env_path.exists():
        if env_example_path.exists():
            # Copy template to .env
            content = env_example_path.read_text(encoding="utf-8")
            env_path.write_text(content, encoding="utf-8")
            logger.info(f"Created .env from template: {env_path}")
        else:
            logger.warning(f"No .env.example found to create .env at {env_path}")
    
    return env_path