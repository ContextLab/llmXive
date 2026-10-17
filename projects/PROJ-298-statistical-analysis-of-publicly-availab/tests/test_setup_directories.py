import sys
from pathlib import Path

import pytest

# Import the toolkit's path helper to monkey‑patch the project root
from llmxive_toolkit import paths

@pytest.fixture
def temp_project_root(tmp_path, monkeypatch):
    """
    Monkey‑patch llmxive_toolkit.paths.root to point at a temporary directory.
    This isolates the test from the real repository root.
    """
    monkeypatch.setattr('llmxive_toolkit.paths.root', tmp_path, raising=False)
    return tmp_path

def test_setup_directories_creates_expected_structure(temp_project_root):
    """
    Run the setup_directories script and verify that all required directories
    are created and writable, and that no ``state`` directory is created
    (the platform owns that location).
    """
    # Import the script after the root has been monkey‑patched
    from code.setup_directories import main

    exit_code = main()
    assert exit_code == 0, "setup_directories should exit with code 0 on success"

    # Expected directories relative to the temporary project root
    expected_dirs = [
        "code",
        "tests",
        "data",
        "notebooks",
        "data/raw",
        "data/processed",
        "data/events",
        "data/taxonomy",
    ]

    for rel_path in expected_dirs:
        dir_path = temp_project_root / rel_path
        assert dir_path.is_dir(), f"Expected directory {dir_path} to exist"
        # Verify writability by attempting to create and delete a temp file
        try:
            with tempfile.NamedTemporaryFile(dir=dir_path, delete=False) as tmp:
                tmp_path = Path(tmp.name)
            tmp_path.unlink()
        except Exception as exc:
            pytest.fail(f"Directory {dir_path} is not writable: {exc}")

    # Ensure the script did not create a ``state`` directory under the project root
    state_dir = temp_project_root / "state"
    assert not state_dir.exists(), "The script must not create a 'state' directory"