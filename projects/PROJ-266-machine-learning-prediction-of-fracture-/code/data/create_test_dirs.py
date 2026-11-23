import os
import sys

def main():
    """
    Create the test directory structure for the project.
    
    Creates:
      - tests/
      - tests/unit/
      - tests/contract/
      - tests/integration/
    """
    base_dir = "tests"
    subdirs = ["unit", "contract", "integration"]
    
    created = []
    for subdir in subdirs:
        path = os.path.join(base_dir, subdir)
        os.makedirs(path, exist_ok=True)
        created.append(path)
    
    # Ensure the root tests dir exists (os.makedirs with exist_ok=True handles this if subdirs are created)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)
        created.insert(0, base_dir)
    
    print(f"Created test directories:")
    for d in created:
        print(f"  - {d}")
    
    # Create __init__.py files to make them proper Python packages
    for subdir in ["", "unit", "contract", "integration"]:
        path = os.path.join(base_dir, subdir) if subdir else base_dir
        init_file = os.path.join(path, "__init__.py")
        with open(init_file, "w") as f:
            f.write("# Test package\n")
        print(f"Created {init_file}")

if __name__ == "__main__":
    main()
