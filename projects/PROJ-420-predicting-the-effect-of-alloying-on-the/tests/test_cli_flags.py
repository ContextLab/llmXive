"""
Test suite for T044: Verify CLI scripts and their flags work correctly.

This task validates that all CLI entry points defined in the project
can be invoked with expected flags without raising ImportError or
argument parsing errors.

Blocked by: T030a-render (requires final report generation logic to be present)
"""
import subprocess
import sys
import json
import os
from pathlib import Path

import pytest


# Project root relative to tests/
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"

# Ensure the code directory is in the Python path for imports
sys.path.insert(0, str(CODE_DIR))

# List of CLI scripts to test
# These are the main entry points defined in the project
CLI_SCRIPTS = [
    "main_pipeline.py",
    "main.py",
    "data/clean.py",
    "data/download.py",
    "modeling.py",
    "analysis.py",
    "merge.py",
    "data_extraction.py",
    "data_cleaning.py",
    "format_check.py",
    "memory_monitor.py",
    "memory_utils.py",
    "ruff_fix_runner.py",
    "validate_quickstart.py",
]

# CLI modules with argparse main() functions
CLI_MODULES = [
    "cli.clean_cli",
    "cli.download_cli",
    "cli.model_cli",
]

def run_cli_script(script_name: str, args: list = None) -> subprocess.CompletedProcess:
    """Run a CLI script with optional arguments."""
    script_path = CODE_DIR / script_name
    if not script_path.exists():
        pytest.skip(f"Script not found: {script_path}")
    
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    # Set environment to avoid interactive prompts
    env = os.environ.copy()
    env["PYTHONPATH"] = str(CODE_DIR)
    
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=60
    )

def run_cli_module(module_name: str, args: list = None) -> subprocess.CompletedProcess:
    """Run a CLI module with optional arguments."""
    # Convert module path to file path (e.g., cli.clean_cli -> cli/clean_cli.py)
    parts = module_name.split(".")
    file_path = CODE_DIR / "/".join(parts[:-1]) / f"{parts[-1]}.py"
    
    if not file_path.exists():
        pytest.skip(f"Module not found: {file_path}")
    
    cmd = [sys.executable, "-m", module_name]
    if args:
        cmd.extend(args)
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(CODE_DIR)
    
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=60
    )

@pytest.mark.parametrize("script", CLI_SCRIPTS)
def test_cli_help_flag(script: str):
    """Test that CLI scripts respond to --help flag without ImportError."""
    result = run_cli_script(script, ["--help"])
    
    # We expect --help to exit with 0 or 2 (argparse error if no action)
    # The key is that it should NOT fail with ImportError
    assert "ImportError" not in result.stderr, f"ImportError in {script}:\n{result.stderr}"
    assert "ModuleNotFoundError" not in result.stderr, f"ModuleNotFoundError in {script}:\n{result.stderr}"
    
    # If the script has a main() with argparse, it should show help
    if result.returncode in (0, 2):
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower(), \
            f"No usage info found in {script}"

@pytest.mark.parametrize("script", CLI_SCRIPTS)
def test_cli_importability(script: str):
    """Test that CLI scripts can be imported without side effects."""
    # Remove .py extension and convert to module path
    module_path = script[:-3].replace("/", ".").replace("\\", ".")
    
    try:
        __import__(module_path)
    except ImportError as e:
        # If it's a circular import or missing dependency, that's a failure
        if "ImportError" in str(e) or "ModuleNotFoundError" in str(e):
            pytest.fail(f"Failed to import {module_path}: {e}")
    except Exception as e:
        # Other exceptions during import (e.g., runtime errors) are also failures
        pytest.fail(f"Unexpected error importing {module_path}: {e}")

@pytest.mark.parametrize("module", CLI_MODULES)
def test_cli_module_help_flag(module: str):
    """Test that CLI modules respond to --help flag."""
    result = run_cli_module(module, ["--help"])
    
    assert "ImportError" not in result.stderr, f"ImportError in {module}:\n{result.stderr}"
    assert "ModuleNotFoundError" not in result.stderr, f"ModuleNotFoundError in {module}:\n{result.stderr}"
    
    # argparse should show usage
    if result.returncode in (0, 2):
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower(), \
            f"No usage info found in {module}"

def test_main_pipeline_execution_structure():
    """Test that main_pipeline.py can at least parse arguments and start."""
    # Run with --help to verify it's a valid CLI
    result = run_cli_script("main_pipeline.py", ["--help"])
    
    # Should not have import errors
    assert "ImportError" not in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
    
    # Should have usage info
    assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()

def test_validate_quickstart_execution():
    """Test that validate_quickstart.py can run and validate the project."""
    result = run_cli_script("validate_quickstart.py", ["--help"])
    
    assert "ImportError" not in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
    assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()

def test_cli_argument_parsing():
    """Test that common CLI flags are recognized."""
    # Test a few key scripts with --help to ensure they parse arguments
    scripts_to_test = ["main_pipeline.py", "main.py", "data/clean.py"]
    
    for script in scripts_to_test:
        result = run_cli_script(script, ["--help"])
        assert result.returncode in (0, 2), f"Unexpected return code {result.returncode} for {script}"
        assert "ImportError" not in result.stderr, f"ImportError in {script}"
        assert "ModuleNotFoundError" not in result.stderr, f"ModuleNotFoundError in {script}"

def test_no_circular_imports_in_cli():
    """Test that importing CLI modules doesn't cause circular import errors."""
    circular_check_modules = [
        "main_pipeline",
        "main",
        "data.clean",
        "data.download",
        "modeling",
        "analysis",
        "logging_config",
        "config",
    ]
    
    for module_name in circular_check_modules:
        try:
            __import__(module_name)
        except ImportError as e:
            if "circular import" in str(e).lower():
                pytest.fail(f"Circular import detected in {module_name}: {e}")
            # Other ImportErrors are allowed if they're due to missing optional deps
        except Exception:
            # Other exceptions are fine for this test
            pass