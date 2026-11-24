"""
Test that the top‑level project directories exist.
This test runs after the ``create_structure.py`` script has been executed.
The platform‑owned ``state`` directory is *not* expected to be created by
the project code; it is managed separately.
"""

import os
from pathlib import Path

def test_top_level_directories_exist():
    project_root = Path(__file__).resolve().parents[1]  # tests/ -> project root
    expected = ["code", "data", "tests", "docs", "artifacts"]
    missing = [d for d in expected if not (project_root / d).is_dir()]
    assert not missing, f"Missing directories: {missing}"