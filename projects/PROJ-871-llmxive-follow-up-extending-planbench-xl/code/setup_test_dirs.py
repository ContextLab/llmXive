import os
from pathlib import Path

def main():
    """Create the test directory structure for the llmXive project."""
    project_root = Path(__file__).resolve().parent.parent
    tests_base = project_root / "tests"
    
    dirs_to_create = [
        tests_base,
        tests_base / "unit",
        tests_base / "integration",
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files to make them proper Python packages
    for dir_path in dirs_to_create:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# llmXive test package\n")
            print(f"Created __init__.py: {init_file}")

if __name__ == "__main__":
    main()
