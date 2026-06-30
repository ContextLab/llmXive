"""
Base configuration management for model lists, dataset paths, and sample limits.
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

# Project root relative to this file (code/)
_ROOT = Path(__file__).resolve().parent.parent

# Default paths
DEFAULT_MODEL_LIST_PATH = "data/model_cards/model_list.yaml"
DEFAULT_DATASET_PATHS = {
    "librispeech": "data/raw/librispeech/dev-clean.json",
    "fma_small": "data/raw/fma_small/metadata.json",
    "esc50": "data/raw/esc50/esc50.json",
}
DEFAULT_SAMPLE_LIMITS = {
    "speech": 50,
    "music": 50,
    "env": 50,
}

# Default model exclusion keywords (for T014)
DEFAULT_EXCLUSION_KEYWORDS = [
    "esc-50",
    "musicbench",
    "audiobench",
    "librispeech",
]

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    Falls back to defaults if the file does not exist or is empty.
    
    Args:
        config_path: Path to the config file relative to project root.
                    If None, uses default location.
    
    Returns:
        Dictionary containing the configuration.
    """
    if config_path is None:
        config_path = DEFAULT_MODEL_LIST_PATH
    
    full_path = _ROOT / config_path
    
    # Initialize with defaults
    config = {
        "model_list_path": str(full_path),
        "dataset_paths": DEFAULT_DATASET_PATHS,
        "sample_limits": DEFAULT_SAMPLE_LIMITS,
        "exclusion_keywords": DEFAULT_EXCLUSION_KEYWORDS,
        "max_audio_duration_seconds": 10,
        "audio_sample_rate": 16000,
        "batch_size": 1,
    }
    
    if full_path.exists():
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    # Merge loaded config with defaults
                    for key, value in loaded.items():
                        if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                            config[key].update(value)
                        else:
                            config[key] = value
        except Exception as e:
            # Log warning but continue with defaults if config is malformed
            print(f"Warning: Could not load config from {full_path}: {e}. Using defaults.")
    
    return config

def get_model_list_path(config: Optional[Dict[str, Any]] = None) -> str:
    """Get the absolute path to the model list file."""
    if config is None:
        config = load_config()
    return str(_ROOT / config.get("model_list_path", DEFAULT_MODEL_LIST_PATH))

def get_dataset_paths(config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Get the mapping of domain names to dataset file paths."""
    if config is None:
        config = load_config()
    paths = config.get("dataset_paths", DEFAULT_DATASET_PATHS)
    # Convert to absolute paths
    return {k: str(_ROOT / v) for k, v in paths.items()}

def get_sample_limits(config: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """Get the sample limits per domain."""
    if config is None:
        config = load_config()
    return config.get("sample_limits", DEFAULT_SAMPLE_LIMITS)

def get_exclusion_keywords(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """Get the list of keywords for model exclusion."""
    if config is None:
        config = load_config()
    return config.get("exclusion_keywords", DEFAULT_EXCLUSION_KEYWORDS)

def get_audio_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get audio processing configuration (sample rate, max duration)."""
    if config is None:
        config = load_config()
    return {
        "sample_rate": config.get("audio_sample_rate", 16000),
        "max_duration": config.get("max_audio_duration_seconds", 10),
    }

def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> str:
    """
    Save the configuration to a YAML file.
    
    Args:
        config: The configuration dictionary to save.
        config_path: Path to save the config file relative to project root.
    
    Returns:
        The absolute path of the saved file.
    """
    if config_path is None:
        config_path = "config.yaml"
    
    full_path = _ROOT / config_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(full_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    return str(full_path)

def get_default_model_list() -> List[Dict[str, Any]]:
    """
    Return a default list of model configurations if the model list file doesn't exist.
    This is used for testing or initial setup.
    """
    return [
        {"name": "mock_model_1", "type": "audio-language", "domain": "general"},
        {"name": "mock_model_2", "type": "audio-language", "domain": "speech"},
    ]