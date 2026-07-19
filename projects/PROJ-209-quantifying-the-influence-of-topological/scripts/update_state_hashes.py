#!/usr/bin/env python3
"""
T017: Update State Hashes Integration
Records SHA-256 checksums for all raw and processed data files,
the synthetic generator version (git hash), and the data_source flag.

Output: data/state/projects/PROJ-209-quantifying-the-influence-of-topological.yaml
"""
import os
import sys
import hashlib
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path to import shared utilities
# Assuming script is run from project root or via python -m
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.path_utils import get_project_root, ensure_dir, get_output_path
from infrastructure.error_handler import retry_with_backoff


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_git_hash() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def load_json_file(file_path: Path) -> Optional[Dict]:
    """Safely load a JSON file."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def scan_directory_for_checksums(
    directory: Path,
    extensions: List[str] = ['.csv', '.json', '.pkl', '.yaml', '.yml']
) -> List[Dict[str, Any]]:
    """Scan a directory for files and compute their checksums."""
    checksums = []
    if not directory.exists():
        return checksums
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and any(file_path.suffix == ext for ext in extensions):
            try:
                checksum = compute_sha256(file_path)
                relative_path = file_path.relative_to(PROJECT_ROOT)
                checksums.append({
                    "path": str(relative_path),
                    "sha256": checksum,
                    "size_bytes": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
            except Exception as e:
                print(f"Warning: Could not checksum {file_path}: {e}")
    return checksums


def generate_project_state_yaml(
    project_id: str,
    raw_checksums: List[Dict],
    processed_checksums: List[Dict],
    synthetic_checksums: List[Dict],
    git_hash: str,
    data_source: str
) -> Dict[str, Any]:
    """Construct the state dictionary for the project."""
    return {
        "project_id": project_id,
        "generated_at": datetime.now().isoformat(),
        "git_hash": git_hash,
        "data_source": data_source,
        "checksums": {
            "raw": raw_checksums,
            "processed": processed_checksums,
            "synthetic": synthetic_checksums
        },
        "summary": {
            "total_raw_files": len(raw_checksums),
            "total_processed_files": len(processed_checksums),
            "total_synthetic_files": len(synthetic_checksums),
            "total_files": len(raw_checksums) + len(processed_checksums) + len(synthetic_checksums)
        }
    }


def save_yaml_file(data: Dict, output_path: Path) -> None:
    """
    Save data as a YAML file.
    Since PyYAML might not be in strict requirements, we implement a simple serializer
    or use json if yaml is not available. However, the spec asks for .yaml.
    We will try to import yaml, fallback to a simple string representation if not.
    """
    try:
        import yaml
        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except ImportError:
        # Fallback: write as JSON but with .yaml extension, or simple text
        # For strict compliance, we try to mimic YAML structure manually or use json
        # Given the constraint of "real data", we assume standard env might have pyyaml.
        # If not, we write a JSON-compatible block which is valid YAML.
        import json
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Warning: PyYAML not found. Saved as JSON-compatible YAML at {output_path}")


def main():
    """Main entry point for T017."""
    print("Starting T017: Update State Hashes...")
    
    project_id = "PROJ-209-quantifying-the-influence-of-topological"
    project_root = get_project_root()
    
    # Define paths
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    synthetic_dir = project_root / "data" / "raw" # Synthetic files are often in raw/ or a specific subfolder
    state_dir = project_root / "data" / "state" / "projects"
    output_file = state_dir / f"{project_id}.yaml"
    
    # Ensure output directory exists
    ensure_dir(output_file.parent)
    
    # Load data source flag
    data_source_file = project_root / "data" / "state" / "data_source.json"
    data_source_info = load_json_file(data_source_file)
    data_source = data_source_info.get("source", "unknown") if data_source_info else "unknown"
    
    print(f"Data Source Flag: {data_source}")
    
    # Scan directories
    print("Scanning raw data...")
    raw_checksums = scan_directory_for_checksums(raw_dir)
    
    print("Scanning processed data...")
    processed_checksums = scan_directory_for_checksums(processed_dir)
    
    # Check for synthetic files specifically if needed, or just include them in raw if they are there
    # The task mentions synthetic_train.csv and synthetic_holdout.csv in data/raw/
    # We'll scan raw again or specifically look for synthetic if they are separate
    synthetic_checksums = []
    if (raw_dir / "synthetic_train.csv").exists():
        synthetic_checksums.append({
            "path": str((raw_dir / "synthetic_train.csv").relative_to(project_root)),
            "sha256": compute_sha256(raw_dir / "synthetic_train.csv"),
            "size_bytes": (raw_dir / "synthetic_train.csv").stat().st_size
        })
    if (raw_dir / "synthetic_holdout.csv").exists():
        synthetic_checksums.append({
            "path": str((raw_dir / "synthetic_holdout.csv").relative_to(project_root)),
            "sha256": compute_sha256(raw_dir / "synthetic_holdout.csv"),
            "size_bytes": (raw_dir / "synthetic_holdout.csv").stat().st_size
        })
    
    # Get git hash
    git_hash = get_git_hash()
    print(f"Git Hash: {git_hash}")
    
    # Generate state
    state_data = generate_project_state_yaml(
        project_id=project_id,
        raw_checksums=raw_checksums,
        processed_checksums=processed_checksums,
        synthetic_checksums=synthetic_checksums,
        git_hash=git_hash,
        data_source=data_source
    )
    
    # Save output
    save_yaml_file(state_data, output_file)
    
    print(f"State file successfully written to: {output_file}")
    print(f"Summary: {state_data['summary']['total_files']} files checksummed.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())