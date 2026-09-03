"""
Script to create the project directory structure for llmXive PROJ-276.
This implements Task T001 from tasks.md.
"""
import os
from pathlib import Path

def main():
    # Define the base directory (project root)
    # We assume this script runs from the project root or code/scripts
    # We will create structure relative to the repository root.
    # Since we are in code/scripts, we go up one level.
    base_path = Path(__file__).resolve().parent.parent

    # Define the directories to create as per tasks.md T001
    # Note: The task asks for `src/...` but the existing API surface shows `code/src/...`.
    # The task description says: "Execute: mkdir -p src/ingestion ..."
    # However, the "Existing project API surface" clearly shows files under `code/src/utils/`.
    # To be consistent with the existing project structure shown in the prompt (which is the ground truth),
    # we will create the directories under `code/` to match the existing `code/src`, `code/tests`, etc.
    # If we strictly followed the text "src/..." it would create a new root-level src/ conflicting with code/src/.
    # Given the constraint "Extend, don't re-author" and the existing API surface, we align with `code/`.
    
    directories = [
        "code/src/ingestion",
        "code/src/modeling",
        "code/src/visualization",
        "code/src/utils",
        "code/tests/contract",
        "code/tests/integration",
        "code/tests/unit",
        "code/data/raw",
        "code/data/processed",
        "code/docs",
        # Also create the root-level state directory for T000 (contradictions)
        "state/contradictions"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(base_path)}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path.relative_to(base_path)}")

    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
