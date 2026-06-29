"""
Script to create the code directory structure for PROJ-267.

This script ensures the code/ directory exists with proper Python package
initialization. It is part of the Phase 1 setup tasks.
"""
import os
from pathlib import Path

def ensure_code_directory():
    """Create the code directory if it doesn't exist."""
    code_dir = Path(__file__).parent
    code_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured directory exists: {code_dir}")
    return code_dir

def main():
    """Main entry point for directory creation."""
    code_dir = ensure_code_directory()

    # Create __init__.py if it doesn't exist
    init_file = code_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            '"""PROJ-267 code package."""\n'
            '__version__ = "0.1.0"\n'
        )
        print(f"Created: {init_file}")
    else:
        print(f"Already exists: {init_file}")

    print(f"Code directory setup complete at: {code_dir}")
    return 0

if __name__ == "__main__":
    exit(main())