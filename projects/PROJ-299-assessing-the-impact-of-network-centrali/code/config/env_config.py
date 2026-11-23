"""
Environment Configuration Management

Loads ADNI credentials from .env.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dotenv.main import DotEnv

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=project_root / ".env")

def load_environment():
    """
    Load environment variables from .env.
    """
    return {
        "ADNI_USER": os.getenv("ADNI_USER"),
        "ADNI_PASS": os.getenv("ADNI_PASS"),
        "ADNI_SUBJECT_LIST": os.getenv("ADNI_SUBJECT_LIST")
    }

def validate_adni_credentials():
    """
    Validate presence of required ADNI credentials.
    """
    config = load_environment()
    missing = []
    for key in ["ADNI_USER", "ADNI_PASS", "ADNI_SUBJECT_LIST"]:
        if not config.get(key):
            missing.append(key)
    
    if missing:
        raise ValueError(f"Missing required ADNI credentials: {', '.join(missing)}")
    
    return True

def get_config():
    """
    Get full configuration.
    """
    return load_environment()

def check_env():
    """
    Check environment status.
    """
    try:
        validate_adni_credentials()
        return True
    except ValueError:
        return False
