import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import get_config_summary


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 hash of a file's contents.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def hash_directory(
    directory_path: Path,
    extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute hashes for all files in a directory (recursive).

    Args:
        directory_path: Path to the directory to hash.
        extensions: Optional list of file extensions to include (e.g., ['.json', '.jsonl']).
        exclude_patterns: Optional list of patterns to exclude (e.g., ['__pycache__', '.git']).

    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes.
    """
    hashes = {}
    directory_path = directory_path.resolve()

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    for root, dirs, files in os.walk(directory_path):
        # Filter out excluded directories
        if exclude_patterns:
            dirs[:] = [d for d in dirs if not any(p in d for p in exclude_patterns)]

        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(directory_path)

            # Check extensions if specified
            if extensions and file_path.suffix not in extensions:
                continue

            # Check exclude patterns for file names
            if exclude_patterns and any(p in str(rel_path) for p in exclude_patterns):
                continue

            try:
                hashes[str(rel_path)] = compute_sha256(file_path)
            except Exception as e:
                print(f"Warning: Could not hash {rel_path}: {e}", file=sys.stderr)

    return hashes


def generate_manifest(
    hashes: Dict[str, str],
    directory_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a manifest file containing hashes and metadata.

    Args:
        hashes: Dictionary of file paths to hashes.
        directory_path: Path to the directory being hashed.
        metadata: Optional additional metadata to include.

    Returns:
        The manifest dictionary.
    """
    manifest = {
        "directory": str(directory_path),
        "file_count": len(hashes),
        "files": hashes,
        "config": get_config_summary(),
        "metadata": metadata or {}
    }
    return manifest


def verify_manifest(
    manifest_path: Path,
    directory_path: Path
) -> Dict[str, Any]:
    """
    Verify files against a manifest.

    Args:
        manifest_path: Path to the manifest JSON file.
        directory_path: Path to the directory to verify.

    Returns:
        Dictionary with verification results:
        {
            "valid": bool,
            "missing_files": List[str],
            "modified_files": List[str],
            "extra_files": List[str]
        }
    """
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    expected_hashes = manifest.get("files", {})
    directory_path = directory_path.resolve()

    # Get current hashes
    current_hashes = hash_directory(directory_path)

    # Check for missing files
    missing_files = [f for f in expected_hashes if f not in current_hashes]

    # Check for modified files
    modified_files = []
    for rel_path, expected_hash in expected_hashes.items():
        if rel_path in current_hashes:
            if current_hashes[rel_path] != expected_hash:
                modified_files.append(rel_path)

    # Check for extra files (not in manifest but exist)
    extra_files = [f for f in current_hashes if f not in expected_hashes]

    is_valid = len(missing_files) == 0 and len(modified_files) == 0

    return {
        "valid": is_valid,
        "missing_files": missing_files,
        "modified_files": modified_files,
        "extra_files": extra_files
    }


def main():
    """
    CLI entry point for hash_artifacts module.
    Usage: python -m code.utils.hash_artifacts <command> [args]
    Commands:
        hash <directory> [--extensions .json,.jsonl] [--exclude __pycache__]
        verify <manifest_path> <directory>
    """
    if len(sys.argv) < 2:
        print("Usage: python -m code.utils.hash_artifacts <command> [args]")
        print("Commands: hash, verify")
        sys.exit(1)

    command = sys.argv[1]

    if command == "hash":
        if len(sys.argv) < 3:
            print("Error: Directory path required")
            sys.exit(1)

        dir_path = Path(sys.argv[2])
        extensions = None
        exclude_patterns = None

        # Parse optional arguments
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--extensions":
                if i + 1 < len(sys.argv):
                    extensions = sys.argv[i + 1].split(",")
                    i += 2
                else:
                    print("Error: --extensions requires a value")
                    sys.exit(1)
            elif sys.argv[i] == "--exclude":
                if i + 1 < len(sys.argv):
                    exclude_patterns = sys.argv[i + 1].split(",")
                    i += 2
                else:
                    print("Error: --exclude requires a value")
                    sys.exit(1)
            else:
                i += 1

        hashes = hash_directory(dir_path, extensions, exclude_patterns)
        manifest = generate_manifest(hashes, dir_path)

        # Save manifest to directory
        manifest_path = dir_path / "hash_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"Manifest saved to: {manifest_path}")
        print(f"Files hashed: {len(hashes)}")

    elif command == "verify":
        if len(sys.argv) < 4:
            print("Error: manifest_path and directory_path required")
            sys.exit(1)

        manifest_path = Path(sys.argv[2])
        dir_path = Path(sys.argv[3])

        result = verify_manifest(manifest_path, dir_path)

        if result["valid"]:
            print("Verification PASSED: All files match.")
        else:
            print("Verification FAILED:")
            if result["missing_files"]:
                print(f"  Missing: {result['missing_files']}")
            if result["modified_files"]:
                print(f"  Modified: {result['modified_files']}")
            if result["extra_files"]:
                print(f"  Extra: {result['extra_files']}")

        sys.exit(0 if result["valid"] else 1)

    else:
        print(f"Unknown command: {command}")
        print("Commands: hash, verify")
        sys.exit(1)


if __name__ == "__main__":
    main()
