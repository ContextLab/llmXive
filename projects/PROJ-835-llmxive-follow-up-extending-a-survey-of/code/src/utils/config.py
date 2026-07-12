"""
Configuration management for the LLMXive pipeline.

Handles random seed setting, path management, and state file I/O.
"""
import os
import sys
import json
import random
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Project root is assumed to be the parent of 'code' in the artifact path structure
# However, standard practice is to resolve relative to the file location or a known root.
# Given the task description and project structure, we assume the project root is
# the directory containing 'src', 'data', 'tests', etc.
# We will dynamically determine the project root relative to this file's location.
# This file is at: code/src/utils/config.py
# Project root is: code/ (relative to this file: ../../)
# But the artifact paths in the prompt suggest 'code/' is the root of the project tree for artifacts.
# Let's assume the working directory when running is the project root.
# If running from 'code/', we need to adjust.
# To be safe and consistent with "Stay inside the project tree", we will assume
# the project root is the directory where 'src', 'data', 'tests' exist.
# We will infer it from the current file's path if needed, or use a constant.
# For robustness, let's define the base path relative to this module.

_MODULE_DIR = Path(__file__).resolve().parent
# This file is in code/src/utils/
# Project root (containing src, data, tests) is code/
_PROJECT_ROOT = _MODULE_DIR.parent.parent

# Ensure the project root exists in the file system (for path resolution)
# If running in a context where 'code' is not the root, this might need adjustment.
# But based on artifact paths like "code/src/utils/config.py", "code/data/...",
# it seems the "code" directory IS the project root for the purpose of this task.
# Let's verify the structure assumption:
# code/
#   src/
#     utils/
#       config.py
#   data/
#   tests/
#   state/
#   ...

# We will use _PROJECT_ROOT as the base for all relative paths.
# If the script is run from a different directory, we rely on the assumption
# that the working directory is the project root, or we use absolute paths based on this file.
# Using absolute paths based on this file is safer for a library module.

def set_random_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across numpy, random, and torch (if available).
    
    Args:
        seed: The integer seed to use.
    """
    random.seed(seed)
    # Attempt to set numpy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    # Attempt to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_path(relative_path: Union[str, Path]) -> Path:
    """
    Resolve a relative path to an absolute path within the project root.
    
    Args:
        relative_path: Path relative to the project root.
        
    Returns:
        Absolute Path object.
    """
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return _PROJECT_ROOT / path

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory.
        
    Returns:
        The Path object of the directory.
    """
    dir_path = get_path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def load_state(state_file: Union[str, Path, None] = None) -> Dict[str, Any]:
    """
    Load the project state from a YAML or JSON file.
    
    Args:
        state_file: Path to the state file. If None, uses the default project state file.
        
    Returns:
        Dictionary containing the state.
    """
    if state_file is None:
        # Default state file path based on task T006
        state_file = "state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml"
    
    state_path = get_path(state_file)
    
    if not state_path.exists():
        return {
            "project_id": "PROJ-835-llmxive-follow-up-extending-a-survey-of",
            "artifact_hashes": {}
        }
    
    try:
        # Try to load as JSON first
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        pass
    
    # If JSON fails, try YAML (requires PyYAML)
    try:
        import yaml
        with open(state_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        raise ImportError("PyYAML is required to load YAML state files. Install it via pip install pyyaml.")
    except yaml.YAMLError:
        raise ValueError(f"Failed to parse state file {state_path} as YAML or JSON.")

def save_state(state: Dict[str, Any], state_file: Union[str, Path, None] = None) -> Path:
    """
    Save the project state to a YAML file.
    
    Args:
        state: The state dictionary to save.
        state_file: Path to the state file. If None, uses the default.
        
    Returns:
        The Path object of the saved file.
    """
    if state_file is None:
        state_file = "state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml"
    
    state_path = get_path(state_file)
    ensure_dir(state_path.parent)
    
    try:
        import yaml
        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to JSON if YAML is not available
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    
    return state_path

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    path = get_path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_artifact_hash(state: Dict[str, Any], artifact_name: str, file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Update the artifact hash in the state dictionary.
    
    Args:
        state: The state dictionary to update.
        artifact_name: The name/key for the artifact.
        file_path: Path to the artifact file.
        
    Returns:
        The updated state dictionary.
    """
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    state["artifact_hashes"][artifact_name] = compute_file_hash(file_path)
    return state

def get_artifact_hash(state: Dict[str, Any], artifact_name: str) -> Optional[str]:
    """
    Retrieve the hash for a specific artifact from the state.
    
    Args:
        state: The state dictionary.
        artifact_name: The name/key for the artifact.
        
    Returns:
        The hash string or None if not found.
    """
    return state.get("artifact_hashes", {}).get(artifact_name)

def validate_state_integrity(state: Dict[str, Any]) -> bool:
    """
    Validate the basic integrity of the state dictionary.
    
    Args:
        state: The state dictionary to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(state, dict):
        return False
    if "artifact_hashes" not in state:
        return False
    if not isinstance(state["artifact_hashes"], dict):
        return False
    return True