"""
Standalone script to execute T004: Create state/ and docs/ directories.
This ensures the task can be run independently and verified.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root (parent of code/)
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent

    state_dir = project_root / "state"
    docs_dir = project_root / "docs"

    print(f"Creating directories at: {project_root}")
    
    # Create directories
    state_dir.mkdir(exist_ok=True)
    docs_dir.mkdir(exist_ok=True)

    # Create placeholder files to ensure directories are populated
    (state_dir / ".gitkeep").touch(exist_ok=True)
    (docs_dir / "README.md").write_text(
        "# Documentation\n\nProject documentation goes here.\n"
    )

    # Verification as per T004
    assert os.path.isdir(state_dir), f"State directory creation failed: {state_dir}"
    assert os.path.isdir(docs_dir), f"Docs directory creation failed: {docs_dir}"

    print("SUCCESS: state/ and docs/ directories created and verified.")

if __name__ == "__main__":
    main()