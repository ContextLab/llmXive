"""
Warning injection utilities for FR007 compliance.

This module provides functions to inject associational analysis warnings
into various output formats (JSON, YAML, text) to ensure proper
scientific communication of results.
"""
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

ASSOCIATIONAL_WARNING_TEXT = (
    "WARNING: This analysis is associational only. "
    "The models identify correlations between composition and hardness but "
    "do not establish causal relationships. Results should be interpreted "
    "with caution and validated through experimental methods."
)

def get_warning_header() -> str:
    """Return a formatted header for warning messages."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] FR007 COMPLIANCE WARNING"

def inject_warning_into_json_output(data: Dict[str, Any], warning_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Inject a warning into a JSON-compatible dictionary.
    
    Args:
        data: The output dictionary.
        warning_text: Optional custom warning text. Defaults to standard warning.
        
    Returns:
        The modified dictionary with warning injected.
    """
    warning = warning_text or ASSOCIATIONAL_WARNING_TEXT
    data['warning'] = warning
    data['warning_type'] = 'associational_analysis'
    data['warning_timestamp'] = datetime.now().isoformat()
    logger.info("Injected associational warning into JSON output")
    return data

def inject_warning_into_yaml_output(data: Dict[str, Any], warning_text: Optional[str] = None) -> str:
    """
    Inject a warning into YAML output and return as string.
    
    Args:
        data: The output dictionary.
        warning_text: Optional custom warning text.
        
    Returns:
        YAML string with warning injected.
    """
    warning = warning_text or ASSOCIATIONAL_WARNING_TEXT
    data['warning'] = warning
    data['warning_type'] = 'associational_analysis'
    data['warning_timestamp'] = datetime.now().isoformat()
    logger.info("Injected associational warning into YAML output")
    return yaml.dump(data, default_flow_style=False, sort_keys=False)

def add_warning_to_text_file(file_path: str, warning_text: Optional[str] = None) -> None:
    """
    Append a warning to a text file.
    
    Args:
        file_path: Path to the text file.
        warning_text: Optional custom warning text.
    """
    warning = warning_text or ASSOCIATIONAL_WARNING_TEXT
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f"\n{get_warning_header()}\n")
        f.write(f"{warning}\n")
        f.write("-" * 80 + "\n")
    
    logger.info(f"Added warning to text file: {file_path}")

def main():
    """Test function for warning injection utilities."""
    logger.info("Testing warning injection utilities...")
    
    # Test JSON injection
    test_data = {"model": "xgboost", "r2": 0.85}
    result = inject_warning_into_json_output(test_data)
    assert 'warning' in result
    logger.info("JSON injection test passed")
    
    # Test YAML injection
    yaml_result = inject_warning_into_yaml_output(test_data)
    assert 'warning' in yaml_result
    logger.info("YAML injection test passed")
    
    # Test text file injection
    test_file = "data/outputs/test_warning.txt"
    add_warning_to_text_file(test_file)
    assert Path(test_file).exists()
    logger.info("Text file injection test passed")
    
    logger.info("All warning injection tests passed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
