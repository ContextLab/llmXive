import pytest
import subprocess
import sys
from pathlib import Path

def test_pytest_discoverable(project_root: Path):
    """Test that pytest can discover and run at least one test."""
    # Run pytest with minimal discovery
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=project_root / "code",
        capture_output=True,
        text=True
    )
    
    # Should find at least the config test itself
    assert "test_pytest_config.py" in result.stdout or result.returncode == 0, \
        "Pytest could not discover tests"
