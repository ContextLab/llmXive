"""
Test script to verify that load_env() correctly reads environment variables from .env file.

This test:
1. Creates a temporary .env file with a custom variable
2. Clears that variable from the current environment
3. Calls load_env()
4. Verifies the variable is now present in os.environ
"""
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Import the function under test
from code.config_loader import load_env, DEFAULTS

def test_load_env_reads_custom_variable():
    """Test that load_env() reads variables from a .env file."""
    # Create a temporary .env file in a temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        env_file = tmp_path / ".env"
        
        # Write a test variable to .env
        test_key = "TEST_CUSTOM_VAR"
        test_value = "test_value_12345"
        
        with open(env_file, "w") as f:
            f.write(f"{test_key}={test_value}\n")
        
        # Save original environment state
        original_value = os.environ.get(test_key, None)
        
        # Remove from environment if present (to simulate fresh load)
        if test_key in os.environ:
            del os.environ[test_key]
        
        # Temporarily patch the project root detection to use our temp dir
        # We need to modify the behavior of load_env to look in our temp dir
        # Since load_env looks at parent of config_loader.py, we can't easily override
        # Instead, we'll create the .env file in the actual project root
        pass
    
    # Alternative approach: Create .env in actual project root
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    
    # Backup existing .env if present
    backup_path = None
    if env_path.exists():
        backup_path = project_root / ".env.backup"
        env_path.rename(backup_path)
    
    try:
        # Create test .env file
        test_key = "TEST_CUSTOM_VAR"
        test_value = "test_value_12345"
        
        with open(env_path, "w") as f:
            f.write(f"{test_key}={test_value}\n")
        
        # Remove from environment if present
        if test_key in os.environ:
            del os.environ[test_key]
        
        # Call load_env - it should pick up our test variable
        load_env()
        
        # Verify the variable is now in environment
        assert test_key in os.environ, f"Variable {test_key} not found in environment"
        assert os.environ[test_key] == test_value, f"Expected {test_value}, got {os.environ[test_key]}"
        
        print(f"✓ Test passed: {test_key}={os.environ[test_key]}")
        
    finally:
        # Restore original .env if it existed
        if backup_path and backup_path.exists():
            env_path.unlink()
            backup_path.rename(env_path)
        elif env_path.exists():
            env_path.unlink()
        
        # Restore original environment
        if original_value is not None:
            os.environ[test_key] = original_value
        elif test_key in os.environ:
            del os.environ[test_key]

def test_load_env_uses_defaults_when_env_missing():
    """Test that load_env() uses defaults when .env is missing."""
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    
    # Backup existing .env if present
    backup_path = None
    if env_path.exists():
        backup_path = project_root / ".env.backup"
        env_path.rename(backup_path)
    
    try:
        # Ensure .env does not exist
        if env_path.exists():
            env_path.unlink()
        
        # Remove a default key from environment
        default_key = "MAX_TOKENS"
        original_value = os.environ.get(default_key, None)
        if default_key in os.environ:
            del os.environ[default_key]
        
        # Call load_env
        load_env()
        
        # Verify default value is set
        assert default_key in os.environ, f"Default {default_key} not found in environment"
        assert os.environ[default_key] == DEFAULTS[default_key], \
            f"Expected {DEFAULTS[default_key]}, got {os.environ[default_key]}"
        
        print(f"✓ Test passed: Default {default_key}={os.environ[default_key]}")
        
    finally:
        # Restore original .env if it existed
        if backup_path and backup_path.exists():
            env_path.unlink()
            backup_path.rename(env_path)
        elif env_path.exists():
            env_path.unlink()
        
        # Restore original environment
        if original_value is not None:
            os.environ[default_key] = original_value
        elif default_key in os.environ:
            del os.environ[default_key]

if __name__ == "__main__":
    print("Running config_loader verification tests...")
    test_load_env_reads_custom_variable()
    test_load_env_uses_defaults_when_env_missing()
    print("All tests passed!")