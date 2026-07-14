"""
Script to initialize the project directory structure for T001.
Creates required directories and __init__.py files.
"""
import os
import sys

def main():
    # Define the relative paths based on the project structure
    # Root directories
    dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "docs"
    ]

    # Python package directories requiring __init__.py
    packages = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]

    # Create directories
    print("Creating project directories...")
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  Created: {d}/")

    # Create __init__.py files
    print("Creating __init__.py files...")
    for pkg in packages:
        file_path = os.path.join(pkg, "__init__.py")
        # Check if file already exists to avoid overwriting with empty content if it had code
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write('"""\n' + f"{pkg.replace('/', ' ').title()} package\n" + '"""\n')
            print(f"  Created: {file_path}")
        else:
            print(f"  Skipped (exists): {file_path}")

    print("Setup complete.")

if __name__ == "__main__":
    main()