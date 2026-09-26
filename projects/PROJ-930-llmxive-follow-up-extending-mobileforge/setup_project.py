"""
Project initialization script for llmXive MobileForge Logic Distillation.

This script creates the required directory structure and initializes
configuration files for the project.
"""
import os
import sys
from pathlib import Path

def main():
    """Create project structure and initialize configuration files."""
    project_root = Path("projects/PROJ-930-llmxive-follow-up-extending-mobileforge")
    code_dir = project_root / "code"
    
    # Define directory structure
    directories = [
        "data/raw",
        "data/processed",
        "data/evaluation",
        "models",
        "utils",
        "tests/unit",
        "tests/integration",
        "state",
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = code_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep in empty directories
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Directory placeholder\n")
    
    # Create state directory structure
    state_dir = code_dir / "state"
    (state_dir / "artifacts.json").write_text("{}\n")
    
    print(f"✓ Project structure created at {project_root}")
    print(f"  - {len(directories)} directories initialized")
    print(f"  - Configuration files ready")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())