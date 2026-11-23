"""
Utility functions for JSON file operations in the parser module.
"""
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def load_json_file(path: str) -> Dict[str, Any]:
    """
    Load a JSON file.
    
    Args:
        path: Path to the JSON file.
        
    Returns:
        Parsed JSON content as a dictionary.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        raise

def save_json_file(data: Dict[str, Any], path: str) -> None:
    """
    Save a dictionary to a JSON file.
    
    Args:
        data: Dictionary to save.
        path: Path to the output file.
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON to {path}")
    except Exception as e:
        logger.error(f"Failed to save JSON to {path}: {e}")
        raise
