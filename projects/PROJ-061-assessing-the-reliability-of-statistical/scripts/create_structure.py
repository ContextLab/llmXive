"""
Script to create the required directory structure and __init__.py files.
This script ensures the project tree is correctly initialized for T009.
"""
import os
import sys

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define the required structure
    # Format: (relative_path, is_dir, needs_init)
    structure = [
        ("code", True, True),
        ("tests", True, True),
        ("tests/unit", True, True),
        ("tests/integration", True, True),
        ("tests/contract", True, True),
        ("data/raw", True, False),
        ("data/processed", True, False),
        ("data/results", True, False),
        ("docs", True, False),
    ]

    created_count = 0
    init_count = 0

    for rel_path, is_dir, needs_init in structure:
        full_path = os.path.join(root, rel_path)
        
        if is_dir:
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                created_count += 1
                print(f"Created directory: {rel_path}")
            else:
                print(f"Directory exists: {rel_path}")
        
        if needs_init:
            init_file = os.path.join(full_path, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write(f'"""{rel_path.replace("/", " ").title()} package."""\n')
                init_count += 1
                print(f"Created __init__.py: {rel_path}/__init__.py")
            else:
                print(f"__init__.py exists: {rel_path}/__init__.py")
        
        # Add .gitkeep for data directories to ensure they are tracked in git
        if rel_path.startswith("data/"):
            gitkeep = os.path.join(full_path, ".gitkeep")
            if not os.path.exists(gitkeep):
                with open(gitkeep, "w", encoding="utf-8") as f:
                    f.write("# Placeholder to ensure directory exists\n")
                print(f"Created .gitkeep: {rel_path}/.gitkeep")

    print(f"\nSummary: Created {created_count} directories, {init_count} __init__.py files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())