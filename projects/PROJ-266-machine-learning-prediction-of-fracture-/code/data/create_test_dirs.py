import os
import sys

def main():
    """Create the test directory structure for the project."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(base_dir)
    
    test_dirs = [
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration"
    ]
    
    created = []
    for d in test_dirs:
        full_path = os.path.join(project_root, d)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created.append(d)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")
    
    # Create __init__.py files to make them Python packages
    init_files = []
    for d in test_dirs:
        init_path = os.path.join(project_root, d, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write("")
            init_files.append(d)
            print(f"Created __init__.py in: {d}")
    
    if not created and not init_files:
        print("All test directories and __init__.py files already exist.")
    else:
        print("\nTest directory structure setup complete.")

if __name__ == "__main__":
    main()
