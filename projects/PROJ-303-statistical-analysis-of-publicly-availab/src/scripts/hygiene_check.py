"""
Hygiene Check Script for NOAA GHCN-Daily Data

Computes SHA-256 hashes for raw data files and writes a manifest to
state/projects/hygiene_manifest.yaml.

Dependencies:
- T005-exec must have completed successfully to ensure valid data exists.
- T001 must have created the directory structure.

Usage:
    python src/scripts/hygiene_check.py
"""

import os
import sys
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from src.config import get_config

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file by reading it in chunks.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def scan_raw_data_directory(raw_data_dir: Path) -> List[Dict[str, Any]]:
    """
    Scans the raw data directory recursively for all files and computes their hashes.
    
    Args:
        raw_data_dir: Path to the raw data directory.
        
    Returns:
        List of dictionaries containing file metadata and hash.
        
    Raises:
        FileNotFoundError: If the raw data directory does not exist.
    """
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    if not raw_data_dir.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {raw_data_dir}")
    
    file_hashes = []
    
    # Walk through all files in the directory
    for root, _, files in os.walk(raw_data_dir):
        for file_name in files:
            file_path = Path(root) / file_name
            
            # Skip hidden files or temporary files
            if file_name.startswith('.'):
                continue
            
            try:
                file_hash = compute_sha256(file_path)
                relative_path = file_path.relative_to(project_root)
                
                file_hashes.append({
                    "file_path": str(relative_path),
                    "absolute_path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "sha256": file_hash,
                    "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
            except (PermissionError, OSError) as e:
                # Log error but continue processing other files
                print(f"Warning: Could not hash {file_path}: {e}", file=sys.stderr)
    
    return file_hashes

def write_manifest(file_hashes: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes the hygiene manifest to a YAML file.
    
    Args:
        file_hashes: List of file hash dictionaries.
        output_path: Path to the output YAML file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "script": "src/scripts/hygiene_check.py",
            "total_files": len(file_hashes),
            "total_size_bytes": sum(f["size_bytes"] for f in file_hashes)
        },
        "files": file_hashes
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    print(f"Hygiene manifest written to: {output_path}")
    print(f"Total files processed: {len(file_hashes)}")
    print(f"Total data size: {manifest['metadata']['total_size_bytes']:,} bytes")

def main():
    """Main entry point for the hygiene check script."""
    try:
        # Load configuration
        config = get_config()
        
        # Define paths based on config
        project_root = config.project_root
        raw_data_dir = project_root / config.paths.raw_data
        state_dir = project_root / config.paths.state
        
        # Output path for hygiene manifest
        output_path = state_dir / "projects" / "hygiene_manifest.yaml"
        
        print(f"Starting hygiene check...")
        print(f"Raw data directory: {raw_data_dir}")
        print(f"Output manifest: {output_path}")
        
        # Scan and hash files
        file_hashes = scan_raw_data_directory(raw_data_dir)
        
        if not file_hashes:
            print("Warning: No files found in raw data directory.", file=sys.stderr)
            # Still write an empty manifest to indicate check was run
            write_manifest([], output_path)
            return 0
        
        # Write manifest
        write_manifest(file_hashes, output_path)
        
        print("Hygiene check completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Ensure T005-exec has completed and raw data exists.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error during hygiene check: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
