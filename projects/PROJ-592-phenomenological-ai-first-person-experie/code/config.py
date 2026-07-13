"""
Configuration module for the Phenomenological AI project.

Provides configuration loading, seeds, paths, model IDs, and
phenomenological marker dictionaries as per FR-008 and FR-009.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration values
DEFAULT_SEEDS = {
    "default": 42,
    "generation": 42,
    "analysis": 42,
    "validation": 42
}

DEFAULT_PATHS = {
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "data_qualitative": "data/qualitative",
    "figures": "figures",
    "prompts": "data/prompts"
}

DEFAULT_MODEL_IDS = {
    "primary": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
    "local_7b": "mistralai/Mistral-7B-v0.1"  # Optional, for local execution only
}

# Phenomenological Marker Dictionaries (FR-008, FR-009)
PHENOMENOLOGICAL_MARKERS = {
    "sensory": [
        "see", "hear", "feel", "touch", "taste", "smell", 
        "light", "sound", "vision", "auditory", "tactile",
        "gustatory", "olfactory", "sight", "noise", "texture"
    ],
    "temporal": [
        "now", "then", "before", "after", "moment", "duration",
        "time", "while", "during", "when", "until", "since",
        "previous", "next", "immediate", "eventually", "suddenly"
    ],
    "intentional": [
        "think", "believe", "desire", "intend", "perceive", "experience",
        "know", "understand", "remember", "forget", "want", "need",
        "hope", "fear", "expect", "assume", "conclude", "decide"
    ]
}

def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file or return defaults.
    
    Args:
        config_path: Path to the configuration file (JSON or Python)
        
    Returns:
        Configuration dictionary
    """
    config = {
        "seeds": DEFAULT_SEEDS.copy(),
        "paths": DEFAULT_PATHS.copy(),
        "model_ids": DEFAULT_MODEL_IDS.copy(),
        "phenomenological_markers": PHENOMENOLOGICAL_MARKERS.copy(),
        "generation": {
            "max_retries": 3,
            "timeout": 60,
            "temperature": 0.7,
            "max_tokens": 512
        },
        "analysis": {
            "nli_model": "cross-encoder/stsb-distilroberta-base",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
        }
    }
    
    if config_path and os.path.exists(config_path):
        try:
            # Try to load as JSON first
            if config_path.endswith('.json'):
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            # Try to load as Python module
            elif config_path.endswith('.py'):
                import importlib.util
                spec = importlib.util.spec_from_file_location("custom_config", config_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Extract known keys from the module
                    if hasattr(module, 'SEEDS'):
                        config['seeds'].update(module.SEEDS)
                    if hasattr(module, 'PATHS'):
                        config['paths'].update(module.PATHS)
                    if hasattr(module, 'MODEL_IDS'):
                        config['model_ids'].update(module.MODEL_IDS)
                    if hasattr(module, 'PHENOMENOLOGICAL_MARKERS'):
                        config['phenomenological_markers'].update(module.PHENOMENOLOGICAL_MARKERS)
        except Exception as e:
            # If loading fails, continue with defaults
            pass
    
    return config

def get_marker_list(marker_type: str) -> list:
    """
    Get the list of markers for a specific type.
    
    Args:
        marker_type: Type of marker ('sensory', 'temporal', 'intentional')
        
    Returns:
        List of marker keywords
    """
    return PHENOMENOLOGICAL_MARKERS.get(marker_type, [])

def get_all_markers() -> Dict[str, list]:
    """
    Get all phenomenological markers.
    
    Returns:
        Dictionary of all marker types and their keywords
    """
    return PHENOMENOLOGICAL_MARKERS.copy()
