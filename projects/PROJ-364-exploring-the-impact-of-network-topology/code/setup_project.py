"""
Project initialization script.
Sets up directory structure and verifies dependencies.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the standard directory structure for the project."""
    base_dirs = [
        "data/raw",
        "data/processed",
        "results",
        "state",
        "logs",
        "contracts",
        "docs",
    ]

    for d in base_dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

def check_dependencies():
    """Verify that required dependencies are installed."""
    required = [
        "networkx", "pandas", "numpy", "scipy", "scikit-learn",
        "matplotlib", "seaborn", "pyyaml", "jsonschema"
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"ERROR: Missing dependencies: {', '.join(missing)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    else:
        print("All dependencies verified.")
        return True

def main():
    """Main entry point for project setup."""
    print("Initializing llmXive Network Topology Project...")
    create_directories()
    if check_dependencies():
        print("Project setup complete.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()