"""
Simple pytest that ensures the pip installation log exists and contains
the phrase 'Successfully installed', indicating that the pinned
dependencies were installed without errors.
"""
import re
from pathlib import Path

def test_pip_install_log_exists_and_successful():
    log_path = Path(__file__).resolve().parents[2] / "data" / "verification" / "pip_install_log.txt"
    assert log_path.is_file(), f"Log file not found at {log_path}"
    content = log_path.read_text(encoding="utf-8")
    # Look for a typical success marker from pip
    assert re.search(r"Successfully installed", content), "pip install did not report successful installation"