import os
import sys
from pathlib import Path

# Define the required directory structure relative to the project root
# The project root is assumed to be the parent of the 'code' directory
# based on the task description "paths are relative to the project root"
# and the artifact path "code/scripts/setup_data_dirs.py".

# However, looking at the existing API surface, there is also a 
# code/setup_data_dirs.py and code/setup_project_structure.py.
# The task T004 specifically asks to "Setup data directory structure".
# We will implement the function to create the specific directories
# required by T004: data/raw/, data/derived/, data/gold_standard/, artifacts/.

# We assume the script is run from the project root or the code directory.
# To be safe and consistent with the "project root" convention in tasks.md:
# If the script is in code/scripts/, the project root is likely code/../
# But often in these pipelines, the "project root" for the code is the 'code' directory itself
# or the root of the repo.
# Let's assume the standard convention: The script is executed from the project root.
# If not, we can try to locate the 'data' directory relative to the script.

# Let's define the directories to be created.
# The task says: `data/raw/`, `data/derived/`, `data/gold_standard/`, `artifacts/`.
# These are relative to the project root.

REQUIRED_DIRS = [
    "data/raw",
    "data/derived",
    "data/gold_standard",
    "artifacts"
]

def setup_directories(root_path: Path = None) -> list:
    """
    Creates the required data directory structure.
    
    Args:
        root_path: The project root path. If None, defaults to the current working directory.
                   If the script is run from code/scripts/, we might need to adjust.
                   We will default to current working directory (cwd) as the project root.
    
    Returns:
        A list of created directory paths (as strings).
    """
    if root_path is None:
        root_path = Path.cwd()
    
    created_dirs = []
    
    for dir_name in REQUIRED_DIRS:
        full_path = root_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            raise
    
    return created_dirs

def main():
    """
    Main entry point for the script.
    """
    print("Setting up data directory structure...")
    # Determine project root. 
    # If run as `python code/scripts/setup_data_dirs.py`, cwd is likely project root.
    # If run as `python setup_data_dirs.py` from code/, cwd is code/.
    # The task says paths are relative to project root.
    # Let's assume cwd is the project root.
    project_root = Path.cwd()
    
    # Check if we are inside the 'code' directory and adjust if necessary
    # to ensure we are creating directories relative to the actual project root.
    # If the script is in code/scripts/, and we are running from project root,
    # then project_root is correct.
    # If the script is run from code/, then project_root is code/, which is fine
    # if the data directories are expected there.
    # However, tasks.md says "paths are relative to the project root" and lists
    # "data/raw/". If the project structure is:
    # <root>/
    #   data/
    #   code/
    #   ...
    # Then running from <root> is correct.
    
    # Let's try to detect if we are in a 'code' subdirectory and adjust.
    # If the current working directory ends with 'code', maybe the project root is one level up?
    # But the task T001 says "Create project structure per implementation plan (src/, tests/, data/, specs/001-gene-regulation/)".
    # This implies data/ is at the same level as src/ (which is inside code/ in the artifact paths).
    # Wait, the artifact paths are like `code/src/...`. This suggests the project root is the repo root,
    # and `code/` is a subdirectory containing the source.
    # So `data/` should be at the repo root.
    # If I run this script from `code/scripts/`, the cwd is `code/scripts/`.
    # I need to go up two levels to get to repo root? Or is `code/` the project root for the python app?
    # Let's look at T001 again: "Create project structure ... (src/, tests/, data/, specs/...)".
    # The artifact paths show `code/src/`, `code/tests/`.
    # This is slightly ambiguous. Is `code/` the project root for the python code, or is the repo root the project root?
    # If repo root is project root, then data/ is at repo root.
    # If code/ is project root, then data/ is at code/data/.
    # Let's assume the standard convention where the "project root" for the python app is the directory
    # containing `src/`, `tests/`, `data/`, etc.
    # In the artifact paths, we see `code/src/`. This implies `code/` might be a container.
    # However, T001 says "Create project structure ... (src/, tests/, data/, ...)".
    # If the structure is `code/src/`, then `src/` is inside `code/`.
    # So `data/` should be inside `code/`? Or at the repo root?
    # Let's look at the task description for T004: "Setup data directory structure (data/raw/, ...)".
    # And the existing script `code/setup_data_dirs.py` (note: no scripts/ subfolder in the filename in the list, but in the task it's `code/scripts/setup_data_dirs.py`).
    # Actually, the API surface lists:
    # `code/scripts/setup_data_dirs.py` and `code/setup_data_dirs.py`.
    # This suggests there might be two files or a confusion.
    # Let's assume the project root is the directory where `data/` should reside.
    # Given the artifact paths `code/src/...`, it's highly likely `code/` is the root of the Python project.
    # So `data/` should be `code/data/`.
    # Let's verify with T001: "Create project structure ... (src/, tests/, data/, ...)".
    # If the project root is `code/`, then `code/src/`, `code/tests/`, `code/data/`.
    # This matches the artifact paths `code/src/...`, `code/tests/...`.
    # So we will create directories relative to the current working directory, assuming cwd is `code/` or the project root.
    # To be robust, we can check if `src/` exists in cwd. If not, maybe we are in the repo root and `code/` is a subdir.
    # But T001 says "Create project structure ... (src/, tests/, data/, ...)".
    # If I am in repo root, and I create `src/`, `tests/`, `data/`, then `code/` is not involved.
    # But the artifacts are under `code/`.
    # This implies the "project root" for the python code is `code/`.
    # So we will create `data/` relative to the directory containing `src/`.
    
    # Let's try to find the project root by looking for `src/` or `tests/`.
    cwd = Path.cwd()
    project_root = cwd
    
    # If cwd doesn't have `src/` or `tests/`, maybe we are in the repo root and `code/` is the project root?
    # But the script is in `code/scripts/`. If I run `python code/scripts/setup_data_dirs.py` from repo root,
    # cwd is repo root. Then `src/` is not there, `code/src/` is.
    # Let's assume the user runs the script from the project root (which is `code/`).
    # If not, we can add a heuristic.
    
    # Heuristic: If `src/` is not in cwd, but `code/src/` is, then project_root = cwd / `code/`.
    # But wait, the artifact path is `code/scripts/setup_data_dirs.py`.
    # If I run from repo root: `python code/scripts/setup_data_dirs.py`.
    # Then cwd = repo root.
    # If I run from code/: `python scripts/setup_data_dirs.py`.
    # Then cwd = code/.
    
    # Let's assume the "project root" is the directory where `data/` should be created.
    # Based on T001 and artifact paths, `data/` is at the same level as `src/` and `tests/`.
    # And `src/` and `tests/` are inside `code/`.
    # So `data/` should be inside `code/`.
    # Therefore, the project root for this script is the `code/` directory.
    
    # Let's check if we are in a subdirectory of `code/` (e.g., `scripts/`).
    # If cwd is `code/scripts/`, then parent is `code/`.
    # If cwd is `code/`, then parent is `code/`.
    # If cwd is repo root, then `code/` is a child.
    
    # Let's try to locate `src/` directory.
    if not (cwd / "src").exists():
        # Maybe we are in repo root? Check for code/src
        if (cwd / "code" / "src").exists():
            project_root = cwd / "code"
        # Maybe we are in code/scripts? Check parent
        elif (cwd.parent / "src").exists():
            project_root = cwd.parent
        # Maybe we are in code/src? Check grandparent
        elif (cwd.parent.parent / "src").exists():
            project_root = cwd.parent.parent
    
    print(f"Detected project root: {project_root}")
    
    # Now create the directories relative to project_root
    created = setup_directories(project_root)
    print(f"Successfully created directories: {created}")

if __name__ == "__main__":
    main()
