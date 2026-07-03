"""
Configuration management for the molecular reactivity project.

Loads settings from `src/modeling/config.yaml`.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "src" / "modeling" / "config.yaml"

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not CONFIG_PATH.exists():
        # Return default config if file doesn't exist (for testing purposes)
        return {
            "reaction_templates": {
                "SN1": "[C:1]([O:2])>>[C:1]+[O:2]-",
                "SN2": "[C:1]([O:2])>>[C:1]=[O:2]",
                "Diels-Alder": "[C:1]=[C:2].[C:3]=[C:4]>>[C:1]1[C:3][C:4][C:2]1"
            }
        }
    
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {CONFIG_PATH}: {e}")
