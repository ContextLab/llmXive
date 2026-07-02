import os
import sys

def create_directories():
    """
    Creates the project directory structure as defined in the implementation plan.
    Directories created:
    - code/data
    - code/analysis
    - code/utils
    - tests/contract
    - tests/integration
    - tests/unit
    - data/raw
    - data/processed
    - data/derived
    - state/projects
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_path)

    directories = [
        "code/data",
        "code/analysis",
        "code/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "data/derived",
        "state/projects"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(root_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Project structure initialization complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
