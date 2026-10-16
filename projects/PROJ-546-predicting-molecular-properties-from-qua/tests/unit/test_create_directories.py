"""
Unit test for the create_directories utility (Task T001).

The test imports the module, invokes the directory‑creation function and
asserts that every expected directory now exists on the filesystem.
"""

import importlib
import sys
from pathlib import Path

# Import the module under test
create_dirs = importlib.import_module("code.create_directories")

def test_create_directories_creates_all_paths(tmp_path, monkeypatch):
    """
    Verify that `create_directories()` creates the exact hierarchy required
    by the specification. The test runs in an isolated temporary directory
    to avoid polluting the repository.
    """
    # Monkey‑patch the repository root to the temporary directory
    repo_root = tmp_path
    # The module determines the repo root via `Path(__file__).resolve().parent.parent`.
    # We replace `__file__` attribute so that the calculation points into our tmp dir.
    # This avoids creating directories in the real project tree during testing.
    module_file = Path(repo_root) / "code" / "create_directories.py"
    module_file.parent.mkdir(parents=True, exist_ok=True)
    # Write the current source code to the temporary location so it can be imported
    with open(__file__, "r", encoding="utf-8") as src, open(module_file, "w", encoding="utf-8") as dst:
        dst.write(src.read())
    monkeypatch.setattr(create_dirs, "__file__", str(module_file), raising=False)

    # Run the directory creation logic
    create_dirs.create_directories()

    # Expected directories relative to the repo root
    expected = [
        Path("projects/PROJ-546-predicting-molecular-properties-from-qua/code"),
        Path("projects/PROJ-546-predicting-molecular-properties-from-qua/data/raw"),
        Path("projects/PROJ-546-predicting-molecular-properties-from-qua/data/optimized_geometries"),
        Path("projects/PROJ-546-predicting-molecular-properties-from-qua/logs"),
        Path("projects/PROJ-546-predicting-molecular-properties-from-qua/reports"),
        Path("projects/PROJ-546-predicting-molecular-properties-from-qua/specs/001-predicting-molecular-properties-from-qua/contracts"),
        Path("projects/PROJ-546-predicting-molecular-properties-from-qua/tests/unit"),
        Path("projects/PROJ-546-predicting-molecular-properties-from-qua/tests/integration"),
        Path("projects/PROJ-546-predicting-molecular-properties-from-qua/tests/contract"),
    ]

    for rel_path in expected:
        full_path = repo_root / rel_path
        assert full_path.is_dir(), f"Expected directory {full_path} to exist"