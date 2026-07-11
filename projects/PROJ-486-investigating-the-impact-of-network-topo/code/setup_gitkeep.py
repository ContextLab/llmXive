import os
import sys

def initialize_gitkeeps():
    """
    Initialize .gitkeep files in all empty directories defined in the project structure.
    This ensures that empty directories are tracked by Git.
    """
    base_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/visualizations",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0

    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            print(f"Warning: Directory {dir_path} does not exist. Skipping .gitkeep creation.")
            continue

        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            # Create an empty .gitkeep file
            with open(gitkeep_path, "w") as f:
                f.write("")
            print(f"Created .gitkeep in {dir_path}")
            created_count += 1
        else:
            print(f".gitkeep already exists in {dir_path}")

    print(f"Initialization complete. Created {created_count} new .gitkeep files.")
    return created_count

if __name__ == "__main__":
    initialize_gitkeeps()
