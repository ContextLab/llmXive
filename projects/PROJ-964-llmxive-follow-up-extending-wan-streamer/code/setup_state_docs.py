import os
import sys
from pathlib import Path

def setup_state_docs_directories():
    """
    Creates the required 'state/' and 'docs/' directories at the project root.
    This satisfies the requirement for T004.
    """
    # Determine project root (assuming code/ is at root or one level down)
    # We look for the .git directory or just assume the parent of this file's directory
    # is the project root if 'code' is a subdirectory.
    current_file = Path(__file__).resolve()
    project_root = current_file.parent

    state_dir = project_root / "state"
    docs_dir = project_root / "docs"

    # Create directories if they don't exist
    state_dir.mkdir(exist_ok=True)
    docs_dir.mkdir(exist_ok=True)

    # Create a placeholder README in docs to ensure the directory is not empty
    # (Some systems treat empty dirs as non-existent in certain checks)
    docs_readme = docs_dir / "README.md"
    if not docs_readme.exists():
        docs_readme.write_text(
            "# Project Documentation\n\n"
            "This directory contains project documentation, research notes, and design documents.\n"
        )

    # Create a placeholder state file to ensure the directory is valid
    state_init = state_dir / ".gitkeep"
    if not state_init.exists():
        state_init.write_text("")

    return state_dir, docs_dir

def main():
    """Entry point for script execution."""
    state_dir, docs_dir = setup_state_docs_directories()
    print(f"Created directories: {state_dir}, {docs_dir}")
    
    # Verification step as per T004 requirements
    assert os.path.isdir(state_dir), f"Failed to create or verify state directory: {state_dir}"
    assert os.path.isdir(docs_dir), f"Failed to create or verify docs directory: {docs_dir}"
    
    print("Verification passed: state/ and docs/ directories exist and are valid.")

if __name__ == "__main__":
    main()
