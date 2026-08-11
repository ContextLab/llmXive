"""
FR-007 Warning Injection Utilities.
Ensures associational framing warnings are injected into outputs.
"""
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.logging_config import get_logger

logger = get_logger(__name__)

ASSOCIATIONAL_WARNING_TEXT = (
    "NOTE: Results are associational, not causal. "
    "Correlations observed in this analysis do not imply causation."
)

def get_warning_header() -> str:
    """Returns the standard warning header string."""
    return ASSOCIATIONAL_WARNING_TEXT

def inject_warning_into_json_output(data: Dict[str, Any], warning_key: str = "associational_warning") -> Dict[str, Any]:
    """
    Injects the associational warning into a JSON-compatible dictionary.
    
    Args:
        data: The dictionary to inject the warning into.
        warning_key: The key name for the warning.
    
    Returns:
        The modified dictionary with the warning injected.
    """
    if not isinstance(data, dict):
        raise TypeError("Data must be a dictionary for JSON injection.")
    
    data[warning_key] = {
        "text": ASSOCIATIONAL_WARNING_TEXT,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "associational_framing"
    }
    logger.info(f"Injected associational warning into JSON output.")
    return data

def inject_warning_into_yaml_output(data: Dict[str, Any], warning_key: str = "associational_warning") -> Dict[str, Any]:
    """
    Injects the associational warning into a YAML-compatible dictionary.
    
    Args:
        data: The dictionary to inject the warning into.
        warning_key: The key name for the warning.
    
    Returns:
        The modified dictionary with the warning injected.
    """
    if not isinstance(data, dict):
        raise TypeError("Data must be a dictionary for YAML injection.")
    
    data[warning_key] = {
        "text": ASSOCIATIONAL_WARNING_TEXT,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "associational_framing"
    }
    logger.info(f"Injected associational warning into YAML output.")
    return data

def add_warning_to_text_file(file_path: Path, warning_text: Optional[str] = None) -> None:
    """
    Appends the associational warning to the end of a text file.
    
    Args:
        file_path: Path to the text file.
        warning_text: Optional custom warning text. Defaults to standard warning.
    """
    if warning_text is None:
        warning_text = ASSOCIATIONAL_WARNING_TEXT
    
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write("\n\n" + warning_text + "\n")
        logger.info(f"Appended warning to text file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to append warning to {file_path}: {e}")
        raise

def main():
    """Simple test runner to verify warning injection logic."""
    logger.info("Running FR-007 Warning Injection tests...")
    
    # Test JSON injection
    test_data = {"model": "XGBoost", "r2": 0.85}
    injected_json = inject_warning_into_json_output(test_data)
    assert "associational_warning" in injected_json
    assert injected_json["associational_warning"]["text"] == ASSOCIATIONAL_WARNING_TEXT
    
    # Test YAML injection
    test_yaml = {"model": "Linear", "rmse": 5.2}
    injected_yaml = inject_warning_into_yaml_output(test_yaml)
    assert "associational_warning" in injected_yaml
    
    # Test text file
    test_file = Path("data/processed/test_warning.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Initial content")
    add_warning_to_text_file(test_file)
    content = test_file.read_text()
    assert ASSOCIATIONAL_WARNING_TEXT in content
    
    logger.info("All FR-007 warning injection tests passed.")
    return True
