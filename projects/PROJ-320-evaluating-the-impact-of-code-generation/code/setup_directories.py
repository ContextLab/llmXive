"""
Script to initialize the project directory structure for the llmXive pipeline.
Creates all required folders for code organization, data storage, testing, and reporting.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    root = Path(".")
    
    # Define all required directories relative to the project root
    directories = [
        # Code structure
        "code",
        "code/data",
        "code/analysis",
        "code/audit",
        "code/utils",
        
        # Data storage
        "data/raw",
        "data/processed",
        
        # Testing
        "tests/unit",
        "tests/integration",
        
        # Reporting
        "reports/figures",
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                created_count += 1
                print(f"Created directory: {dir_path}")
            else:
                print(f"Error: {dir_path} exists but is not a directory")
        except PermissionError:
            print(f"Permission denied creating: {dir_path}")
        except Exception as e:
            print(f"Error creating {dir_path}: {e}")
    
    print(f"\nDirectory setup complete: {created_count} created, {skipped_count} skipped")

if __name__ == "__main__":
    main()