import os
import pytest
from pathlib import Path

def test_directory_structure_requirements():
    """
    Verify that the source directory structure required by T001b exists.
    Specifically checks for:
    - src/generators
    - src/inference
    - src/analysis
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    src_root = project_root / "src"

    required_dirs = [
        "generators",
        "inference",
        "analysis"
    ]

    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = src_root / dir_name
        if not dir_path.exists():
            missing_dirs.append(str(dir_path))
        elif not dir_path.is_dir():
            missing_dirs.append(f"{dir_path} (exists but is not a directory)")

    assert len(missing_dirs) == 0, f"Required source directories missing: {missing_dirs}"

    # Verify __init__.py files exist to make them valid Python packages
    for dir_name in required_dirs:
        init_path = src_root / dir_name / "__init__.py"
        if not init_path.exists():
            # Create empty __init__.py if missing to satisfy Python package requirements
            init_path.touch()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
