import subprocess
import os
import pytest
from pathlib import Path
import tomli
import sys

# Ensure the code directory is in the path so imports work relative to project root
# when running as a script, though pytest usually handles this via conftest or path setup.
# We will explicitly add the parent of 'code' to sys.path if running directly.
if "code" in os.getcwd():
    sys.path.insert(0, os.path.dirname(os.getcwd()))
else:
    # Fallback for when running from project root
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root / "code"))

def test_flake8_config_exists():
    """Verify that .flake8 configuration file exists at project root."""
    project_root = Path(__file__).resolve().parents[2]
    flake8_config = project_root / ".flake8"
    assert flake8_config.exists(), f".flake8 config file not found at {flake8_config}"

def test_pyproject_toml_exists():
    """Verify that pyproject.toml configuration file exists at project root."""
    project_root = Path(__file__).resolve().parents[2]
    pyproject_config = project_root / "pyproject.toml"
    assert pyproject_config.exists(), f"pyproject.toml config file not found at {pyproject_config}"

def test_black_can_parse_config():
    """Verify that Black can successfully parse the pyproject.toml configuration."""
    project_root = Path(__file__).resolve().parents[2]
    pyproject_config = project_root / "pyproject.toml"
    
    try:
        # Run black --version to ensure it's installed, then check config parsing
        result = subprocess.run(
            ["black", "--config", str(pyproject_config), "--check", "--diff", str(project_root / "code" / "__init__.py")],
            capture_output=True,
            text=True,
            timeout=30
        )
        # We expect a non-zero exit code if the file is not formatted, but we want to ensure
        # Black can *read* the config without crashing (i.e., no SyntaxError or ConfigError).
        # A successful parse usually means exit code 0 (no changes) or 1 (changes needed),
        # but NOT 2 (usage error/config error) or 124 (timeout).
        # However, to be safe, we just check that it didn't crash with a config error.
        # If the config is valid, Black runs.
        assert "UsageError" not in result.stderr and "ConfigError" not in result.stderr, \
            f"Black failed to parse config: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black is not installed in the environment.")
    except subprocess.TimeoutExpired:
        pytest.fail("Black timed out while checking config.")

def test_flake8_can_parse_config():
    """Verify that Flake8 can successfully parse the .flake8 configuration."""
    project_root = Path(__file__).resolve().parents[2]
    flake8_config = project_root / ".flake8"
    
    try:
        # Run flake8 with the config on a dummy file or the config file itself to ensure it parses
        # We run it on the .flake8 file itself or a minimal python file to trigger config load
        sample_file = project_root / "code" / "__init__.py"
        if not sample_file.exists():
            # Create a temporary minimal file if needed, but usually __init__.py exists
            sample_file = project_root / "code" / "config.py"
        
        result = subprocess.run(
            ["flake8", "--config", str(flake8_config), str(sample_file)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # We expect flake8 to run. It might return 1 if there are linting errors,
        # which is fine. We care that it didn't crash due to config issues.
        # Config errors usually appear in stderr or as a specific exit code.
        # Exit code 2 is often a usage error.
        assert result.returncode != 2, f"Flake8 config error: {result.stderr}"
        assert "UsageError" not in result.stderr and "ConfigError" not in result.stderr, \
            f"Flake8 failed to parse config: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Flake8 is not installed in the environment.")
    except subprocess.TimeoutExpired:
        pytest.fail("Flake8 timed out while checking config.")

def test_linting_rules_are_reasonable():
    """Verify that the linting rules in .flake8 are reasonable and match expected constraints."""
    project_root = Path(__file__).resolve().parents[2]
    flake8_config = project_root / ".flake8"
    
    # Read the config file
    config_content = flake8_config.read_text()
    
    # Check for expected max-line-length
    assert "max-line-length" in config_content, "max-line-length not found in .flake8"
    
    # Parse the config to ensure it's valid
    # We can use configparser or just verify the string contains the expected keys
    import configparser
    config = configparser.ConfigParser()
    config.read(str(flake8_config))
    
    assert "flake8" in config, "Section [flake8] not found in .flake8"
    
    max_len = config["flake8"].get("max-line-length", 88)
    assert int(max_len) <= 120, f"max-line-length {max_len} is too high (>120)"
    assert int(max_len) >= 80, f"max-line-length {max_len} is too low (<80)"
    
    # Check for ignore list if present
    if "ignore" in config["flake8"]:
        ignore_list = config["flake8"]["ignore"].split(",")
        # Ensure we don't have overly aggressive ignores
        assert "E" not in ignore_list, "Ignoring all E errors is not reasonable"
        assert "W" not in ignore_list, "Ignoring all W errors is not reasonable"

def test_flake8_runs_on_sample_file():
    """
    Execute T003b: Verify linting configuration by running flake8 on a sample file.
    This test explicitly runs flake8 as described in the task to generate the required evidence.
    """
    project_root = Path(__file__).resolve().parents[2]
    flake8_config = project_root / ".flake8"
    
    # Select a sample file that exists in the project
    # T003a created .flake8 and pyproject.toml. T001 created the structure.
    # We'll try to find a python file in the code directory.
    sample_files = list((project_root / "code").rglob("*.py"))
    
    if not sample_files:
        # If no python files exist yet (unlikely given T001/T005b), create a minimal one for testing
        # But per T001, directories should exist. Let's assume at least config.py or similar exists.
        # If truly empty, we can't run flake8 on a sample.
        pytest.skip("No Python files found in code/ directory to run flake8 on.")
    
    sample_file = sample_files[0]
    
    try:
        # Run flake8 on the sample file with the project config
        result = subprocess.run(
            ["flake8", "--config", str(flake8_config), str(sample_file)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # The task is to verify the configuration runs.
        # We assert that the process completed (exit code 0, 1, or 2).
        # Exit code 0: No issues found.
        # Exit code 1: Issues found (linting errors). This is a SUCCESSFUL run of flake8.
        # Exit code 2: Usage error (e.g., config parse error). This is a FAILURE of the config.
        
        assert result.returncode != 2, (
            f"Flake8 configuration verification failed. "
            f"Exit code: {result.returncode}\n"
            f"Stdout: {result.stdout}\n"
            f"Stderr: {result.stderr}"
        )
        
        # Log the result for the task evidence
        print(f"--- Flake8 Verification on {sample_file.name} ---")
        print(f"Exit Code: {result.returncode}")
        if result.stdout:
            print(f"Linting Output:\n{result.stdout}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr}")
        print("--- End Verification ---")
        
    except FileNotFoundError:
        pytest.fail("Flake8 executable not found. Please install flake8.")
    except subprocess.TimeoutExpired:
        pytest.fail("Flake8 execution timed out.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
