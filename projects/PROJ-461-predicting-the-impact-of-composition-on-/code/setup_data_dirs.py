"""
Script to setup data directory structure for the project.
Creates data/, models/, and reports/ directories if they don't exist.
"""
import os
from pathlib import Path

def setup_directories():
    """Create the required directory structure."""
    base_dir = Path(__file__).parent.parent
    
    directories = [
        base_dir / "data",
        base_dir / "models",
        base_dir / "reports",
        base_dir / "logs",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "external",
        base_dir / "docs",
        base_dir / "docs" / "deviations",
        base_dir / "docs" / "kickback_requests",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    print("\nDirectory structure setup complete.")

def main():
    """Main entry point."""
    setup_directories()

if __name__ == "__main__":
    main()