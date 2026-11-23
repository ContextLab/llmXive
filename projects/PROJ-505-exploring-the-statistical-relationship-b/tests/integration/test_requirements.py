import pytest
from pathlib import Path
from llmxive_toolkit import paths

def test_requirements_install_log():
    """The verification script must have produced a success log."""
    log_path = paths.results("requirements_install.log")
    assert log_path.is_file(), f"Log file not found at {log_path}"
    content = log_path.read_text()
    assert "success" in content.lower(), "Installation did not succeed"