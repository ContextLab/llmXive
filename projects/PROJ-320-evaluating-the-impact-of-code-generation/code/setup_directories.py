"""
Script to create the project directory structure and initialize Python packages.
This implements Task T001a.
"""
import os
from pathlib import Path

def create_directories():
    """Create all required project directories and __init__.py files."""
    base_path = Path(".")
    
    # Define directories to create
    directories = [
        "code",
        "code/data",
        "code/analysis",
        "code/audit",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "reports/figures"
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Define __init__.py files to create
    init_files = [
        "code/__init__.py",
        "code/data/__init__.py",
        "code/analysis/__init__.py",
        "code/audit/__init__.py",
        "code/utils/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]
    
    # Create __init__.py files with appropriate content
    init_content_template = '"""{module_description}."""\n'
    
    init_contents = {
        "code/__init__.py": "Root package for llmXive research code.",
        "code/data/__init__.py": "Data acquisition and processing module.",
        "code/analysis/__init__.py": "Analysis and statistical testing module.",
        "code/audit/__init__.py": "Audit and validation module.",
        "code/utils/__init__.py": "Utility functions and shared infrastructure.",
        "tests/unit/__init__.py": "Unit tests package.",
        "tests/integration/__init__.py": "Integration tests package."
    }
    
    for file_path in init_files:
        full_path = base_path / file_path
        if not full_path.exists():
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(init_content_template.format(module_description=init_contents[file_path]))
            print(f"Created file: {full_path}")
        else:
            print(f"File already exists: {full_path}")
    
    print("Directory structure setup complete.")

def main():
    """Entry point for the script."""
    create_directories()

if __name__ == "__main__":
    main()
