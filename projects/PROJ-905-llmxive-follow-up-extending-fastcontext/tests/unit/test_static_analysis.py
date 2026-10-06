import pytest
from pathlib import Path
import tempfile
import os

# Import the function under test from the sibling module
from static_analysis import calculate_dir_score, calculate_import_score


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


@pytest.fixture
def sample_repo_mixed_imports(tmp_path):
    """
    Fixture creating a repository with mixed import patterns:
    - Standard library imports (e.g., 'import os')
    - Relative imports (e.g., 'from . import x')
    - Internal package imports (e.g., 'from mypkg import module')
    - External third-party imports (e.g., 'import requests')
    Returns the Path to the temporary repository root.
    """
    repo_root = tmp_path / "sample_repo_mixed_imports"
    repo_root.mkdir()
    
    # Create a src directory structure
    src_dir = repo_root / "src"
    src_dir.mkdir()
    
    # Create a package
    pkg_dir = src_dir / "mypkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").touch()
    
    # Create a module with mixed imports
    module_file = pkg_dir / "module.py"
    module_file.write_text(
        "import os\n"
        "import sys\n"
        "from . import utils\n"
        "from .subpkg import helper\n"
        "from mypkg.core import Engine\n"
        "import requests\n"
        "import numpy as np\n"
        "from external_lib import something\n"
    )
    
    # Create a subpackage
    subpkg_dir = pkg_dir / "subpkg"
    subpkg_dir.mkdir()
    (subpkg_dir / "__init__.py").touch()
    (subpkg_dir / "helper.py").write_text("pass\n")
    
    # Create another module
    core_file = pkg_dir / "core.py"
    core_file.write_text(
        "import json\n"
        "from mypkg import module\n"
    )
    
    return repo_root


def test_import_pattern_analysis_returns_score__5_for_mixed_imports(sample_repo_mixed_imports):
    """
    Unit test for T009.
    Asserts that calculate_import_score returns a moderate value (around 0.5)
    for a repository with mixed import patterns (internal, relative, external).
    
    The score is calculated as:
    0.5 * internal_ratio + 0.5 * (1 - graph_density)
    
    With mixed imports, we expect:
    - internal_ratio to be moderate (some internal, some external)
    - graph_density to be moderate (not fully connected, not empty)
    Resulting in a score around 0.5.
    """
    score = calculate_import_score(sample_repo_mixed_imports)
    
    # We expect a moderate score for mixed imports
    # The exact value depends on the specific implementation, but it should be
    # neither very low (0.0-0.2) nor very high (0.8-1.0)
    # A moderate value around 0.5 is expected for mixed patterns
    assert 0.3 <= score <= 0.7, (
        f"Expected moderate import score (0.3-0.7) for mixed imports, "
        f"got {score}. This suggests the import analysis may not be "
        f"correctly distinguishing between internal and external imports."
    )