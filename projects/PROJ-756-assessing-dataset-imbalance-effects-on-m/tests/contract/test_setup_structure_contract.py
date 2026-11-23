import os
import sys
import pytest
from pathlib import Path
import shutil

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_structure import create_directories

PROJECT_ROOT = Path("projects/PROJ-756-assessing-dataset-imbalance-effects-on-m")

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Ensure clean state before and after tests."""
    if PROJECT_ROOT.exists():
        shutil.rmtree(PROJECT_ROOT)
    
    yield
    
    if PROJECT_ROOT.exists():
        shutil.rmtree(PROJECT_ROOT)

def test_contract_directory_structure():
    """
    Contract test: Verify the project structure matches the specification.
    The specification requires: data/, code/, tests/, artifacts/, results/, state/, logs/, logs/archive/
    """
    create_directories()
    
    # Define the contract structure
    contract_structure = {
        "data": {
            "type": "directory",
            "children": {
                "raw": {"type": "directory"}
            }
        },
        "code": {"type": "directory"},
        "tests": {"type": "directory"},
        "artifacts": {"type": "directory"},
        "results": {"type": "directory"},
        "state": {"type": "directory"},
        "logs": {
            "type": "directory",
            "children": {
                "archive": {"type": "directory"}
            }
        }
    }

    def verify_structure(base_path, contract):
        for name, spec in contract.items():
            full_path = base_path / name
            
            assert full_path.exists(), f"Missing required path: {full_path}"
            
            if spec["type"] == "directory":
                assert full_path.is_dir(), f"{full_path} is not a directory"
                
                if "children" in spec:
                    verify_structure(full_path, spec["children"])
            else:
                assert full_path.is_file(), f"{full_path} is not a file"

    verify_structure(PROJECT_ROOT, contract_structure)

def test_contract_project_root_path():
    """
    Contract test: Verify the project root path is exactly as specified.
    """
    create_directories()
    
    expected_path = Path("projects/PROJ-756-assessing-dataset-imbalance-effects-on-m")
    assert PROJECT_ROOT == expected_path, f"Project root path mismatch: {PROJECT_ROOT} != {expected_path}"
    assert PROJECT_ROOT.exists(), "Project root does not exist"