"""
T001: Create project structure per plan.md.
Creates the required directory hierarchy for the cortical column LLM project.
"""
import os
import sys

def main():
    # Define the root project directory relative to the script location
    # The script is in code/, so root is one level up
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define the required directories relative to the root
    # Based on tasks.md: "directories: `src/models`, `src/data`, `src/training`, `src/experiments`, `tests`"
    # Note: The prompt mentions `src/` in Path Conventions, but tasks.md explicitly lists `src/...`
    # We will create `src` and `tests` at the root level as per standard Python project layout
    # and the specific task description.
    
    directories = [
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "src/utils",
        "src/experiments",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "figures",
        "scripts",
        "docs",
        "configs",
        "state"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(root_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # Optional: check if it's a file, if so, error out
            if os.path.isfile(full_path):
                print(f"Error: Path exists but is a file: {full_path}", file=sys.stderr)
                sys.exit(1)
            # print(f"Directory already exists: {full_path}")

    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    print(f"Root directory: {root_dir}")

if __name__ == "__main__":
    main()