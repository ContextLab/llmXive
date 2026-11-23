"""
Unit tests for the ``setup_project_structure`` utility (Task T001).

The test creates a temporary directory, patches the internal
``_REQUIRED_DIRS`` constant to point inside that temporary location,
runs ``create_directories()``, and asserts that every expected
directory exists after the call.
"""

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import List

import pytest

# The module under test lives at ``code/setup_project_structure.py``.
# Import it as a regular module (not as a package) to avoid interference
# with the repository's top‑level ``code`` package.
SPEC_MODULE_PATH = Path(__file__).resolve().parents[2] / "code" / "setup_project_structure.py"

@pytest.fixture
def temp_root(tmp_path, monkeypatch):
    """
    Create a temporary repository root and adjust ``sys.path`` so that the
    module can be imported from that location.
    """
    # Add the temporary root to ``sys.path`` so that ``import code.setup_project_structure``
    # resolves to the temporary copy.
    sys.path.insert(0, str(tmp_path))
    # Copy the source file into the temporary tree preserving its relative location.
    target_dir = tmp_path / "code"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "setup_project_structure.py"
    target_file.write_text(SPEC_MODULE_PATH.read_text(encoding="utf-8"))
    # Ensure the package namespace exists (``code`` is a namespace package)
    (tmp_path / "code" / "__init__.py").write_text("")
    yield tmp_path
    # Cleanup
    sys.path.pop(0)

def test_create_directories_creates_all_required_paths(temp_root):
    """
    Verify that ``create_directories`` creates the full layout.
    """
    # Import the freshly‑copied module from the temporary location.
    module: ModuleType = importlib.import_module("code.setup_project_structure")
    # Patch the internal constant to use paths relative to the temporary root.
    # This avoids creating directories in the real repository during the test.
    temp_required: List[Path] = [
        temp_root / "code" / "src" / "config",
        temp_root / "code" / "src" / "extraction",
        temp_root / "code" / "src" / "detection",
        temp_root / "code" / "src" / "inference",
        temp_root / "code" / "src" / "analysis",
        temp_root / "code" / "src" / "reporting",
        temp_root / "code" / "src" / "pipeline",
        temp_root / "code" / "src" / "cli",
        temp_root / "code" / "tests" / "unit",
        temp_root / "code" / "tests" / "integration",
        temp_root / "code" / "tests" / "contract",
        temp_root / "code" / "data" / "raw",
        temp_root / "code" / "data" / "annotations",
        temp_root / "code" / "data" / "derived",
        temp_root / "code" / "data" / "results",
        temp_root / "code" / "logs",
        temp_root / "specs" / "001-eval-llm-review-quality" / "contracts",
    ]
    # Monkey‑patch the module's private constant.
    monkeypatch.setattr(module, "_REQUIRED_DIRS", temp_required, raising=False)

    # Run the creation routine.
    created_paths = module.create_directories()

    # All expected directories must now exist.
    for expected_dir in temp_required:
        assert expected_dir.is_dir(), f"Expected directory missing: {expected_dir}"
        # The function should have returned the absolute path.
        assert any(p.resolve() == expected_dir.resolve() for p in created_paths)

    # No extra directories should have been created beyond the list.
    all_created = {p.resolve() for p in created_paths}
    assert all_created == {d.resolve() for d in temp_required}