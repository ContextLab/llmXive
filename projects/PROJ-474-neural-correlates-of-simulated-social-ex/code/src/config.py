"""
Configuration loader for the project.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """
    Load configuration from code/config.yaml.
    """
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        # Fallback to defaults if config.yaml is missing during early dev
        return {
            "paths": {
                "data_raw": str(Path(__file__).parent.parent / "data" / "raw"),
                "data_processed": str(Path(__file__).parent.parent / "data" / "processed"),
                "data_results": str(Path(__file__).parent.parent / "data" / "results"),
            },
            "qc": {
                "motion_threshold_mm": 3.0,
                "min_subjects": 10
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
