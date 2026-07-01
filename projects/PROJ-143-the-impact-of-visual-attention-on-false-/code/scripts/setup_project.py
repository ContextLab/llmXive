import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as per the implementation plan.
    Directories created:
      - src/
      - tests/
      - data/raw
      - data/processed
    """
    # Define the project root based on the file's location context or current working dir
    # Assuming this script runs from the project root or 'code' subfolder.
    # We will create structure relative to the current working directory.
    project_root = Path.cwd()
    
    # Define required directories relative to project root
    # The task specifies: src/, tests/, data/raw, data/processed
    # However, looking at the existing API surface, files are in 'code/' (e.g., code/src, code/tests).
    # To be consistent with the existing project API surface provided in the prompt
    # (which shows files like code/src/analysis/metrics.py), we must create the structure
    # under 'code/' if that is the established root, OR create at root if 'code' is the root.
    # The prompt says: "All artifact paths are relative to the project root and MUST live under code/, data/, tests/..."
    # But the existing files are explicitly listed as `code/src/...`.
    # The task description says: "Create project structure... (`src/`, `tests/`, `data/raw`, `data/processed`)"
    # This implies the structure should be at the root where the script runs.
    # However, the existing files provided in the prompt are under `code/`.
    # To ensure compatibility with the existing API surface (which imports from `src` and `tests` but the files are in `code/src`),
    # we must create the directories exactly where the existing files expect them to be.
    # The existing files are: code/src/..., code/tests/...
    # This implies the "project root" for the Python execution context is the `code` directory,
    # OR the `src` and `tests` directories are expected to be at the same level as this script.
    # Given the instruction "All artifact paths are relative to the project root", and the existing files are in `code/`,
    # it is safest to create the structure inside `code/` to match the existing file paths (e.g. code/src).
    # BUT, the task description explicitly lists `src/`, `tests/` (without `code/` prefix).
    # Let's look at the "Existing project API surface":
    # `code/src/analysis/metrics.py` exists.
    # `code/tests/test_config.py` exists.
    # This means the directories `src` and `tests` already exist inside `code`.
    # The task T001 asks to "Create project structure". Since they seem to exist in the prompt's context,
    # we will ensure they exist and also create the `data` subdirectories which are missing.
    # We will run this relative to the directory where this script is located (assuming it's the project root).
    
    base_dir = Path(__file__).parent.parent  # Assuming script is in code/scripts/
    # If the script is run from root, __file__ is code/scripts/setup_project.py
    # So base_dir becomes code/.
    
    # If the script is run from root and placed directly in root, base_dir is root.
    # Let's check if we are in `code` or root.
    # The prompt says "All artifact paths are relative to the project root".
    # The existing files are listed as `code/src/...`.
    # This implies the project root is the parent of `code`.
    # But the task T001 says create `src/`, `tests/`.
    # If the project root is parent of `code`, then `src/` would be at root, but existing files are at `code/src/`.
    # This is a contradiction in the prompt's description vs the existing file list.
    # Resolution: The existing file list `code/src/...` suggests the working directory for the project IS `code`.
    # OR the `code` folder is the project root.
    # Let's assume the current working directory is the project root and the existing files are just listed with a prefix for clarity in the prompt,
    # OR we must create `src` and `tests` inside the current directory.
    # Given the existing files are `code/src/...`, and the task asks for `src/`, `tests/`, `data/raw`, `data/processed`.
    # We will create `src`, `tests`, `data/raw`, `data/processed` in the current working directory.
    # If the existing files are actually at `code/src`, then we are creating a duplicate structure or the prompt's `code/` prefix is the root.
    # Let's assume the project root is the directory containing `scripts`.
    # So we create `src`, `tests`, `data` relative to `scripts`'s parent.
    
    # Actually, looking at the prompt: "All artifact paths are relative to the project root and MUST live under code/, data/, tests/..."
    # This implies the project root is the parent of `code`, `data`, `tests`.
    # But the existing files are `code/src/...`.
    # If the project root is parent of `code`, then `src` is inside `code`.
    # The task T001 asks to create `src/`, `tests/`, `data/raw`, `data/processed`.
    # This phrasing usually implies these are at the project root.
    # If the project root is the parent of `code`, then `src` would be at `PROJECT_ROOT/src`.
    # But the existing files are at `PROJECT_ROOT/code/src`.
    # This suggests the "project root" for the purpose of this task is the `code` directory itself.
    # Let's assume the current working directory IS the `code` directory (or the script is run from there).
    # We will create the directories relative to the script's parent (which is `code`).
    
    base_path = Path(__file__).resolve().parent.parent
    
    dirs_to_create = [
        base_path / "src",
        base_path / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "processed"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} directories.")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())