"""
Hash Artifacts Utility Script.

Computes SHA-256 hashes for all files under a specified directory (default: data/)
and writes a JSON manifest to a specified output location (default: state/manifest.json).

This script is designed to be run as part of the pipeline to ensure data integrity
and versioning of artifacts.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import project configuration for path resolution
try:
    from config import get_path, ensure_directories, get_config_summary
except ImportError:
    # Fallback for standalone execution if config is not in path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import get_path, ensure_directories, get_config_summary


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

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
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def hash_directory(
    directory: Path,
    extensions: Optional[List[str]] = None,
    ignore_dirs: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Recursively hash all files in a directory.

    Args:
        directory: Root directory to scan.
        extensions: Optional list of file extensions to include (e.g., ['.json', '.jsonl']).
                    If None, all files are included.
        ignore_dirs: Optional list of directory names to ignore (e.g., ['.git', '__pycache__']).

    Returns:
        List of dictionaries containing file path and hash.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if ignore_dirs is None:
        ignore_dirs = ['.git', '__pycache__', '.pytest_cache', 'node_modules']

    artifacts = []
    for root, dirs, files in os.walk(directory):
        # Filter out ignored directories in-place to prevent os.walk from descending into them
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            file_path = Path(root) / file

            # Check extension filter if provided
            if extensions:
                if file_path.suffix not in extensions:
                    continue

            # Calculate relative path from the root directory
            relative_path = file_path.relative_to(directory)

            try:
                file_hash = compute_sha256(file_path)
                artifacts.append({
                    "path": str(relative_path),
                    "hash": file_hash,
                    "size_bytes": file_path.stat().st_size
                })
            except (PermissionError, OSError) as e:
                print(f"Warning: Could not hash {file_path}: {e}", file=sys.stderr)

    return artifacts


def generate_manifest(
    artifacts: List[Dict[str, Any]],
    source_directory: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a manifest dictionary from the list of artifacts.

    Args:
        artifacts: List of artifact dictionaries (path, hash, size).
        source_directory: The directory that was hashed.
        metadata: Optional additional metadata to include (e.g., timestamp, config).

    Returns:
        Complete manifest dictionary.
    """
    manifest = {
        "version": "1.0",
        "source_directory": str(source_directory),
        "artifact_count": len(artifacts),
        "artifacts": artifacts
    }

    if metadata:
        manifest["metadata"] = metadata

    return manifest


def verify_manifest(manifest_path: Path, data_dir: Path) -> bool:
    """
    Verify the hashes in a manifest against the current state of files in data_dir.

    Args:
        manifest_path: Path to the manifest JSON file.
        data_dir: Path to the directory containing the data files.

    Returns:
        True if all hashes match, False otherwise.
    """
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return False

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    source_dir = Path(manifest["source_directory"])
    # Resolve relative to manifest location if needed, but assume absolute or relative to project root
    if not source_dir.is_absolute():
        source_dir = (manifest_path.parent / source_dir).resolve()

    if not source_dir.exists():
        print(f"Source directory in manifest not found: {source_dir}", file=sys.stderr)
        return False

    all_match = True
    for artifact in manifest["artifacts"]:
        file_path = source_dir / artifact["path"]
        if not file_path.exists():
            print(f"Missing file: {file_path}", file=sys.stderr)
            all_match = False
            continue

        current_hash = compute_sha256(file_path)
        if current_hash != artifact["hash"]:
            print(f"Hash mismatch for {file_path}: expected {artifact['hash']}, got {current_hash}", file=sys.stderr)
            all_match = False

    return all_match


def hash_artifact(file_path: Path) -> str:
    """
    Convenience wrapper to hash a single file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal hash string.
    """
    return compute_sha256(file_path)


def main():
    """
    CLI entry point for the hash artifacts utility.

    Usage:
        python code/utils/hash_artifacts.py --dir data/curated --output state/manifest_curated.json
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute SHA-256 hashes for files in a directory and generate a manifest."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="data",
        help="Directory to scan for files (relative to project root). Default: data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="state/manifest.json",
        help="Output path for the manifest JSON file (relative to project root). Default: state/manifest.json"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing manifest against current files instead of generating a new one."
    )
    parser.add_argument(
        "--extensions",
        type=str,
        nargs="+",
        default=None,
        help="File extensions to include (e.g., .json .jsonl .csv). If omitted, all files are included."
    )

    args = parser.parse_args()

    # Resolve paths relative to project root (assuming script is in code/utils/)
    project_root = Path(__file__).resolve().parent.parent.parent
    target_dir = project_root / args.dir
    output_path = project_root / args.output

    # Ensure extensions are prefixed with dot if not already
    if args.extensions:
        args.extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.extensions]

    try:
        if args.verify:
            if not output_path.exists():
                print(f"Error: Manifest file not found at {output_path}", file=sys.stderr)
                sys.exit(1)
            print(f"Verifying files in {target_dir} against {output_path}...")
            is_valid = verify_manifest(output_path, target_dir)
            if is_valid:
                print("Verification PASSED: All hashes match.")
                sys.exit(0)
            else:
                print("Verification FAILED: Hash mismatches or missing files detected.", file=sys.stderr)
                sys.exit(1)
        else:
            if not target_dir.exists():
                print(f"Error: Target directory not found: {target_dir}", file=sys.stderr)
                sys.exit(1)

            print(f"Scanning directory: {target_dir}")
            artifacts = hash_directory(target_dir, extensions=args.extensions)

            if not artifacts:
                print("Warning: No files found to hash.", file=sys.stderr)
            else:
                print(f"Found {len(artifacts)} files.")

            # Generate metadata
            config_summary = get_config_summary()
            metadata = {
                "generated_by": "hash_artifacts.py",
                "config_summary": config_summary
            }

            manifest = generate_manifest(
                artifacts,
                str(target_dir.relative_to(project_root)),
                metadata
            )

            # Ensure output directory exists
            ensure_directories([output_path.parent])

            with open(output_path, 'w') as f:
                json.dump(manifest, f, indent=2)

            print(f"Manifest written to: {output_path}")
            print(f"Total artifacts: {len(artifacts)}")

    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()