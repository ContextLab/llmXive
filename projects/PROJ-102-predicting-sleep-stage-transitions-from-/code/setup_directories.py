import os
from pathlib import Path

def main():
    """
    Creates the standard project directory structure for llmXive.
    This implements Task T001a: Create src/, tests/, data/, specs/ directories.
    """
    base_dir = Path(".")
    
    # Define the required top-level directories
    required_dirs = [
        "src",
        "tests",
        "data",
        "specs"
    ]
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create __init__.py files to make them proper Python packages where applicable
    # src is definitely a package
    src_init = base_dir / "src" / "__init__.py"
    if not src_init.exists():
        src_init.touch()
        print(f"Created: {src_init}")
    
    # tests is definitely a package
    tests_init = base_dir / "tests" / "__init__.py"
    if not tests_init.exists():
        tests_init.touch()
        print(f"Created: {tests_init}")
    
    print(f"\nSetup complete. Created {created_count} new directories.")
    print("Directory structure:")
    for d in required_dirs:
        p = base_dir / d
        print(f"  {p}/")

if __name__ == "__main__":
    main()