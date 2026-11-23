import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Configuration for artifact scanning
ARTIFACT_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "data/models",
    "src/features",
    "src/modeling",
    "src/intervention",
    "src/eval",
    "src/utils",
]
EXCLUDE_PATTERNS = {".git", "__pycache__", ".pyc", ".tmp", ".log"}
MANIFEST_PATH = "state/artifact_manifest.json"


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic hash of a file.
    Reads in chunks to handle large files without OOM.
    """
    hasher = hashlib.new(algorithm)
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {file_path}")

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_artifacts(base_dir: Path, artifact_dirs: List[str] = None) -> List[Dict[str, Any]]:
    """
    Recursively scan project directories for artifacts and compute their hashes.
    Returns a list of dicts: {'path': str, 'hash': str, 'size': int, 'type': str}
    """
    if artifact_dirs is None:
        artifact_dirs = ARTIFACT_DIRS

    artifacts = []
    base_path = Path(base_dir)

    for rel_dir in artifact_dirs:
        target_dir = base_path / rel_dir
        if not target_dir.exists():
            # Skip non-existent directories (e.g., empty data folders)
            continue

        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                # Check exclusion patterns
                if any(exc in str(file_path) for exc in EXCLUDE_PATTERNS):
                    continue

                try:
                    file_hash = compute_file_hash(file_path)
                    artifacts.append({
                        "path": str(file_path.relative_to(base_path)),
                        "hash": file_hash,
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix,
                        "mtime": file_path.stat().st_mtime
                    })
                except Exception as e:
                    # Log error but continue scanning other files
                    print(f"Warning: Could not hash {file_path}: {e}", file=sys.stderr)

    return artifacts


def generate_manifest(artifacts: List[Dict[str, Any]], project_root: Path) -> Dict[str, Any]:
    """
    Generate a manifest dictionary containing metadata and a list of artifact hashes.
    """
    import time
    return {
        "project_root": str(project_root),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "algorithm": "sha256",
        "total_artifacts": len(artifacts),
        "artifacts": artifacts,
        "summary": {
            "total_size_bytes": sum(a["size"] for a in artifacts),
            "by_type": {}
        }
    }


def save_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """
    Save the manifest to a JSON file. Creates parent directories if needed.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def main() -> int:
    """
    Entry point for the hash artifacts utility.
    Scans project directories, generates a manifest, and saves it to state/.
    Returns 0 on success, 1 on failure.
    """
    project_root = Path.cwd()
    print(f"Scanning artifacts in: {project_root}")

    try:
        artifacts = scan_artifacts(project_root)
        if not artifacts:
            print("No artifacts found to hash.")
            # Still generate an empty manifest to indicate successful scan
            manifest = generate_manifest([], project_root)
        else:
            manifest = generate_manifest(artifacts, project_root)

        output_path = project_root / MANIFEST_PATH
        save_manifest(manifest, output_path)
        print(f"Manifest saved to: {output_path}")
        print(f"Total artifacts hashed: {manifest['total_artifacts']}")
        return 0

    except Exception as e:
        print(f"Error during artifact hashing: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
