import os
import sys
from pathlib import Path

def setup_state_docs_directories(base_path: Path) -> None:
    """
    Create the required 'state/' and 'docs/' directories at the project root.
    
    This implements T004: Create `state/` and `docs/` directories.
    
    Args:
        base_path: The project root directory path.
    """
    state_dir = base_path / "state"
    docs_dir = base_path / "docs"
    
    # Create state directory and subdirectories
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "projects").mkdir(exist_ok=True)
    (state_dir / "artifacts").mkdir(exist_ok=True)
    
    # Create docs directory and subdirectories
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "api").mkdir(exist_ok=True)
    (docs_dir / "design").mkdir(exist_ok=True)
    
    # Create placeholder README files to ensure directories are tracked
    (state_dir / "README.md").write_text(
        "# Project State\n\n"
        "This directory contains the persistent state of the project, "
        "including artifact hashes, configuration snapshots, and execution logs.\n\n"
        "## Contents\n\n"
        "- `projects/`: Per-project state files\n"
        "- `artifacts/`: Hash records and metadata for generated artifacts\n"
    )
    
    (docs_dir / "README.md").write_text(
        "# Project Documentation\n\n"
        "This directory contains all project documentation, including design specs, "
        "API references, and user guides.\n\n"
        "## Contents\n\n"
        "- `api/`: API documentation and contract specifications\n"
        "- `design/`: Design documents, architecture decisions, and planning materials\n"
    )

    print(f"Created directories: {state_dir}, {docs_dir}")

def main() -> None:
    """Entry point for directory setup."""
    # Determine project root (parent of 'code' directory)
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent
    
    setup_state_docs_directories(project_root)
    print("T004: state/ and docs/ directories created successfully.")

if __name__ == "__main__":
    main()
