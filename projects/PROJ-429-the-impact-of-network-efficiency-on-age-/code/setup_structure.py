import os
import json
from pathlib import Path
from datetime import datetime
from config import ensure_dirs

def create_directories():
    """
    Creates the project directory structure as defined in plan.md.
    Directories: code/, data/, state/, tests/, docs/, contracts/, figures/
    """
    base_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "data/quality",
        "data/config",
        "state",
        "tests/unit",
        "tests/integration",
        "tests/benchmark",
        "docs/decisions",
        "contracts",
        "figures"
    ]
    
    # Ensure base code and data dirs exist first
    ensure_dirs()
    
    for dir_path in base_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

def create_manifest():
    """
    Creates an initial manifest.json recording the creation of the structure.
    """
    manifest = {
        "project": "PROJ-429-the-impact-of-network-efficiency-on-age-",
        "task": "T001",
        "created_at": datetime.utcnow().isoformat(),
        "structure_version": "1.0",
        "directories": [
            "code", "data/raw", "data/processed", "data/results", 
            "data/quality", "data/config", "state", "tests/unit", 
            "tests/integration", "tests/benchmark", "docs/decisions", 
            "contracts", "figures"
        ]
    }
    
    manifest_path = Path("data/quality/structure_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Created manifest: {manifest_path}")

def main():
    """
    Entry point for T001: Create project structure.
    """
    print("Starting T001: Creating project structure...")
    create_directories()
    create_manifest()
    print("T001 Complete.")

if __name__ == "__main__":
    main()