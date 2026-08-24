"""
Setup script for T004: Create data directory structure and verify existence.

This script ensures the following directories exist:
- data/raw/
- data/processed/

And creates/initializes the checksums file:
- data/checksums.json

It verifies the existence of these paths after creation.
"""
import json
import os
from pathlib import Path

# Define project root relative to this script's location or current working directory
# Assuming this script runs from the project root or code/ directory
# We'll resolve relative to the script's parent directory to be safe if placed in code/
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent if script_dir.name == "code" else script_dir

data_dir = project_root / "data"
raw_dir = data_dir / "raw"
processed_dir = data_dir / "processed"
checksums_file = data_dir / "checksums.json"

def ensure_directory(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def ensure_checksums_file(path: Path) -> None:
    """Initialize or verify checksums.json file."""
    default_content = {
        "version": "1.0.0",
        "description": "Checksums for downloaded and generated artifacts to ensure data integrity.",
        "files": {}
    }
    
    if not path.exists():
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_content, f, indent=2)
        print(f"Created checksums file: {path}")
    else:
        # Verify it's valid JSON and has the expected structure
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            if "version" not in content or "files" not in content:
                # Update structure if missing keys
                content["version"] = content.get("version", "1.0.0")
                content["files"] = content.get("files", {})
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2)
                print(f"Updated checksums file structure: {path}")
            else:
                print(f"Checksums file already valid: {path}")
        except json.JSONDecodeError:
            raise RuntimeError(f"Checksums file exists but is not valid JSON: {path}")

def verify_structure() -> bool:
    """Verify all required paths exist."""
    checks = [
        (data_dir, "data directory"),
        (raw_dir, "data/raw directory"),
        (processed_dir, "data/processed directory"),
        (checksums_file, "data/checksums.json file")
    ]
    
    all_valid = True
    for path, desc in checks:
        if path.exists():
            print(f"✓ Verified: {desc} exists at {path}")
        else:
            print(f"✗ Missing: {desc} at {path}")
            all_valid = False
    
    return all_valid

def main():
    print(f"Running T004: Setup data directory structure")
    print(f"Project root detected at: {project_root}")
    
    # Ensure directories exist
    ensure_directory(data_dir)
    ensure_directory(raw_dir)
    ensure_directory(processed_dir)
    
    # Ensure checksums file exists and is valid
    ensure_checksums_file(checksums_file)
    
    # Verify final structure
    print("\nVerifying structure...")
    if verify_structure():
        print("\n✓ T004: Data directory structure setup completed successfully.")
        return 0
    else:
        print("\n✗ T004: Failed to verify data directory structure.")
        return 1

if __name__ == "__main__":
    exit(main())