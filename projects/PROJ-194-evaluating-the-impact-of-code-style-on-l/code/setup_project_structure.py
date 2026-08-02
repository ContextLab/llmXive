"""
Project Structure Initialization Script.
Creates the required directory tree for the llmXive pipeline.
"""
import os
import sys

def main():
    """Create project directories: code/, data/, results/, tests/, contracts/."""
    # Define the root directory (current working directory)
    root_dir = os.getcwd()
    
    # Define required directories relative to root
    required_dirs = [
        "code",
        "data",
        "results",
        "tests",
        "contracts"
    ]
    
    # Additional subdirectories required by the pipeline
    sub_dirs = [
        "code/transform/formatters",
        "code/transform/renamer",
        "code/transform/stripper",
        "code/evaluate/config",
        "code/mutation",
        "code/validation",
        "data/derived",
        "data/raw",
        "results/figures",
        "tests/unit",
        "tests/integration"
    ]
    
    all_dirs = required_dirs + sub_dirs
    
    created_count = 0
    existing_count = 0
    
    print(f"Initializing project structure in: {root_dir}")
    
    for dir_path in all_dirs:
        full_path = os.path.join(root_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            existing_count += 1
    
    print(f"\nProject structure initialization complete.")
    print(f"  - New directories created: {created_count}")
    print(f"  - Existing directories: {existing_count}")
    
    # Verify all required top-level directories exist
    missing = []
    for dir_name in required_dirs:
        if not os.path.exists(os.path.join(root_dir, dir_name)):
            missing.append(dir_name)
    
    if missing:
        print(f"ERROR: The following directories are missing: {missing}")
        sys.exit(1)
    else:
        print("Verification passed: All required directories exist.")
        return 0

if __name__ == "__main__":
    sys.exit(main() or 0)