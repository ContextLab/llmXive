"""
FR-007 Associational Framing Warning Utilities.

This module provides utilities to inject mandatory associational warnings
into various output formats (JSON, YAML, text) to comply with FR-007.
"""
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.logging_config import get_logger

# Standard warning text for FR-007 compliance
ASSOCIATIONAL_WARNING_TEXT = (
    "NOTE: Results are associational, not causal. "
    "Correlations observed in this analysis do not imply causation."
)


def get_warning_header() -> str:
    """Return a formatted header for associational warnings."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[FR-007 WARNING] ({timestamp}) {ASSOCIATIONAL_WARNING_TEXT}"


def inject_warning_into_json_output(
    data: Dict[str, Any],
    field_name: str = "warning",
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Inject the FR-007 warning into a JSON-serializable dictionary.
    
    Args:
        data: The dictionary to modify.
        field_name: Key under which to store the warning.
        overwrite: If True, overwrite existing field; else skip if exists.
    
    Returns:
        Modified dictionary.
    """
    logger = get_logger(__name__)
    
    if field_name in data and not overwrite:
        logger.debug(f"Warning field '{field_name}' already exists; skipping.")
        return data
    
    data[field_name] = {
        "code": "FR-007",
        "message": ASSOCIATIONAL_WARNING_TEXT,
        "timestamp": datetime.now().isoformat()
    }
    logger.debug(f"Injected FR-007 warning into '{field_name}'.")
    return data


def inject_warning_into_yaml_output(
    data: Dict[str, Any],
    output_path: Path,
    field_name: str = "warning"
) -> None:
    """
    Inject the FR-007 warning into a YAML file.
    
    Args:
        data: Dictionary to save with warning.
        output_path: Path to the output YAML file.
        field_name: Key under which to store the warning.
    """
    logger = get_logger(__name__)
    
    inject_warning_into_json_output(data, field_name, overwrite=True)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Saved YAML output with FR-007 warning to {output_path}")


def add_warning_to_text_file(
    text_content: str,
    output_path: Path,
    position: str = "top"
) -> None:
    """
    Add the FR-007 warning to a text file.
    
    Args:
        text_content: Original text content.
        output_path: Path to the output file.
        position: Where to insert warning ('top' or 'bottom').
    """
    logger = get_logger(__name__)
    
    warning_header = get_warning_header()
    
    if position == "top":
        final_content = f"{warning_header}\n\n{text_content}"
    else:
        final_content = f"{text_content}\n\n{warning_header}"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    logger.info(f"Saved text output with FR-007 warning to {output_path}")


def main():
    """Run self-tests for FR-007 warning injection."""
    logger = get_logger(__name__)
    logger.info("Running FR-007 warning utility tests...")
    
    # Test JSON injection
    test_data = {"metric": 0.85, "model": "XGBoost"}
    result = inject_warning_into_json_output(test_data)
    assert "warning" in result
    assert result["warning"]["code"] == "FR-007"
    logger.info("JSON injection test passed.")
    
    # Test YAML injection
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    inject_warning_into_yaml_output(test_data, tmp_path)
    assert tmp_path.exists()
    with open(tmp_path, 'r') as f:
        loaded = yaml.safe_load(f)
    assert "warning" in loaded
    logger.info("YAML injection test passed.")
    
    # Cleanup
    tmp_path.unlink()
    
    # Test Text injection
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
        tmp_path = Path(tmp.name)
        tmp.write("Sample report content.")
    
    add_warning_to_text_file("Sample report content.", tmp_path)
    assert tmp_path.exists()
    with open(tmp_path, 'r') as f:
        content = f.read()
    assert ASSOCIATIONAL_WARNING_TEXT in content
    logger.info("Text injection test passed.")
    
    # Cleanup
    tmp_path.unlink()
    
    logger.info("All FR-007 warning utility tests passed.")


if __name__ == "__main__":
    main()