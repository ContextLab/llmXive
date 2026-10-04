"""
Setup script to create the docs/ directory structure.
This script ensures all required documentation directories exist.
"""
import os
from pathlib import Path
import sys

# Add the project root to the path to allow importing config if needed
# though for this simple task we can use relative paths directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCS_DIR = PROJECT_ROOT / "docs"

SUBDIRECTORIES = [
    "api",
    "design",
    "development",
    "user_guides",
    "reports",
    "specs",
]

def create_docs_structure():
    """Create the docs/ directory and its subdirectories."""
    print(f"Ensuring docs structure exists at: {DOCS_DIR}")
    
    # Create the main docs directory
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    created_dirs = []
    for subdir in SUBDIRECTORIES:
        dir_path = DOCS_DIR / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(dir_path)
        print(f"  - Created/Verified: {dir_path}")

    # Create a README.md in the docs root if it doesn't exist
    readme_path = DOCS_DIR / "README.md"
    if not readme_path.exists():
        readme_content = """# Documentation

This directory contains all project documentation.

## Structure

- **api/**: API reference documentation
- **design/**: Design documents and architecture decisions
- **development/**: Development guides and setup instructions
- **user_guides/**: User guides and tutorials
- **reports/**: Generated reports and analysis results
- **specs/**: Feature specifications and requirements

## Generating Documentation

Run the setup script to ensure directory structure:
```bash
python code/setup_docs.py
```
"""
        readme_path.write_text(readme_content)
        print(f"  - Created: {readme_path}")
    else:
        print(f"  - Exists: {readme_path}")

    print("Docs directory structure is ready.")
    return True

def main():
    """Entry point for the script."""
    try:
        create_docs_structure()
        return 0
    except Exception as e:
        print(f"Error creating docs structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())