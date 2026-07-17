"""
Data loader module for llmXive.
Handles downloading, verifying checksums, and hashing datasets.
"""

import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple

# Import from sibling module T005
from validate_citations import load_manifest, extract_urls_from_markdown, verify_citations

# Constants
DATA_RAW_DIR = Path("data/raw")
CHECKSUMS_FILE = Path("data/checksums.json")


def ensure_dirs():
    """Ensure data directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)


def compute_file_hash(filepath: Path, algorithm: str = "sha256") -> str:
    """
    Compute the hash of a file.

    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm (default: sha256).

    Returns:
        Hex digest of the file hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    hasher = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_file(
    url: str,
    output_path: Path,
    expected_hash: Optional[str] = None,
    chunk_size: int = 8192,
) -> Tuple[bool, str]:
    """
    Download a file from a URL.

    Args:
        url: The URL to download from.
        output_path: Local path to save the file.
        expected_hash: Optional expected hash for verification.
        chunk_size: Size of chunks to read during download.

    Returns:
        Tuple of (success: bool, message: str).

    Raises:
        Exception: If download fails or hash verification fails.
    """
    ensure_dirs()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Downloading from {url} to {output_path}...")
        urllib.request.urlretrieve(url, output_path)
        print(f"Download complete: {output_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {e}")

    # Verify hash if expected_hash is provided
    if expected_hash:
        actual_hash = compute_file_hash(output_path)
        if actual_hash.lower() != expected_hash.lower():
            raise ValueError(
                f"Hash mismatch for {output_path}. "
                f"Expected: {expected_hash}, Got: {actual_hash}"
            )
        print(f"Hash verification successful: {actual_hash}")

    return True, f"Successfully downloaded and verified {output_path}"


def load_checksums() -> Dict[str, str]:
    """
    Load existing checksums from the checksums file.

    Returns:
        Dictionary mapping filenames to their checksums.
    """
    if CHECKSUMS_FILE.exists():
        with open(CHECKSUMS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_checksums(checksums: Dict[str, str]) -> None:
    """
    Save checksums to the checksums file.

    Args:
        checksums: Dictionary mapping filenames to their checksums.
    """
    with open(CHECKSUMS_FILE, "w") as f:
        json.dump(checksums, f, indent=2)


def verify_dataset(dataset_name: str, manifest_path: Optional[str] = None) -> bool:
    """
    Verify a dataset against its manifest or checksums file.

    Args:
        dataset_name: Name of the dataset to verify.
        manifest_path: Optional path to a markdown manifest file.

    Returns:
        True if verification passes, False otherwise.

    Raises:
        FileNotFoundError: If the dataset file or manifest is not found.
    """
    dataset_path = DATA_RAW_DIR / dataset_name

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    # If a manifest is provided, verify against it
    if manifest_path:
        manifest_data = load_manifest(manifest_path)
        # The manifest should contain expected hashes
        # We'll use the verify_citations function to check URLs if they exist
        # For now, we assume the manifest contains hash info
        expected_hash = manifest_data.get(dataset_name)
        if expected_hash:
            actual_hash = compute_file_hash(dataset_path)
            if actual_hash.lower() != expected_hash.lower():
                raise ValueError(
                    f"Dataset {dataset_name} hash verification failed. "
                    f"Expected: {expected_hash}, Got: {actual_hash}"
                )
            print(f"Dataset {dataset_name} verified successfully.")
            return True

    # Fallback: check against local checksums file
    checksums = load_checksums()
    if dataset_name in checksums:
        expected_hash = checksums[dataset_name]
        actual_hash = compute_file_hash(dataset_path)
        if actual_hash.lower() != expected_hash.lower():
            raise ValueError(
                f"Dataset {dataset_name} hash verification failed. "
                f"Expected: {expected_hash}, Got: {actual_hash}"
            )
        print(f"Dataset {dataset_name} verified successfully against checksums file.")
        return True

    # No verification info found
    print(f"No verification info found for {dataset_name}. Skipping hash check.")
    return True


def register_dataset(dataset_name: str, filepath: Optional[Path] = None) -> None:
    """
    Register a dataset in the checksums file.

    Args:
        dataset_name: Name of the dataset.
        filepath: Optional explicit path. If None, looks in data/raw.
    """
    if filepath is None:
        filepath = DATA_RAW_DIR / dataset_name

    if not filepath.exists():
        raise FileNotFoundError(f"Cannot register non-existent file: {filepath}")

    checksums = load_checksums()
    file_hash = compute_file_hash(filepath)
    checksums[dataset_name] = file_hash
    save_checksums(checksums)
    print(f"Registered {dataset_name} with hash {file_hash}")


def main():
    """CLI entry point for data loader operations."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Data loader: download, verify, and hash datasets."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download a dataset")
    download_parser.add_argument("url", help="URL to download from")
    download_parser.add_argument("output_name", help="Name for the output file")
    download_parser.add_argument("--hash", help="Expected hash for verification")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a dataset")
    verify_parser.add_argument("dataset_name", help="Name of the dataset to verify")
    verify_parser.add_argument(
        "--manifest", help="Path to markdown manifest file"
    )

    # Register command
    register_parser = subparsers.add_parser("register", help="Register a dataset")
    register_parser.add_argument("dataset_name", help="Name of the dataset")
    register_parser.add_argument("--path", help="Explicit path to the dataset file")

    args = parser.parse_args()

    if args.command == "download":
        output_path = DATA_RAW_DIR / args.output_name
        download_file(
            args.url, output_path, expected_hash=args.hash
        )
        register_dataset(args.output_name, output_path)

    elif args.command == "verify":
        verify_dataset(args.dataset_name, args.manifest)

    elif args.command == "register":
        filepath = Path(args.path) if args.path else None
        register_dataset(args.dataset_name, filepath)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()