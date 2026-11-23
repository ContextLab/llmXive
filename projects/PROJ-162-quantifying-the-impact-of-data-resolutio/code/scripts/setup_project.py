import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as specified in T001.
    Directories created:
    - src
    - tests
    - data/raw
    - data/processed
    - data/profiling
    - contracts
    - state
    """
    # Define the project root (assumed to be the parent of 'scripts')
    # However, standard practice for this project seems to be running from root.
    # We will resolve paths relative to the current working directory.
    root = Path.cwd()

    # Define relative paths based on T001 requirement
    # Note: The task mentions 'src', but the existing API surface shows 'code/src'.
    # The task description says "Create project structure per implementation plan: mkdir -p src tests..."
    # However, the existing files are under 'code/'.
    # To ensure consistency with the existing API surface provided in the prompt (which uses 'code/'),
    # we will create the directories under 'code/' if 'code' exists, or at root if not.
    # Given the prompt says "Existing project API surface... code/src/config.py", the project root is likely the repo root,
    # and the structure is under 'code/'.
    # BUT, the task T001 explicitly says: "mkdir -p src tests data/raw...".
    # Let's look at the "Path Conventions" in tasks.md: "Single project: src/, tests/ at repository root".
    # This contradicts the "Existing project API surface" which shows 'code/'.
    # Since T001 is the task to CREATE the structure, and the prompt says "Existing project API surface" includes 'code/',
    # it implies the structure *should* be 'code/'.
    # However, the task text literally says "mkdir -p src tests...".
    # Let's assume the task description in tasks.md might be a template or slightly outdated regarding the 'code/' prefix,
    # but the *intent* is the directories listed.
    # The safest bet that satisfies "Create project structure" and aligns with the *existing* files (which are in code/)
    # is to create them under 'code/'.
    # Wait, if I create them at root, they won't match the existing API surface paths (code/src).
    # If I create them under code/, they match.
    # The task T001 text: "Create project structure per implementation plan: mkdir -p src tests data/raw data/processed data/profiling contracts state".
    # The "Path Conventions" section says: "Single project: src/, tests/ at repository root".
    # The "Existing project API surface" says: "code/src/config.py".
    # This is a conflict. The prompt says "You are an LLM-driven implementer... Implement the task...".
    # If I create 'src' at root, I break the existing API surface paths (which assume 'code/src').
    # If I create 'code/src', I satisfy the existing API surface but technically deviate from the literal "mkdir -p src".
    # However, the "implementation plan" mentioned in T001 likely refers to the *actual* plan which established the 'code/' prefix.
    # I will create the directories under `code/` to ensure the project structure matches the existing API surface (code/src, code/tests, etc.).
    # The directories to create are:
    # code/src (already exists? prompt says "Existing... code/src/config.py", so yes, but we ensure it)
    # code/tests (already exists)
    # code/data/raw
    # code/data/processed
    # code/data/profiling
    # code/contracts
    # code/state

    base_dir = root / "code"
    if not base_dir.exists():
        base_dir.mkdir(parents=True)

    dirs_to_create = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/profiling",
        "contracts",
        "state"
    ]

    created_count = 0
    for d in dirs_to_create:
        full_path = base_dir / d
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())