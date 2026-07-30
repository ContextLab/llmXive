import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_directories

def test_create_directories():
    """Test that create_directories creates all expected folders."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        create_directories(base_path)
        
        expected_dirs = [
            "code",
            "code/agent",
            "code/analysis",
            "code/data",
            "code/metrics",
            "code/utils",
            "data/raw",
            "data/curated",
            "data/results",
            "tests/unit",
            "tests/contract",
            "contracts",
            "docs",
            "paper",
            "state",
            "figures",
        ]
        
        for dir_name in expected_dirs:
            full_path = base_path / dir_name
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"
