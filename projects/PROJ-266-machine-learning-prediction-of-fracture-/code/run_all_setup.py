"""
Convenience script to run all setup tasks (T001a, T001b, T001c) in sequence.
Ensures the full directory structure is created for the project.
"""
import os
import sys

# Add project root to path to import code modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.create_project_dirs import main as create_code_dirs
from code.data.create_data_dirs import main as create_data_dirs
from code.data.create_test_dirs import main as create_test_dirs

def main():
    print("=" * 60)
    print("Running Project Setup Tasks (T001a, T001b, T001c)")
    print("=" * 60)

    print("\n[Task T001a] Creating code directories...")
    create_code_dirs()

    print("\n[Task T001b] Creating data directories...")
    create_data_dirs()

    print("\n[Task T001c] Creating test directories...")
    create_test_dirs()

    print("\n" + "=" * 60)
    print("Setup complete. Verifying directory structure...")
    print("=" * 60)

    required_dirs = [
        "code", "code/data", "code/models", "code/train", "code/explain",
        "data", "data/raw", "data/processed", "data/explainability",
        "tests", "tests/unit", "tests/contract", "tests/integration"
    ]

    all_exist = True
    for d in required_dirs:
        exists = os.path.isdir(d)
        status = "✓" if exists else "✗"
        print(f"  {status} {d}")
        if not exists:
            all_exist = False

    if all_exist:
        print("\nAll required directories created successfully.")
        return 0
    else:
        print("\nERROR: Some directories were not created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
