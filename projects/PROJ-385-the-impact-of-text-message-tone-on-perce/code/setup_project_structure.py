"""
Task T001: Create project structure per implementation plan.
Creates the required directories: code/, data/, tests/, specs/
and their subdirectories as defined in the project plan.
"""
import os
from pathlib import Path
from config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_consent_dir,
    get_specs_dir,
    get_contracts_dir,
    get_code_dir,
    get_tests_dir,
    get_figures_dir
)

def create_directories():
    """
    Creates the full project directory structure.
    """
    project_root = get_project_root()
    print(f"Project root: {project_root}")

    # Core directories
    dirs_to_create = [
        get_code_dir(),
        get_tests_dir(),
        get_specs_dir(),
        get_figures_dir(),
        get_data_dir(),
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
        get_contracts_dir(),
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        path_obj = Path(dir_path)
        if not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
            print(f"Created: {dir_path}")
            created_count += 1
        else:
            print(f"Exists: {dir_path}")

    # Create placeholder __init__.py files for code and tests to make them packages
    code_init = get_code_dir() / "__init__.py"
    tests_init = get_tests_dir() / "__init__.py"
    tests_unit_init = get_tests_dir() / "unit" / "__init__.py"
    tests_integration_init = get_tests_dir() / "integration" / "__init__.py"
    tests_contract_init = get_tests_dir() / "contract" / "__init__.py"

    init_files = [code_init, tests_init, tests_unit_init, tests_integration_init, tests_contract_init]

    for init_file in init_files:
        path_obj = Path(init_file)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        if not path_obj.exists():
            path_obj.touch()
            print(f"Created: {init_file}")
        else:
            print(f"Exists: {init_file}")

    # Create placeholder data files to ensure structure is visible
    # (Optional, but helps verify structure)
    raw_data = get_raw_data_dir()
    processed_data = get_processed_data_dir()
    consent_dir = get_consent_dir()

    # Create .gitkeep files to ensure directories are tracked by git
    gitkeep_files = [
        raw_data / ".gitkeep",
        processed_data / ".gitkeep",
        consent_dir / ".gitkeep",
        get_specs_dir() / ".gitkeep",
        get_contracts_dir() / ".gitkeep",
        get_figures_dir() / ".gitkeep",
    ]

    for gitkeep in gitkeep_files:
        path_obj = Path(gitkeep)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        if not path_obj.exists():
            path_obj.touch()
            print(f"Created: {gitkeep}")
        else:
            print(f"Exists: {gitkeep}")

    print(f"\nTotal directories created: {created_count}")
    print("Project structure setup complete.")

def main():
    """
    Entry point for the script.
    """
    create_directories()

if __name__ == "__main__":
    main()
