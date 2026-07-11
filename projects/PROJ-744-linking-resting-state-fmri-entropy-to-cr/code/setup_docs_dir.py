import os
import sys
from pathlib import Path

def create_directory(path: str) -> bool:
    """
    Create a directory at the specified path if it does not exist.
    
    Args:
        path: The path to the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    dir_path = Path(path)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create a placeholder README.md to ensure the directory is not ignored
        readme_path = dir_path / "README.md"
        if not readme_path.exists():
            readme_path.write_text(
                "# Project Documentation\n\n"
                "This directory contains project documentation, "
                "design documents, and research notes.\n"
            )
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """Main entry point to create the docs directory."""
    docs_dir = "docs"
    print(f"Creating directory: {docs_dir}")
    if create_directory(docs_dir):
        print(f"Successfully created or verified existence of: {docs_dir}")
        # List contents to provide evidence
        if os.path.exists(docs_dir):
            print(f"Contents of {docs_dir}:")
            for item in os.listdir(docs_dir):
                print(f"  - {item}")
    else:
        print(f"Failed to create directory: {docs_dir}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()