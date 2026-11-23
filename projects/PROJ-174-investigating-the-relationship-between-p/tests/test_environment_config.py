import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

def test_missing_env_vars_fail():
    """
    Verify that the pipeline fails gracefully with a clear error message
    when required environment variables are missing.
    """
    # Ensure no .env file exists in the test context
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".env"
        # Create an empty .env file to simulate missing values
        env_file.write_text("")

        # Temporarily set the environment to use this empty .env
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        # Reload the module to pick up the new environment
        import importlib
        import main
        importlib.reload(main)

        try:
            result = main.verify_environment()
            assert result is False, "verify_environment should return False when vars are missing"
        finally:
            os.chdir(old_cwd)
            # Clean up sys.modules to avoid caching issues in subsequent tests
            if 'main' in sys.modules:
                del sys.modules['main']

def test_valid_env_vars_pass():
    """
    Verify that the pipeline passes when all required environment variables are set.
    """
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".env"
        env_file.write_text(
            "DATA_PATH=/tmp\n"
            "OPENNEURO_API_KEY=test_key_123\n"
            "LOG_LEVEL=DEBUG\n"
        )

        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        # Reload the module to pick up the new environment
        import importlib
        import main
        importlib.reload(main)

        try:
            result = main.verify_environment()
            assert result is True, "verify_environment should return True when vars are present"
        finally:
            os.chdir(old_cwd)
            if 'main' in sys.modules:
                del sys.modules['main']

def test_env_file_structure():
    """
    Verify that code/.env.example exists and contains required keys.
    """
    env_example_path = Path(__file__).parent.parent / "code" / ".env.example"
    assert env_example_path.exists(), "code/.env.example must exist"
    
    content = env_example_path.read_text()
    required_keys = ["DATA_PATH", "OPENNEURO_API_KEY", "LOG_LEVEL"]
    
    for key in required_keys:
        assert key in content, f"Required key '{key}' missing from .env.example"