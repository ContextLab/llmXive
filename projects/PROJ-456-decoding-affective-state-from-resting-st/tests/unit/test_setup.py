import os
import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "projects" / "PROJ-456-decoding-affective-state-from-resting-st" / "code"))

def test_project_structure_exists():
    """Verify that the project directory structure was created correctly."""
    base_dir = Path(__file__).parent.parent.parent.parent
    project_root = base_dir / "projects" / "PROJ-456-decoding-affective-state-from-resting-st"
    
    # Check main directories exist
    assert project_root.exists(), "Project root directory does not exist"
    assert (project_root / "code").exists(), "code/ directory missing"
    assert (project_root / "data").exists(), "data/ directory missing"
    assert (project_root / "tests").exists(), "tests/ directory missing"
    assert (project_root / "docs").exists(), "docs/ directory missing"
    assert (project_root / "state").exists(), "state/ directory missing"
    
    # Check subdirectories
    assert (project_root / "data" / "raw").exists(), "data/raw/ directory missing"
    assert (project_root / "data" / "processed").exists(), "data/processed/ directory missing"
    assert (project_root / "data" / "templates").exists(), "data/templates/ directory missing"
    assert (project_root / "data" / "logs").exists(), "data/logs/ directory missing"
    assert (project_root / "tests" / "unit").exists(), "tests/unit/ directory missing"
    
    # Check for .gitkeep files (evidence of directory creation)
    gitkeep_found = False
    for dir_path in [project_root, project_root / "code", project_root / "data"]:
        if (dir_path / ".gitkeep").exists():
            gitkeep_found = True
            break
    
    assert gitkeep_found, "No .gitkeep files found - directories may not have been properly created"

def test_placeholder_files_exist():
    """Verify that placeholder files were created."""
    base_dir = Path(__file__).parent.parent.parent.parent
    project_root = base_dir / "projects" / "PROJ-456-decoding-affective-state-from-resting-st"
    
    assert (project_root / "README.md").exists(), "README.md missing"
    assert (project_root / "requirements.txt").exists(), "requirements.txt missing"
    assert (project_root / "code" / "__init__.py").exists(), "code/__init__.py missing"
    assert (project_root / "tests" / "__init__.py").exists(), "tests/__init__.py missing"

def test_setup_module_imports():
    """Verify that the setup module can be imported."""
    try:
        from setup_project_structure import create_directory_structure, create_placeholder_files, main
        assert callable(create_directory_structure)
        assert callable(create_placeholder_files)
        assert callable(main)
    except ImportError as e:
        pytest.fail(f"Failed to import setup module: {e}")