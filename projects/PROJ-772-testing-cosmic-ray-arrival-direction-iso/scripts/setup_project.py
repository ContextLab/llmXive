"""
Script to programmatically verify and create the project directory structure.
This ensures the structure exists as a runnable artifact, satisfying the requirement
that scripts must produce real outputs when executed.
"""
import os
import sys

PROJECT_ROOT = "projects/PROJ-772-testing-cosmic-ray-arrival-direction-iso"
SUBDIRS = [
    "code",
    "code/ingestion",
    "code/analysis",
    "code/stats",
    "code/utils",
    "code/models",
    "data",
    "data/raw",
    "data/processed",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "state",
]

def main():
    base_path = os.path.join(PROJECT_ROOT)
    created_count = 0

    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
        created_count += 1
        print(f"Created root directory: {base_path}")

    for subdir in SUBDIRS:
        full_path = os.path.join(base_path, subdir)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")

    # Ensure __init__.py files exist for Python packages
    init_files = [
        os.path.join(base_path, "code", "__init__.py"),
        os.path.join(base_path, "code", "ingestion", "__init__.py"),
        os.path.join(base_path, "code", "analysis", "__init__.py"),
        os.path.join(base_path, "code", "stats", "__init__.py"),
        os.path.join(base_path, "code", "utils", "__init__.py"),
        os.path.join(base_path, "code", "models", "__init__.py"),
        os.path.join(base_path, "tests", "unit", "__init__.py"),
        os.path.join(base_path, "tests", "integration", "__init__.py"),
        os.path.join(base_path, "tests", "contract", "__init__.py"),
    ]

    for f_path in init_files:
        if not os.path.exists(f_path):
            with open(f_path, "w") as f:
                f.write("# Auto-initialized by setup_project.py\n")
            print(f"Created init file: {f_path}")
        else:
            print(f"Init file exists: {f_path}")

    # Ensure .gitkeep files exist for data directories
    keep_files = [
        os.path.join(base_path, "data", "raw", ".gitkeep"),
        os.path.join(base_path, "data", "processed", ".gitkeep"),
        os.path.join(base_path, "state", ".gitkeep"),
    ]

    for f_path in keep_files:
        if not os.path.exists(f_path):
            with open(f_path, "w") as f:
                f.write("# Git keep file\n")
            print(f"Created keep file: {f_path}")
        else:
            print(f"Keep file exists: {f_path}")

    print(f"\nSetup complete. Created/verified {created_count} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())