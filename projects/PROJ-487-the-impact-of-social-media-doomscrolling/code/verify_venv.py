"""
Task T004b: Verify Python virtual environment.

Verifies that the virtual environment activation script exists at:
projects/PROJ-487-the-impact-of-social-media-doomscrolling/venv/bin/activate

Exit code 0 if found, 1 if not.
"""
import os
import sys
from pathlib import Path

def verify_venv(project_root: Path) -> bool:
    """
    Verify that the venv/bin/activate script exists in the project root.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        True if the activation script exists, False otherwise.
    """
    activate_path = project_root / "venv" / "bin" / "activate"
    if not activate_path.exists():
        print(f"ERROR: Virtual environment activation script not found at: {activate_path}")
        print("Please run 'python -m venv venv' in the project root first.")
        return False
    
    if not activate_path.is_file():
        print(f"ERROR: Path exists but is not a file: {activate_path}")
        return False
    
    print(f"SUCCESS: Virtual environment activation script found at: {activate_path}")
    return True

def main():
    """Main entry point for verification."""
    # Determine the project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    print(f"Checking project root: {project_root}")
    
    success = verify_venv(project_root)
    
    if not success:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()