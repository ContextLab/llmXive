"""
Update state/artifacts/checksums.json with SHA-256 hash of final artifacts.

This script implements Task T036: Versioning Discipline.
It calculates the SHA-256 hash of the statistical_comparison.csv file
and updates the state/artifacts/checksums.json file with the hash and timestamp.

Dependencies:
- No external dependencies beyond standard library
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def update_checksums(
    artifact_path: Path, checksums_path: Path
) -> dict:
    """
    Update the checksums.json file with the hash of the specified artifact.
    
    Args:
        artifact_path: Path to the artifact file to hash
        checksums_path: Path to the checksums.json file
        
    Returns:
        Dictionary containing the updated checksum information
        
    Raises:
        FileNotFoundError: If the artifact file does not exist
        ValueError: If the artifact file is empty
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {artifact_path}")
    
    if artifact_path.stat().st_size == 0:
        raise ValueError(f"Artifact file is empty: {artifact_path}")
    
    file_hash = calculate_sha256(artifact_path)
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    checksum_entry = {
        "file": artifact_path.name,
        "hash": file_hash,
        "timestamp": timestamp
    }
    
    # Load existing checksums or create new dict
    checksums = {}
    if checksums_path.exists():
        with open(checksums_path, "r") as f:
            checksums = json.load(f)
    
    # Update or add the entry
    checksums[artifact_path.name] = checksum_entry
    
    # Ensure parent directory exists
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write updated checksums
    with open(checksums_path, "w") as f:
        json.dump(checksums, f, indent=2)
    
    return checksum_entry


def main():
    """Main entry point for the checksum update script."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    artifact_path = project_root / "data" / "processed" / "statistical_comparison.csv"
    checksums_path = project_root / "state" / "artifacts" / "checksums.json"
    
    print(f"Processing artifact: {artifact_path}")
    print(f"Checksums file: {checksums_path}")
    
    try:
        entry = update_checksums(artifact_path, checksums_path)
        print(f"Successfully updated checksums.json")
        print(f"  File: {entry['file']}")
        print(f"  Hash: {entry['hash']}")
        print(f"  Timestamp: {entry['timestamp']}")
        return 0
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())