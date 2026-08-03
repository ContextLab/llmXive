import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file if present
# This must happen at import time to ensure env vars are available
load_dotenv()

# --- Environment Configuration Management ---

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root.
    Defaults to the directory containing this config file if PROJECT_ROOT is not set.
    """
    env_root = os.getenv("PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    # Fallback: assume project root is the parent of the 'code' directory
    return Path(__file__).resolve().parent.parent

def get_model_path() -> Path:
    """
    Returns the path to the model directory.
    Uses MODEL_DIR env var if set, otherwise defaults to 'models' under project root.
    """
    env_model_dir = os.getenv("MODEL_DIR")
    if env_model_dir:
        return Path(env_model_dir).resolve()
    return get_project_root() / "models"

def get_arm_config() -> Dict[str, Any]:
    """
    Returns a dictionary containing the active arm configuration.
    Reads ARM_TYPE and related settings from environment variables.
    Falls back to defaults defined in the task requirements (Arm B as primary).
    """
    arm_type = os.getenv("ARM_TYPE", "B").upper()
    max_tokens = int(os.getenv("MAX_TOKENS", "4096"))
    seed = int(os.getenv("SEED", "42"))
    
    # Model ID from task T005 requirements
    model_id = os.getenv("MODEL_ID", "mmpro/MMProLong-7B-1.0")
    
    return {
        "arm_type": arm_type,
        "max_tokens": max_tokens,
        "seed": seed,
        "model_id": model_id,
        # Explicitly set primary arm as per T005 requirement
        "arm_primary": "B" if arm_type == "B" else "A"
    }

def validate_config() -> bool:
    """
    Validates that critical configuration values are present and sane.
    Returns True if valid, raises ValueError if invalid.
    """
    config = get_arm_config()
    
    if config["arm_type"] not in ["A", "B"]:
        raise ValueError(f"Invalid ARM_TYPE '{config['arm_type']}'. Must be 'A' or 'B'.")
    
    if config["max_tokens"] <= 0:
        raise ValueError(f"Invalid MAX_TOKENS '{config['max_tokens']}'. Must be positive.")
    
    # Check if model path exists if specified via env
    model_dir = get_model_path()
    if not model_dir.exists():
        # Log warning but don't fail validation if just missing (T040 handles download)
        # However, for config validation, we just ensure the path object is valid
        pass

    return True

# Expose the loaded environment for debugging if needed
def get_environment() -> Dict[str, str]:
    """
    Returns a dictionary of all loaded environment variables relevant to the project.
    """
    return {
        "PROJECT_ROOT": os.getenv("PROJECT_ROOT", "default"),
        "MODEL_DIR": os.getenv("MODEL_DIR", "default"),
        "ARM_TYPE": os.getenv("ARM_TYPE", "default"),
        "MAX_TOKENS": os.getenv("MAX_TOKENS", "default"),
        "MODEL_ID": os.getenv("MODEL_ID", "default"),
        "SEED": os.getenv("SEED", "default"),
    }
