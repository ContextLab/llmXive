import os
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Define the directories to be checksummed as per task requirements
CHECKSUM_DIRS = [
    "data/configs",
    "data/results",
    "data/logs",
    "state"
]

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def find_files(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Recursively find all files in a directory.
    Optionally filter by extensions (e.g., ['.yaml', '.json', '.npy']).
    If extensions is None, include all files.
    """
    files = []
    if not directory.exists():
        logging.warning(f"Directory does not exist: {directory}")
        return files

    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            if extensions:
                if any(file_path.suffix == ext for ext in extensions):
                    files.append(file_path)
            else:
                files.append(file_path)
    return files

def generate_checksums(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate SHA256 checksums for all files in the target directories.
    Returns a dictionary containing the checksums and metadata.
    Writes the result to a JSON file if output_path is provided.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    checksums = {
        "project_root": str(project_root),
        "directories": CHECKSUM_DIRS,
        "files": {}
    }

    for dir_name in CHECKSUM_DIRS:
        target_dir = project_root / dir_name
        if not target_dir.exists():
            logging.warning(f"Skipping non-existent directory: {target_dir}")
            continue

        files = find_files(target_dir)
        for file_path in files:
            # Store path relative to project root
            rel_path = file_path.relative_to(project_root)
            try:
                checksum = calculate_sha256(file_path)
                checksums["files"][str(rel_path)] = checksum
            except Exception as e:
                logging.error(f"Error hashing {file_path}: {e}")
                checksums["files"][str(rel_path)] = "ERROR"

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(checksums, f, indent=2)
        logging.info(f"Checksums written to {output_path}")

    return checksums

def verify_checksums(checksum_file: Path) -> bool:
    """
    Verify current file checksums against a previously generated checksum file.
    Returns True if all match, False otherwise.
    """
    if not checksum_file.exists():
        logging.error(f"Checksum file not found: {checksum_file}")
        return False

    with open(checksum_file, "r") as f:
        stored_checksums = json.load(f)

    project_root = Path(checksum_file).resolve().parent.parent
    current_checksums = generate_checksums()

    # Compare
    if stored_checksums.get("files") != current_checksums.get("files"):
        logging.error("Checksum mismatch detected.")
        return False

    logging.info("All checksums verified successfully.")
    return True

def main():
    """Main entry point for script execution."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate or verify SHA256 checksums for project artifacts.")
    parser.add_argument("--output", type=str, default="state/checksums.json",
                        help="Path to write the checksum JSON file.")
    parser.add_argument("--verify", type=str, default=None,
                        help="Path to a checksum file to verify against.")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    if args.verify:
        verify_path = Path(args.verify)
        if not verify_path.is_absolute():
            verify_path = project_root / verify_path
        success = verify_checksums(verify_path)
        exit(0 if success else 1)
    else:
        generate_checksums(output_path)
        exit(0)

if __name__ == "__main__":
    main()
