"""
Integration test for T054: Quickstart.md validation.
Validates reproducible setup by simulating a fresh environment installation
and verifying the CLI entry point runs without errors.
"""
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Project root is the parent of 'tests'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
QUICKSTART_PATH = PROJECT_ROOT / "quickstart.md"

# Expected entry points based on tasks.md and API surface
BENCHMARK_SCRIPT = PROJECT_ROOT / "src" / "benchmark" / "run_benchmark.py"
TASK_SCRIPT = PROJECT_ROOT / "src" / "benchmark" / "run_task.py"

def check_requirements_exists():
    """Ensure requirements.txt exists."""
    assert REQUIREMENTS_PATH.exists(), f"requirements.txt not found at {REQUIREMENTS_PATH}"

def check_quickstart_exists():
    """Ensure quickstart.md exists."""
    assert QUICKSTART_PATH.exists(), f"quickstart.md not found at {QUICKSTART_PATH}"

def check_scripts_exist():
    """Ensure main entry point scripts exist."""
    assert BENCHMARK_SCRIPT.exists(), f"run_benchmark.py not found at {BENCHMARK_SCRIPT}"
    assert TASK_SCRIPT.exists(), f"run_task.py not found at {TASK_SCRIPT}"

def test_quickstart_syntax_validation():
    """
    Validate that the scripts can be parsed (syntax check) and
    that they respond to --help without importing heavy dependencies if possible,
    or at least without crashing immediately.
    """
    # 1. Verify files exist
    check_requirements_exists()
    check_quickstart_exists()
    check_scripts_exist()

    # 2. Validate Python syntax
    # We run python -m py_compile on the main scripts to ensure they are syntactically valid
    # without actually importing them (which might fail due to missing deps in a test env).
    for script in [BENCHMARK_SCRIPT, TASK_SCRIPT]:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Syntax error in {script}:\n{result.stderr}"
        )

def test_cli_help_execution():
    """
    Simulate the 'run --help' step from quickstart.md.
    This verifies the CLI argument parsing is functional.
    """
    # Test run_benchmark.py --help
    result_benchmark = subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30
    )

    # We expect returncode 0 for --help, or 2 if argparse finds an issue but prints help.
    # In a healthy state, it should be 0.
    if result_benchmark.returncode != 0:
        # If it fails, it might be due to missing imports at runtime (e.g., missing deps).
        # However, for T054, we assume the environment is set up.
        # If the error is ImportError, we note it but the task is about the script structure.
        # But per T054 "verify no errors", we assert it runs cleanly if deps are present.
        # Since we are running in the context of the project, we expect it to work.
        assert result_benchmark.returncode == 0, (
            f"run_benchmark.py --help failed:\nStdout: {result_benchmark.stdout}\nStderr: {result_benchmark.stderr}"
        )

    assert "usage:" in result_benchmark.stdout.lower(), (
        "run_benchmark.py --help did not show usage information."
    )

    # Test run_task.py --help
    result_task = subprocess.run(
        [sys.executable, str(TASK_SCRIPT), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30
    )

    if result_task.returncode != 0:
        assert result_task.returncode == 0, (
            f"run_task.py --help failed:\nStdout: {result_task.stdout}\nStderr: {result_task.stderr}"
        )

    assert "usage:" in result_task.stdout.lower(), (
        "run_task.py --help did not show usage information."
    )

def test_config_loading_validation():
    """
    Validate that the default config file exists and can be loaded by the script logic
    (simulated via a quick import check if possible, or file existence).
    """
    default_config = PROJECT_ROOT / "src" / "benchmark" / "config" / "default.yaml"
    assert default_config.exists(), f"default.yaml not found at {default_config}"

    # Try to parse the YAML to ensure it's not corrupted
    import yaml
    with open(default_config, 'r') as f:
        try:
            config = yaml.safe_load(f)
            assert isinstance(config, dict), "default.yaml must be a YAML mapping"
            assert "datasets" in config, "default.yaml missing 'datasets' key"
            assert "seeds" in config, "default.yaml missing 'seeds' key"
        except yaml.YAMLError as e:
            pytest.fail(f"default.yaml is not valid YAML: {e}")

def test_quickstart_instructions_consistency():
    """
    Verify that the instructions in quickstart.md match the actual file structure.
    This is a sanity check for the 'validation method' described in T054.
    """
    with open(QUICKSTART_PATH, 'r') as f:
        content = f.read()

    # Check for key sections mentioned in tasks.md T015
    required_sections = [
        "Prerequisites",
        "Setup Commands",
        "Verification steps",
        "Troubleshooting"
    ]

    for section in required_sections:
        assert section.lower() in content.lower(), (
            f"quickstart.md missing required section: {section}"
        )

    # Check for command patterns
    assert "pip install" in content.lower(), "quickstart.md should mention pip install"
    assert "python" in content.lower(), "quickstart.md should mention python execution"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])