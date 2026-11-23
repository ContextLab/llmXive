"""
Unit tests for the security scan script.
"""
import pytest
import subprocess
from pathlib import Path
import tempfile
import os
from scripts.security_scan import check_prerequisites, run_scan


@pytest.fixture
def temp_baseline():
    """Create a temporary baseline file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.baseline', delete=False) as f:
        # Write a minimal valid baseline JSON structure
        f.write('{"version": "1.0", "results": {}, "filters": []}')
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_scan_dir():
    """Create a temporary directory for scanning."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup would happen in real test suite, but we leave it for now
    # import shutil
    # shutil.rmtree(temp_dir)


def test_check_prerequisites_detects_missing_tool(monkeypatch):
    """Test that check_prerequisites returns False if detect-secrets is missing."""
    # Mock subprocess.run to simulate missing tool
    def mock_run(cmd, **kwargs):
        raise FileNotFoundError("Command not found")

    monkeypatch.setattr("subprocess.run", mock_run)
    assert check_prerequisites("nonexistent.baseline") is False


def test_check_prerequisites_creates_baseline_if_missing(temp_baseline, monkeypatch):
    """Test that check_prerequisites creates a baseline if it doesn't exist."""
    # Remove the baseline file
    os.unlink(temp_baseline)

    # Mock subprocess to simulate successful baseline creation
    def mock_run(cmd, **kwargs):
        if "scan" in cmd:
            # Create the file
            Path(cmd[cmd.index("--baseline") + 1]).write_text('{"version": "1.0"}')
            return subprocess.CompletedProcess(cmd, 0)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("subprocess.run", mock_run)

    # This should succeed and create the file
    result = check_prerequisites(temp_baseline)
    assert result is True
    assert Path(temp_baseline).exists()


def test_run_scan_fails_on_missing_directory():
    """Test that run_scan returns False if scan path doesn't exist."""
    result = run_scan("/nonexistent/path/to/scan", "nonexistent.baseline")
    assert result is False


def test_run_scan_success(temp_baseline, temp_scan_dir):
    """Test that run_scan returns True when no secrets are found."""
    # Create a clean file in the scan dir
    clean_file = Path(temp_scan_dir) / "clean.txt"
    clean_file.write_text("This is a clean file with no secrets.")

    # Mock subprocess to simulate clean scan
    def mock_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="No secrets found", stderr="")

    import subprocess
    original_run = subprocess.run
    subprocess.run = mock_run

    try:
        result = run_scan(temp_scan_dir, temp_baseline)
        assert result is True
    finally:
        subprocess.run = original_run


def test_run_scan_fails_on_pii(temp_baseline, temp_scan_dir):
    """Test that run_scan returns False when PII is detected."""
    # Create a file with a potential secret
    secret_file = Path(temp_scan_dir) / "secret.txt"
    secret_file.write_text("API_KEY = 'sk-1234567890abcdef'")

    # Mock subprocess to simulate detection (return code 1)
    def mock_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd,
            1,
            stdout="Potential secret found: API_KEY",
            stderr="Audit failed"
        )

    import subprocess
    original_run = subprocess.run
    subprocess.run = mock_run

    try:
        result = run_scan(temp_scan_dir, temp_baseline)
        assert result is False
    finally:
        subprocess.run = original_run
