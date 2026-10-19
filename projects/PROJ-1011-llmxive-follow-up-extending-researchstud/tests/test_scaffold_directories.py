"""
Test that the top‑level project layout directories exist.
"""
import os
from pathlib import Path

def test_scaffold_directories():
    """
    Verify that the required top‑level directories are present:
    - projects/PROJ-1011-llmxive-follow-up-extending-researchstud
    - code
    - data
    - tests
    """
    # Root of the repository (where this test resides)
    repo_root = Path(__file__).resolve().parent.parent
    
    # Expected directories relative to repo root
    expected_dirs = [
        repo_root / "projects" / "PROJ-1011-llmxive-follow-up-extending-researchstud",
        repo_root / "code",
        repo_root / "data",
        repo_root / "tests",
    ]
    
    missing = [str(p) for p in expected_dirs if not p.is_dir()]
    assert not missing, f"Missing required directories: {', '.join(missing)}"