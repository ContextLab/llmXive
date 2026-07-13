"""
Project setup script for PROJ-867.
Creates the required directory structure: code/, data/, tests/, docs/.
"""
import os
import sys

PROJECT_ROOT = "projects/PROJ-867-llmxive-follow-up-extending-representati"
SUBDIRS = ["code", "data", "tests", "docs"]

def main():
    base_path = os.path.join(PROJECT_ROOT)
    
    # Ensure the base project directory exists
    os.makedirs(base_path, exist_ok=True)
    print(f"Base directory created/exists: {base_path}")

    created_dirs = []
    for subdir in SUBDIRS:
        dir_path = os.path.join(base_path, subdir)
        os.makedirs(dir_path, exist_ok=True)
        created_dirs.append(dir_path)
        print(f"Directory created: {dir_path}")

    # Create empty __init__.py files to make tests a package
    init_path = os.path.join(base_path, "tests", "__init__.py")
    with open(init_path, "w") as f:
        f.write("")
    print(f"Created package marker: {init_path}")

    # Create empty requirements.txt placeholder
    req_path = os.path.join(base_path, "code", "requirements.txt")
    if not os.path.exists(req_path):
        with open(req_path, "w") as f:
            f.write("# Dependencies will be added by T001b\n")
        print(f"Created placeholder: {req_path}")

    print("Project structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
