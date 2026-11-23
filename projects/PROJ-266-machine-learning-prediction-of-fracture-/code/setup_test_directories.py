import os
import sys

def main():
    """Create the test directory structure for the project."""
    base_dir = "tests"
    dirs = [
        base_dir,
        os.path.join(base_dir, "unit"),
        os.path.join(base_dir, "contract"),
        os.path.join(base_dir, "integration"),
    ]

    created = []
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            created.append(d)
            print(f"Created directory: {d}")
        else:
            print(f"Directory already exists: {d}")

    if not created:
        print("All test directories already exist.")
    
    # Create __init__.py files to make them Python packages
    for d in dirs:
        init_file = os.path.join(d, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Test package\n")
            print(f"Created {init_file}")

    return 0

if __name__ == "__main__":
    sys.exit(main())