"""
Utility functions for hashing artifacts to ensure data integrity.
Implements Constitution Principle V.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hex digest of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def hash_directory(
    directory_path: Path,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Hash all files in a directory.
    
    Args:
        directory_path: Path to the directory.
        extensions: Optional list of file extensions to include.
    
    Returns:
        Dictionary mapping relative file paths to their hashes.
    """
    hashes = {}
    
    if not directory_path.exists():
        return hashes
    
    for file_path in directory_path.rglob("*"):
        if file_path.is_file():
            if extensions is None or any(file_path.suffix == ext for ext in extensions):
                rel_path = file_path.relative_to(directory_path)
                hashes[str(rel_path)] = compute_sha256(file_path)
    
    return hashes


def generate_manifest(
    hashes: Dict[str, str],
    directory_path: Path,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a manifest file containing hashes.
    
    Args:
        hashes: Dictionary of file paths to hashes.
        directory_path: Base directory path.
        output_path: Optional output path for manifest.
    
    Returns:
        Path to the generated manifest.
    """
    if output_path is None:
        output_path = directory_path / "manifest.json"
    
    manifest = {
        "directory": str(directory_path),
        "file_hashes": hashes,
        "total_files": len(hashes)
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    return output_path


def verify_manifest(
    manifest_path: Path,
    directory_path: Path
) -> Dict[str, bool]:
    """
    Verify file hashes against a manifest.
    
    Args:
        manifest_path: Path to the manifest file.
        directory_path: Base directory path.
    
    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    results = {}
    expected_hashes = manifest.get("file_hashes", {})
    
    for rel_path, expected_hash in expected_hashes.items():
        file_path = directory_path / rel_path
        if file_path.exists():
            actual_hash = compute_sha256(file_path)
            results[rel_path] = (actual_hash == expected_hash)
        else:
            results[rel_path] = False
    
    return results


def hash_artifact(
    file_path: Path,
    state_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Hash a single artifact and record it in the state directory.
    
    Args:
        file_path: Path to the file to hash.
        state_dir: Directory to store the state manifest. Defaults to 'state/'.
    
    Returns:
        Dictionary containing the hash and metadata.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    
    if state_dir is None:
        state_dir = Path("state")
    
    state_dir.mkdir(parents=True, exist_ok=True)
    
    file_hash = compute_sha256(file_path)
    rel_path = str(file_path)
    timestamp = str(Path(file_path).stat().st_mtime)
    
    result = {
        "path": rel_path,
        "hash": file_hash,
        "timestamp": timestamp
    }
    
    state_file = state_dir / "artifact_hashes.json"
    
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            try:
                state = json.load(f)
            except json.JSONDecodeError:
                state = {}
    else:
        state = {}
    
    state[rel_path] = result
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    
    return result


def main():
    """Main entry point for testing hashing utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hash artifacts for data integrity.")
    parser.add_argument(
        "--file",
        type=str,
        help="Path to a single file to hash and record in state/"
    )
    parser.add_argument(
        "--directory",
        type=str,
        help="Path to a directory to hash all files in"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to write the manifest (only for --directory)"
    )
    parser.add_argument(
        "--verify",
        type=str,
        help="Path to a manifest file to verify against a directory"
    )
    parser.add_argument(
        "--directory-for-verify",
        type=str,
        help="Directory to verify against the manifest (required with --verify)"
    )
    
    args = parser.parse_args()
    
    if args.verify and args.directory_for_verify:
        manifest_path = Path(args.verify)
        dir_path = Path(args.directory_for_verify)
        results = verify_manifest(manifest_path, dir_path)
        all_valid = all(results.values())
        print(f"Verification results: {results}")
        print(f"Overall status: {'PASS' if all_valid else 'FAIL'}")
        return 0 if all_valid else 1
    
    if args.file:
        file_path = Path(args.file)
        result = hash_artifact(file_path)
        print(f"Hashed {file_path}: {result['hash']}")
        print(f"Recorded in state/artifact_hashes.json")
        return 0
    
    if args.directory:
        dir_path = Path(args.directory)
        hashes = hash_directory(dir_path)
        print(f"Hashed {len(hashes)} files in {dir_path}")
        
        output_path = Path(args.output) if args.output else None
        manifest_path = generate_manifest(hashes, dir_path, output_path)
        print(f"Manifest written to: {manifest_path}")
        return 0
    
    # Default: test mode
    print("Testing Hash Artifacts...")
    
    # Test compute_sha256
    test_file = Path(__file__)
    hash_val = compute_sha256(test_file)
    print(f"Hash of {test_file.name}: {hash_val}")
    
    # Test hash_artifact with a dummy file
    dummy_content = b"test content for hashing"
    dummy_path = Path("data/raw/dummy_test.txt")
    dummy_path.parent.mkdir(parents=True, exist_ok=True)
    dummy_path.write_bytes(dummy_content)
    
    try:
        result = hash_artifact(dummy_path)
        print(f"Dummy file hashed: {result['hash']}")
        print(f"State recorded at: state/artifact_hashes.json")
        
        # Verify the state file exists and contains the entry
        state_file = Path("state/artifact_hashes.json")
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
            if str(dummy_path) in state:
                print("Verification: State file contains the dummy entry.")
            else:
                print("Error: State file missing the dummy entry.")
                return 1
        else:
            print("Error: State file not created.")
            return 1
    finally:
        # Cleanup dummy file
        if dummy_path.exists():
            dummy_path.unlink()
        if Path("state").exists() and list(Path("state").glob("*")):
            # Only remove state if it was created by this test
            # In a real run, we wouldn't clean up
            pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main())