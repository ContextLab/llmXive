"""
Script to compute SHA-256 hashes for project artifacts.
Implements versioning discipline (Principle V) by generating a manifest
of file hashes for reproducibility and integrity checking.
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add src to path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils.config import get_path


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_artifact_paths() -> List[Path]:
    """
    Collect all relevant artifact files to hash.
    Includes:
    - All .py files in code/src/
    - All .py files in code/scripts/
    - All .py files in code/tests/
    - Config files in code/ (requirements.txt, etc.)
    - Generated results in code/results/
    - Data files in code/data/
    """
    artifact_dirs = [
        "code/src",
        "code/scripts",
        "code/tests",
        "code/results",
        "code/data",
    ]
    
    patterns = ["*.py", "*.txt", "*.json", "*.csv", "*.yaml", "*.yml"]
    
    paths: List[Path] = []
    
    for dir_name in artifact_dirs:
        dir_path = _project_root / dir_name
        if not dir_path.exists():
            continue
        
        for pattern in patterns:
            paths.extend(dir_path.rglob(pattern))
    
    # Filter out __pycache__ and hidden files
    paths = [p for p in paths if "__pycache__" not in str(p) and not p.name.startswith(".")]
    
    # Sort for deterministic ordering
    return sorted(paths)


def generate_hash_manifest(output_path: Path) -> Dict[str, Any]:
    """
    Generate a manifest of SHA-256 hashes for all tracked artifacts.
    Returns the manifest dictionary and writes it to output_path.
    """
    artifact_paths = get_artifact_paths()
    
    manifest: Dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project": "PROJ-014-robotic-artificial-intelligence-for-auto",
        "total_files": len(artifact_paths),
        "artifacts": {}
    }
    
    for file_path in artifact_paths:
        # Store relative path from project root
        relative_path = str(file_path.relative_to(_project_root))
        
        try:
            file_hash = compute_sha256(file_path)
            file_size = file_path.stat().st_size
            manifest["artifacts"][relative_path] = {
                "sha256": file_hash,
                "size_bytes": file_size
            }
        except Exception as e:
            # Log error but continue with other files
            print(f"Warning: Could not hash {relative_path}: {e}", file=sys.stderr)
            continue
    
    # Write manifest to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    
    return manifest


def main():
    """Main entry point for hash generation."""
    # Determine output path - default to code/results/hash_manifest.json
    output_path = get_path("results", "hash_manifest.json")
    
    print(f"Computing SHA-256 hashes for project artifacts...")
    print(f"Output: {output_path}")
    
    try:
        manifest = generate_hash_manifest(output_path)
        
        print(f"Successfully hashed {manifest['total_files']} files.")
        print(f"Manifest saved to: {output_path}")
        
        # Print summary
        print("\nArtifact Hash Summary:")
        print("-" * 60)
        for rel_path, info in sorted(manifest["artifacts"].items()):
            print(f"{info['sha256'][:16]}...  {rel_path}")
        
        return 0
        
    except Exception as e:
        print(f"Error generating hash manifest: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
