"""
Setup script to create project directory structure.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any

def ensure_directories():
    """Create all required project directories."""
    project_root = Path("projects/PROJ-819-llmxive-follow-up-extending-heterogeneou")
    
    dirs = [
        project_root,
        project_root / "code",
        project_root / "code" / "cache",
        project_root / "code" / "pipeline",
        project_root / "code" / "analysis",
        project_root / "code" / "data",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "derived",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "state",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")
    
    # Create __init__.py files
    init_dirs = [
        project_root / "code",
        project_root / "code" / "cache",
        project_root / "code" / "pipeline",
        project_root / "code" / "analysis",
        project_root / "code" / "data",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "data" / "raw",
        project_root / "data" / "derived",
        project_root / "state",
    ]
    
    for d in init_dirs:
        init_file = d / "__init__.py"
        init_file.touch(exist_ok=True)
        print(f"Created __init__.py: {init_file}")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_data_files(base_dir: Path) -> List[Path]:
    """Get all files in data directories."""
    files = []
    for ext in ["*.json", "*.csv", "*.log", "*.txt", "*.png"]:
        files.extend(base_dir.rglob(ext))
    return files

def generate_checksums(base_dir: Path) -> Dict[str, str]:
    """Generate checksums for all data files."""
    checksums = {}
    files = get_data_files(base_dir)
    for f in files:
        rel_path = str(f.relative_to(base_dir))
        checksums[rel_path] = calculate_sha256(f)
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path):
    """Save checksums to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def main():
    """Main entry point."""
    print("Setting up project directories...")
    ensure_directories()
    print("Directory setup complete.")

if __name__ == "__main__":
    main()