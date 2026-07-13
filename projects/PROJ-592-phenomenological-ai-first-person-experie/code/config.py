"""
Configuration module for the Phenomenological AI pipeline.
Defines seeds, paths, model IDs, and phenomenological marker dictionaries.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Default configuration
DEFAULT_CONFIG = {
    "seeds": [42, 123, 456],
    "output_dir": "data",
    "model_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
    "gguf_file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    "max_tokens": 512,
    "temperature": 0.7,
    "num_generations": 80,
    # Phenomenological Marker Dictionaries (FR-008, FR-009)
    "markers": {
        "sensory": [
            "see", "hear", "feel", "touch", "taste", "smell", 
            "light", "sound", "warmth", "cold", "pressure", 
            "texture", "color", "noise", "scent"
        ],
        "temporal": [
            "now", "then", "before", "after", "moment", "duration",
            "time", "when", "while", "during", "immediately",
            "suddenly", "gradually", "soon", "later"
        ],
        "intentional": [
            "think", "believe", "desire", "intend", "perceive", 
            "experience", "know", "want", "hope", "fear",
            "remember", "forget", "understand", "realize", "decide"
        ]
    }
}

_CONFIG: Optional[Dict[str, Any]] = None


def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or return default."""
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    
    if config_path and Path(config_path).exists():
        # If a config file is provided, load it (simplified for this task)
        # In a real scenario, this would parse YAML/JSON
        pass
    
    _CONFIG = DEFAULT_CONFIG
    return _CONFIG


def get_marker_dictionaries() -> Dict[str, List[str]]:
    """Return the phenomenological marker dictionaries."""
    config = get_config()
    return config.get("markers", DEFAULT_CONFIG["markers"])


def get_marker_list(marker_type: str) -> List[str]:
    """Return a specific list of markers (sensory, temporal, intentional)."""
    markers = get_marker_dictionaries()
    return markers.get(marker_type, [])


def get_all_markers() -> List[str]:
    """Return all markers flattened into a single list."""
    markers = get_marker_dictionaries()
    all_markers = []
    for category in markers.values():
        all_markers.extend(category)
    return all_markers
