import os
import subprocess
import sys
from pathlib import Path

def test_venv_script_exists():
    """Verify that the setup script exists."""
    script_path = Path(__file__).parent.parent / "code" / "setup_venv.py"
    assert script_path.exists(), f"Script {script_path} does not exist"

def test_requirements_file_exists():
    """Verify that requirements.txt exists."""
    req_path = Path(__file__).parent.parent / "code" / "requirements.txt"
    assert req_path.exists(), f"Requirements file {req_path} does not exist"

def test_venv_creation_logic():
    """
    This test validates the logic of the setup script by checking
    if it can be imported and the main function is callable.
    It does not run the full install to avoid side effects in test environment.
    """
    # Add code directory to path to simulate execution context
    code_dir = Path(__file__).parent.parent / "code"
    sys.path.insert(0, str(code_dir))
    
    try:
        import setup_venv
        assert hasattr(setup_venv, 'main'), "setup_venv module must have a 'main' function"
        assert callable(setup_venv.main), "setup_venv.main must be callable"
    finally:
        sys.path.remove(str(code_dir))