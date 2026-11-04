import subprocess
import sys
from pathlib import Path
import pytest

def test_cli_help_output():
    """
    Verify that python -m src.cli.main --help prints all required sub-commands.
    """
    # Run the CLI with --help
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    stdout = result.stdout
    
    # Required sub-commands
    required_cmds = [
        "extract-topology",
        "calc-vdos",
        "ingest-kappa",
        "aggregate",
        "analyze",
        "run"
    ]
    
    for cmd in required_cmds:
        assert cmd in stdout, f"Sub-command '{cmd}' not found in CLI help output"

def test_cli_invalid_command():
    """Verify that an invalid command prints help and exits 0 (per implementation)."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "invalid-cmd"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
