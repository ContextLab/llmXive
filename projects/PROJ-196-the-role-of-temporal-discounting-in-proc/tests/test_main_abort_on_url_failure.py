"""
Test that the main orchestrator aborts cleanly when a URL verification fails.
"""
import subprocess
import sys
from pathlib import Path

def test_abort_without_fallback():
    # Use a deliberately invalid URL to trigger the RuntimeError in verify_urls.
    # The script should exit with a non‑zero status code.
    cmd = [
        sys.executable,
        str(Path(__file__).parents[2] / "code" / "main.py"),
        "--url", "http://example.invalid/does-not-exist"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert "URL verification failed" in result.stderr or "URL verification failed" in result.stdout