"""
Integration test for QIIME 2 CLI usage (T002b -> T018 dependency)

This test verifies that the QIIME 2 CLI can be invoked via the wrapper
and that the `qiime` command is available in the configured environment.
"""

import pytest
import subprocess
from code.qiime2_setup import run_qiime2_command, verify_qiime2_installation, setup_qiime2_environment

@pytest.mark.integration
def test_qiime2_cli_available():
    """
    Test that the QIIME 2 CLI is available and returns a version string.
    This ensures T002b (installation) is successful and T018 (preprocessing) can proceed.
    """
    # Ensure setup is run (or assume it was run by CI/runner)
    # In a real CI, this would be a separate step or pre-condition
    if not verify_qiime2_installation():
        # Attempt setup if not found (might be slow in CI)
        setup_qiime2_environment()

    success, stdout, stderr = run_qiime2_command(['--version'])
    
    assert success, f"QIIME 2 version check failed. Stderr: {stderr}"
    assert "qiime2" in stdout.lower(), f"Expected 'qiime2' in output, got: {stdout}"

@pytest.mark.integration
def test_qiime2_demux_help():
    """
    Test that a specific QIIME 2 plugin (demux) is accessible.
    """
    success, stdout, stderr = run_qiime2_command(['demux', 'summarize', '--help'])
    
    assert success, f"QIIME 2 demux help failed. Stderr: {stderr}"
    assert "summarize" in stdout.lower(), "Expected 'summarize' in help output."
