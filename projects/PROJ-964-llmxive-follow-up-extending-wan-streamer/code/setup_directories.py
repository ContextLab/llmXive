"""
T002: Create code/ subdirectories.

Creates the required directory structure under the 'code/' folder:
- code/
- code/data/
- code/models/
- code/inference/
- code/evaluation/
- code/utils/
- code/tasks/
- code/tests/

Verification: Runs os.path.isdir on each path and asserts True.
"""
import os
import sys
from pathlib import Path


def setup_code_directories(base_path: Path) -> bool:
    """
    Create the required code/ subdirectories and verify their existence.
    
    Args:
        base_path: The project root path (parent of 'code' directory).
        
    Returns:
        True if all directories were created and verified successfully.
        
    Raises:
        AssertionError: If any directory creation or verification fails.
    """
    code_dir = base_path / "code"
    required_subdirs = [
        "data",
        "models",
        "inference",
        "evaluation",
        "utils",
        "tasks",
        "tests",
    ]
    
    # Ensure the base code directory exists
    code_dir.mkdir(parents=True, exist_ok=True)
    
    created_dirs = []
    for subdir_name in required_subdirs:
        subdir_path = code_dir / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(subdir_path)
    
    # Verification step: Assert all directories exist
    print("Verifying directory creation...")
    for dir_path in created_dirs:
        is_dir = os.path.isdir(str(dir_path))
        print(f"  Checking {dir_path}: {'EXISTS' if is_dir else 'MISSING'}")
        assert is_dir, f"Failed to create or verify directory: {dir_path}"
    
    # Also verify the root code directory
    assert os.path.isdir(str(code_dir)), f"Failed to create or verify directory: {code_dir}"
    print(f"  Checking {code_dir}: EXISTS")
    
    print("\nAll code/ subdirectories created and verified successfully.")
    return True


def main():
    """Entry point for the script."""
    # Determine project root (parent of this file's directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    print(f"Project root: {project_root}")
    print(f"Creating code/ subdirectories in: {project_root / 'code'}")
    
    success = setup_code_directories(project_root)
    
    if success:
        print("\nTask T002 completed successfully.")
        sys.exit(0)
    else:
        print("\nTask T002 failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
