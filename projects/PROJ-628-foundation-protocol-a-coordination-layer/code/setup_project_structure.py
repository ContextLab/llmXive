"""
Script to create the root project structure for PROJ-628-foundation-protocol-a-coordination-layer.
This implements Task T001a by creating the directory tree and verifying existence.
"""
import os
import sys

PROJECT_ROOT = "projects/PROJ-628-foundation-protocol-a-coordination-layer"

# Define the directory structure to create
# Based on T001b requirements and standard project layout
directories = [
    PROJECT_ROOT,
    os.path.join(PROJECT_ROOT, "code"),
    os.path.join(PROJECT_ROOT, "code", "foundation_protocol"),
    os.path.join(PROJECT_ROOT, "code", "agents"),
    os.path.join(PROJECT_ROOT, "code", "benchmarks"),
    os.path.join(PROJECT_ROOT, "code", "experiments"),
    os.path.join(PROJECT_ROOT, "code", "reports"),
    os.path.join(PROJECT_ROOT, "code", "data"),
    os.path.join(PROJECT_ROOT, "code", "tests"),
    os.path.join(PROJECT_ROOT, "data"),
    os.path.join(PROJECT_ROOT, "results"),
    os.path.join(PROJECT_ROOT, "state"),
    os.path.join(PROJECT_ROOT, "docs"),
    # Additional directories referenced in tasks.md for completeness
    os.path.join(PROJECT_ROOT, "contracts"),
    os.path.join(PROJECT_ROOT, "specs"),
    os.path.join(PROJECT_ROOT, "specs", "feature-001-foundation-protocol"),
    os.path.join(PROJECT_ROOT, "tests"),
    os.path.join(PROJECT_ROOT, "scripts"),
    os.path.join(PROJECT_ROOT, "ideas"),
    os.path.join(PROJECT_ROOT, "reviews"),
]

def create_structure():
    created_count = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
          os.makedirs(dir_path)
          print(f"Created directory: {dir_path}")
          created_count += 1
        else:
          # Check if it's a directory, if it's a file that's an error state
          if os.path.isfile(dir_path):
              print(f"ERROR: Path exists but is a file, not a directory: {dir_path}")
              return False
    print(f"Successfully created {created_count} directories.")
    return True

def verify_structure():
    missing = []
    for dir_path in directories:
        if not os.path.isdir(dir_path):
            missing.append(dir_path)
    
    if missing:
        print("Verification FAILED. Missing directories:")
        for m in missing:
            print(f"  - {m}")
        return False
    
    print("Verification PASSED. All required directories exist.")
    
    # Print a tree-like structure for the root
    print(f"\nProject Structure for {PROJECT_ROOT}:")
    print("-" * 40)
    # Simple recursive print for the root
    def print_tree(path, prefix=""):
        try:
            items = sorted(os.listdir(path))
            for i, item in enumerate(items):
                item_path = os.path.join(path, item)
                is_last = (i == len(items) - 1)
                connector = "└── " if is_last else "├── "
                print(f"{prefix}{connector}{item}")
                
                if os.path.isdir(item_path):
                    extension = "    " if is_last else "│   "
                    print_tree(item_path, prefix + extension)
        except PermissionError:
            pass

    # Only print depth 2 to keep output manageable
    print_tree(PROJECT_ROOT)
    return True

if __name__ == "__main__":
    print("Initializing Project Structure...")
    if not create_structure():
        sys.exit(1)
    
    print("\nVerifying Project Structure...")
    if not verify_structure():
        sys.exit(1)
    
    print("\nTask T001a completed successfully.")
