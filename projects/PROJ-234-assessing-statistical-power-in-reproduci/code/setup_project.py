import os
from pathlib import Path

def main():
    """
    Creates the project directory tree and placeholder .gitkeep files
    as specified in task T001.
    """
    # Define the required directory structure relative to project root.
    # Keys are directory names, values are nested structures or None for files.
    structure = {
        "code": {
            "utils": {},
            "__init__.py": None, # File
        },
        "data": {
            "raw": {},
            "processed": {},
        },
        "tests": {
            "unit": {},
            "integration": {},
        },
        "docs": {},
        "contracts": {},
    }

    def create_recursive(base_path, tree):
        for name, content in tree.items():
            path = base_path / name
            if content is None:
                # Create file
                path.touch()
                print(f"Created file: {path}")
            elif isinstance(content, dict):
                # Create directory
                path.mkdir(parents=True, exist_ok=True)
                # Create .gitkeep in every directory
                (path / ".gitkeep").touch()
                print(f"Created directory and .gitkeep: {path}")
                # Recurse into subdirectories
                create_recursive(path, content)

    print("Initializing project directory tree...")
    create_recursive(Path("."), structure)
    print("Project scaffolding complete.")

if __name__ == "__main__":
    main()