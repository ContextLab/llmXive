import sys
import pytest
from pathlib import Path

def test_bootstrap_creates_requirements_and_directories(monkeypatch, tmp_path):
    """
    Verify that the bootstrap script creates the required directory layout,
    writes the pinned requirements.txt, and exits cleanly.
    """
    # Monkey‑patch the project root used by llmxive_toolkit.paths to a temporary directory
    from llmxive_toolkit import paths
    monkeypatch.setattr(paths, "root", tmp_path)

    # Import the bootstrap module after the monkey‑patch so that lazy imports pick up the new root
    from code.bootstrap import main, _REQUIREMENTS

    # The bootstrap script calls sys.exit(0); capture the SystemExit exception
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0

    # Expected directories under the temporary root
    expected_dirs = [
        tmp_path / "code",
        tmp_path / "data" / "raw",
        tmp_path / "data" / "interim",
        tmp_path / "data" / "processed",
        tmp_path / "data" / "results",
        tmp_path / "code" / "tests",
        tmp_path / "docs",
    ]
    for d in expected_dirs:
        assert d.is_dir(), f"Missing expected directory: {d}"

    # Verify that the pinned requirements.txt was written correctly
    req_path = tmp_path / "code" / "requirements.txt"
    assert req_path.is_file(), "requirements.txt was not created"
    # Compare file contents to the internal _REQUIREMENTS string (strip trailing newline)
    file_content = req_path.read_text().strip()
    assert file_content == _REQUIREMENTS.strip(), "requirements.txt content does not match the pinned list"