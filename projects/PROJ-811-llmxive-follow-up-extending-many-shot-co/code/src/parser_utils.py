"""
Utility functions for parsing and data handling.
"""
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> Dict:
    """Loads a JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {filepath}")
        return {}

def save_json_file(filepath: str, data: Dict):
    """Saves data to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
