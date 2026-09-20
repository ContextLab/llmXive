import os
import pytest
from pathlib import Path

def test_directory_structure_requirements():
    """
    Verify that the required directory structure for the project exists.
    This test checks:
    - src/generators exists
    - src/inference exists
    - src/analysis exists
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    src_dir = base_dir / "src"
    
    required_dirs = [
        "generators",
        "inference",
        "analysis"
    ]
    
    for subdir in required_dirs:
        target_path = src_dir / subdir
        assert target_path.exists(), f"Directory {target_path} does not exist"
        assert target_path.is_dir(), f"Path {target_path} is not a directory"
        
        # Check for __init__.py to ensure it's a Python package
        init_file = target_path / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in {target_path}"
    
    # Also verify the tests directory structure
    tests_dir = base_dir / "tests"
    unit_dir = tests_dir / "unit"
    integration_dir = tests_dir / "integration"
    
    assert unit_dir.exists(), f"Directory {unit_dir} does not exist"
    assert integration_dir.exists(), f"Directory {integration_dir} does not exist"
    
    print("All required directory structures verified successfully.")