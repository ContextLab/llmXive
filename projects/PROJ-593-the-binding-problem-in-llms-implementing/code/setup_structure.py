"""
Setup script to initialize project directory structure.
This script ensures all required directories exist as per the implementation plan.
"""
import os
from pathlib import Path

def create_directories():
    base_dir = Path(__file__).parent
    directories = [
        "src",
        "src/data",
        "src/models",
        "src/analysis",
        "src/benchmarks",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data",
        "data/raw",
        "data/processed",
        "data/final",
        "data/synthetic",
        "config",
        "plots",
        "figures",
        "docs",
        "docs/traceability"
    ]

    created = []
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory exists: {dir_path}")

    if not created:
        print("\nAll required directories already exist.")
    else:
        print(f"\nSuccessfully created {len(created)} directories.")

    # Create placeholder README in src if empty
    src_readme = base_dir / "src" / "README.md"
    if not src_readme.exists():
        src_readme.write_text("# Source Code\n\nImplementation modules for the binding problem project.")
        print("Created src/README.md")

    # Create placeholder README in tests if empty
    tests_readme = base_dir / "tests" / "README.md"
    if not tests_readme.exists():
        tests_readme.write_text("# Tests\n\nTest suite for the binding problem project.")
        print("Created tests/README.md")

if __name__ == "__main__":
    create_directories()
    print("\nProject structure setup complete.")