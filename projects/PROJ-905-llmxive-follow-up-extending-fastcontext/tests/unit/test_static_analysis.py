import pytest
from pathlib import Path
import tempfile
import os

# Import the function under test from the sibling module
from static_analysis import calculate_dir_score


@pytest.fixture
def sample_repo_standard(tmp_path):
    """
    Fixture creating a standard repository layout:
    - src/
    - tests/
    - docs/
    Returns the Path to the temporary repository root.
    """
    repo_root = tmp_path / "sample_repo_standard"
    repo_root.mkdir()
    
    # Create the standard directories
    (repo_root / "src").mkdir()
    (repo_root / "tests").mkdir()
    (repo_root / "docs").mkdir()
    
    # Add a dummy file in src to ensure it's not empty (optional but good practice)
    (repo_root / "src" / "__init__.py").touch()
    
    return repo_root


def test_directory_naming_returns_score_1_0_for_standard_layout(sample_repo_standard):
    """
    Unit test for T008.
    Asserts that calculate_dir_score returns a normalized value indicating 
    complete alignment (1.0) when the repository contains src/, tests/, and docs/.
    """
    score = calculate_dir_score(sample_repo_standard)
    
    # The specification defines 1.0 as complete alignment (all present)
    # We assert exact equality because the logic is deterministic (0, 0.33, 0.66, 1.0)
    assert score == 1.0, f"Expected score 1.0 for standard layout, got {score}"