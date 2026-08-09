"""
Module to initialize the project directory structure for llmXive Follow-up.
Creates all required directories as defined in T001a.
"""
import os
from pathlib import Path
from typing import List


def ensure_directories(root_path: str = None) -> List[str]:
    """
    Creates the required directory structure for the project.

    Args:
        root_path: The base path for the project. Defaults to the current directory
                   if None, but typically should be the project root.

    Returns:
        A list of created directory paths.
    """
    if root_path is None:
        root_path = Path.cwd()
    else:
        root_path = Path(root_path)

    # Define relative paths based on T001a requirements
    # Note: The task specifies paths relative to the project root, but since this
    # script might be run from the root, we construct them relative to the root_path.
    # The task lists:
    # projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/
    # tests/
    # data/raw/
    # data/processed/
    # data/test/
    # specs/
    # docs/
    # specs/001-llmxive-drift-detection/

    # Based on the task description, the project root is `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/`
    # However, the task says "Initialize project directory structure: Create ... `projects/.../code/`".
    # This implies the script might be run from a parent directory, or the paths are relative to the repo root.
    # Given the "Path Conventions" section: "Paths shown below assume single project structure per plan.md"
    # and the task explicitly lists the full path `projects/PROJ-.../code/`, we will create these relative to the provided root.
    # If root_path is the repo root, we create the project folder.
    # If root_path is the project folder, we create the subfolders.
    # To be safe and match the task literal requirement "Create ... `projects/.../code/`", we assume root_path is the repo root.
    
    # Let's assume the script is run from the repo root (or passed the repo root).
    # The task requires:
    # `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`
    # `tests/` (relative to project root? or repo root? T001b test_directories_exist suggests relative to project root usually, but T001a lists full path)
    # Looking at T001a: "Create and verify directories `projects/.../code/`, `tests/`, `data/raw/`..."
    # The mix of full path and relative paths suggests `tests/`, `data/`, `specs/`, `docs/` are relative to the project root.
    # So:
    # Project Root = `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/`
    # We need to create:
    # 1. `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` (This is Project Root + code)
    # 2. `tests/` (Relative to Project Root)
    # 3. `data/raw/`
    # 4. `data/processed/`
    # 5. `data/test/`
    # 6. `specs/`
    # 7. `docs/`
    # 8. `specs/001-llmxive-drift-detection/`

    # To make this robust, we will assume the `root_path` passed is the REPO ROOT.
    # Then the project directory is `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5`.
    
    project_name = "PROJ-924-llmxive-follow-up-extending-agentdog-1-5"
    project_dir = root_path / "projects" / project_name
    
    # Ensure the project directory exists first
    project_dir.mkdir(parents=True, exist_ok=True)
    
    relative_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/test",
        "specs",
        "docs",
        "specs/001-llmxive-drift-detection"
    ]

    created_paths = []
    for rel_dir in relative_dirs:
        dir_path = project_dir / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(dir_path))
    
    return created_paths

def main():
    """Entry point for creating directory structure."""
    # Default to current working directory as the repo root
    root = Path.cwd()
    print(f"Creating directory structure in: {root}")
    
    created = ensure_directories(root)
    
    print("Successfully created directories:")
    for p in created:
        print(f"  - {p}")
    
    # Verify existence (Acceptance Criteria)
    print("\nVerifying existence...")
    all_exist = True
    for p in created:
        if not os.path.exists(p):
            print(f"  ERROR: {p} does not exist!")
            all_exist = False
        else:
            print(f"  OK: {p}")
    
    if all_exist:
        print("\nAll directories verified successfully.")
    else:
        print("\nVerification failed.")
        exit(1)

if __name__ == "__main__":
    main()
