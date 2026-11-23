"""
Unit tests for the project CLI defined in code/main.py.
The tests verify that the argument parser accepts the expected flags
and that the script exits with code 0 when invoked without the
--full-pipeline flag.
"""
import subprocess
import sys
import os

# Resolve the path to the main module relative to the repository root.
MAIN_SCRIPT = os.path.join("code", "main.py")

def run_cli(args):
    """Helper to invoke the CLI and capture exit code."""
    completed = subprocess.run(
        [sys.executable, MAIN_SCRIPT] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed

def test_cli_parsing():
    """CLI should parse flags without error and exit with code 0."""
    result = run_cli(
        ["--include-mp", "--fallback-mode", "--streaming"]
    )
    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"
    # Ensure the help text contains our flag names.
    help_result = run_cli(["-h"])
    assert "--full-pipeline" in help_result.stdout
    assert "--include-mp" in help_result.stdout
    assert "--fallback-mode" in help_result.stdout
    assert "--streaming" in help_result.stdout