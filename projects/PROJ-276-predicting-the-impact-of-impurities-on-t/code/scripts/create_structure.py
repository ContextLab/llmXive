import os
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in T001.
    Prints the resulting tree structure to stdout for verification.
    """
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")

    # Define the required directories relative to project root
    dirs_to_create = [
        "src/ingestion",
        "src/modeling",
        "src/visualization",
        "src/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "docs"
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Exists:  {full_path.relative_to(project_root)}")

    print(f"\nTotal directories created/verified: {created_count}/{len(dirs_to_create)}")

    # Print final tree structure for verification
    print("\--- Project Structure Verification ---")
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"[OK] {full_path.relative_to(project_root)}")

    if created_count == 0 and all((project_root / d).exists() for d in dirs_to_create):
        print("\nAll required directories are present.")
    elif created_count > 0:
        print("\nNew directories created successfully.")
    else:
        print("\nError: Could not create or verify directories.")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
