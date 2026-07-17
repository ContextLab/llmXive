"""
Script to create the required directory structure for the llmXive project.
Creates 'code/' with subdirectories and 'tests/' with subdirectories as specified.
"""
import os
from pathlib import Path

def create_directories():
    """Create the project directory structure."""
    # Define the base project root (assumed to be the parent of this script's location)
    # or explicitly relative to the current working directory if run from root.
    # We will create directories relative to the current working directory.
    base_path = Path.cwd()

    # Define the required directories under 'code/'
    code_dirs = [
        "code/data_generation",
        "code/model_training",
        "code/simulation",
        "code/analysis",
        "code/tests", # This acts as a container for the test subdirs
    ]

    # Define the required directories under 'tests/' (as per task T001c requirement, though T001a focuses on code/)
    # The task T001a specifically asks for 'code/' structure and 'tests/' inside it?
    # Re-reading T001a: "Create `code/` directory structure (`data_generation`, `model_training`, `simulation`, `analysis`, `tests/`)"
    # This implies the tests folder should be inside code/ OR the task description lists the subfolders of code/ AND tests/ as a group.
    # Looking at T001c: "Create `tests/` directory structure (`test_data_generation`, `test_model_training`, `test_simulation`)"
    # Standard Python project structure usually has tests/ at root.
    # However, the task T001a explicitly lists `tests/` as a subdirectory of `code/` in the parenthetical list.
    # But T001c says "Create `tests/` directory structure" implying a root level tests/.
    # Let's look at the existing API surface provided in the prompt:
    # `code/tests/conftest.py` exists in the API surface list.
    # `code/tests/test_data_generation/test_checksum.py` exists.
    # This confirms the project structure places tests INSIDE the code/ directory.
    # Therefore, T001a creates code/ and its subdirs including tests/.
    # T001c will then populate the subdirs inside code/tests/.

    # Subdirectories for code/tests/
    test_subdirs = [
        "code/tests/test_data_generation",
        "code/tests/test_model_training",
        "code/tests/test_simulation"
    ]

    all_dirs = code_dirs + test_subdirs

    created_count = 0
    for dir_path in all_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    return created_count

def main():
    """Entry point for the script."""
    print("Starting directory structure setup...")
    count = create_directories()
    print(f"Setup complete. Created {count} new directories.")

if __name__ == "__main__":
    main()