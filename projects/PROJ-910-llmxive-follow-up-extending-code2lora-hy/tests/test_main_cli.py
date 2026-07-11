"""
Tests for the main.py CLI entry point (Task T009).
Verifies that the CLI lists the required commands.
"""
import subprocess
import sys

def test_help_list_commands():
    """
    Verify that `python code/main.py --help` lists the three required commands:
    generate, evaluate, sensitivity.
    """
    result = subprocess.run(
        [sys.executable, "code/main.py", "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"CLI failed to run: {result.stderr}"
    
    stdout = result.stdout
    
    # Check for required commands in help text
    assert "generate" in stdout, "Help text missing 'generate' command"
    assert "evaluate" in stdout, "Help text missing 'evaluate' command"
    assert "sensitivity" in stdout, "Help text missing 'sensitivity' command"
    
    # Verify they are listed as subcommands
    assert "Available commands:" in stdout or "positional arguments:" in stdout, \
        "Help text does not indicate subcommands"

def test_generate_subcommand_help():
    """
    Verify that `python code/main.py generate --help` runs without error.
    """
    result = subprocess.run(
        [sys.executable, "code/main.py", "generate", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Generate help failed: {result.stderr}"

def test_evaluate_subcommand_help():
    """
    Verify that `python code/main.py evaluate --help` runs without error.
    """
    result = subprocess.run(
        [sys.executable, "code/main.py", "evaluate", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Evaluate help failed: {result.stderr}"

def test_sensitivity_subcommand_help():
    """
    Verify that `python code/main.py sensitivity --help` runs without error.
    """
    result = subprocess.run(
        [sys.executable, "code/main.py", "sensitivity", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Sensitivity help failed: {result.stderr}"