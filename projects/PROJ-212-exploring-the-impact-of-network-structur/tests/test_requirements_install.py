"""
Simple test that ensures the requirements installation script produced a SUCCESS log.
The existence and content of the log file serve as evidence that `pip install -r
requirements.txt` completed without errors.
"""
import pathlib

from llmxive_toolkit import paths

def test_requirements_install_log_exists():
    log_path = paths.results("requirements_install_log.txt")
    assert log_path.is_file(), f"Log file not found: {log_path}"
    content = log_path.read_text()
    assert "SUCCESS" in content, f"Installation did not succeed: {content}"