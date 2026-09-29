import os
import pytest
from pathlib import Path
from scripts.create_contract_structure import create_directories, print_tree

def test_create_contract_directories(tmp_path):
    """Test that the contracts directory structure is created correctly."""
    # Monkeypatch the root to use tmp_path for testing
    import scripts.create_contract_structure as module
    original_cwd = Path.cwd()
    
    # We simulate the creation in a temp directory
    # In real execution, this would be the project root
    # For this test, we verify the logic by checking if the function
    # creates the expected paths relative to a known root.
    
    # Since create_directories uses __file__ to find root, we can't easily mock it
    # without changing the script. Instead, we verify the expected paths exist
    # after calling the function in the actual project context if possible,
    # or we test the logic by mocking Path behavior.
    
    # Direct verification of the expected structure relative to project root
    # assuming the script runs from code/scripts
    project_root = Path(__file__).resolve().parent.parent.parent
    contracts_root = project_root / "contracts"
    
    expected_subdirs = [
        contracts_root / "scene",
        contracts_root / "trajectory",
        contracts_root / "stats"
    ]
    
    # Run the creation (idempotent)
    create_directories()
    
    for subdir in expected_subdirs:
        assert subdir.exists(), f"Directory {subdir} was not created"
        assert subdir.is_dir(), f"{subdir} is not a directory"
        
        # Check for README placeholder
        readme = subdir / "README.md"
        assert readme.exists(), f"README.md missing in {subdir}"
        assert "Contracts" in readme.read_text(), "README.md content is invalid"

def test_print_tree_output(capsys):
    """Test that print_tree outputs the structure."""
    # Ensure structure exists first
    create_directories()
    project_root = Path(__file__).resolve().parent.parent.parent
    contracts_root = project_root / "contracts"
    
    print_tree(contracts_root)
    captured = capsys.readouterr()
    assert "scene" in captured.out
    assert "trajectory" in captured.out
    assert "stats" in captured.out