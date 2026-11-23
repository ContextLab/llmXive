"""
Pytest configuration and shared fixtures for the llmXive project.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add the code directory to the path so imports work correctly
# This ensures that 'from config.loader import ...' works in tests
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

@pytest.fixture
def temp_project_root(tmp_path):
    """
    Creates a temporary directory structure mimicking the project root
    for isolated tests that need file I/O.
    """
    # Create standard directories
    (tmp_path / "data" / "raw" / "humaneval").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "code").mkdir(parents=True, exist_ok=True)
    
    # Create a minimal config file for testing
    config_file = tmp_path / "config" / "analysis.yaml"
    config_file.write_text(
        "seed: 42\n"
        "threshold_alpha: 0.05\n"
        "batch_size_start: 50\n"
        "timeout_minutes: 5\n"
    )

    # Return the path object
    return tmp_path

@pytest.fixture
def sample_code_snippet():
    """
    Returns a simple valid Python code snippet for AST testing.
    """
    return """
def add(a, b):
    return a + b

result = add(1, 2)
"""

@pytest.fixture
def sample_invalid_code_snippet():
    """
    Returns an invalid Python code snippet for error handling testing.
    """
    return """
def broken(
    return 1
"""