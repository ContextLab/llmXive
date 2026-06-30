"""
Data Integrity Check Utility.

Provides functions to verify the integrity of raw data files using checksums.
Supports MD5 and SHA256 algorithms. Generates a manifest for future verification.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Configure logging for this module
logger = logging.getLogger(__name__)

# Default manifest filename
DEFAULT_MANIFEST_NAME = "data_manifest.json"

def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use ('md5' or 'sha256').

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'md5' or 'sha256'.")

    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files (like EEG data) without loading entirely into memory
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError as e:
        logger.error(f"IO Error reading file {file_path}: {e}")
        raise

def scan_directory_for_files(
    directory: Path,
    extensions: List[str] = [".edf", ".gdf", ".vhdr"],
    recursive: bool = True
) -> List[Path]:
    """
    Scan a directory for data files with specific extensions.

    Args:
        directory: Root directory to scan.
        extensions: List of file extensions to look for (e.g., ['.edf']).
        recursive: Whether to scan subdirectories.

    Returns:
        List of Path objects for matching files.
    """
    files = []
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return files

    glob_pattern = "**/*" if recursive else "*"
    for ext in extensions:
        # glob needs the extension to include the dot, e.g., "*.edf"
        pattern = f"{glob_pattern}*{ext}"
        found = list(directory.glob(pattern))
        files.extend(found)
    
    return sorted(files)

def generate_manifest(
    data_dir: Path,
    output_path: Optional[Path] = None,
    algorithm: str = "sha256",
    extensions: List[str] = [".edf", ".gdf", ".vhdr"]
) -> Dict[str, Any]:
    """
    Generate a manifest of checksums for all data files in a directory.

    Args:
        data_dir: Directory containing raw data files.
        output_path: Optional path to save the manifest JSON. If None, manifest is not saved.
        algorithm: Hash algorithm to use.
        extensions: File extensions to include.

    Returns:
        Dictionary containing the manifest data.
    """
    logger.info(f"Generating manifest for directory: {data_dir}")
    files = scan_directory_for_files(data_dir, extensions)
    
    manifest = {
        "algorithm": algorithm,
        "source_directory": str(data_dir),
        "files": {}
    }

    if not files:
        logger.warning(f"No files found with extensions {extensions} in {data_dir}")
        return manifest

    total = len(files)
    for i, file_path in enumerate(files):
        try:
            checksum = calculate_file_checksum(file_path, algorithm)
            # Store relative path for portability
            rel_path = file_path.relative_to(data_dir)
            manifest["files"][str(rel_path)] = {
                "checksum": checksum,
                "size_bytes": file_path.stat().st_size
            }
            logger.debug(f"Checked {i+1}/{total}: {rel_path}")
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")
            manifest["files"][str(file_path)] = {"error": str(e)}

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest saved to {output_path}")

    return manifest

def verify_manifest(
    data_dir: Path,
    manifest_path: Path,
    strict: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify files against a saved manifest.

    Args:
        data_dir: Directory containing the data files.
        manifest_path: Path to the manifest JSON file.
        strict: If True, fail if any file is missing or checksum mismatch.

    Returns:
        Tuple of (is_valid, details_dict).
        details_dict contains:
            - 'valid_files': list of paths with matching checksums
            - 'invalid_files': list of paths with mismatched checksums
            - 'missing_files': list of paths in manifest but not on disk
            - 'new_files': list of paths on disk but not in manifest
            - 'errors': list of paths that caused errors
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    algorithm = manifest.get("algorithm", "sha256")
    expected_files = manifest.get("files", {})

    results = {
        "valid_files": [],
        "invalid_files": [],
        "missing_files": [],
        "new_files": [],
        "errors": []
    }

    # Check expected files
    for rel_path_str, info in expected_files.items():
        full_path = data_dir / rel_path_str
        
        if "error" in info:
            # Error during generation, skip verification for this file
            results["errors"].append(rel_path_str)
            continue

        if not full_path.exists():
            results["missing_files"].append(rel_path_str)
            continue

        try:
            current_checksum = calculate_file_checksum(full_path, algorithm)
            expected_checksum = info["checksum"]

            if current_checksum == expected_checksum:
                results["valid_files"].append(rel_path_str)
            else:
                results["invalid_files"].append(rel_path_str)
                logger.warning(f"Checksum mismatch for {rel_path_str}")
        except Exception as e:
            results["errors"].append(rel_path_str)
            logger.error(f"Error verifying {rel_path_str}: {e}")

    # Check for new files not in manifest
    current_files = scan_directory_for_files(data_dir)
    current_rel_paths = {str(f.relative_to(data_dir)) for f in current_files}
    expected_rel_paths = set(expected_files.keys())
    
    results["new_files"] = list(current_rel_paths - expected_rel_paths)

    is_valid = (
        len(results["invalid_files"]) == 0 and
        len(results["missing_files"]) == 0 and
        len(results["errors"]) == 0
    )

    if strict and not is_valid:
        logger.error("Integrity check FAILED in strict mode.")
    elif is_valid:
        logger.info("Integrity check PASSED.")
    else:
        logger.warning("Integrity check completed with issues.")

    return is_valid, results

def main():
    """
    CLI entry point for the integrity check utility.
    Usage:
      python code/integrity.py generate --dir data/raw
      python code/integrity.py verify --dir data/raw --manifest data/results/manifest.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Data Integrity Check Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate subcommand
    gen_parser = subparsers.add_parser("generate", help="Generate a checksum manifest")
    gen_parser.add_argument("--dir", type=str, required=True, help="Directory containing raw data")
    gen_parser.add_argument("--output", type=str, default=None, help="Output path for manifest (default: data/raw/../results/data_manifest.json)")
    gen_parser.add_argument("--ext", type=str, nargs="+", default=[".edf"], help="File extensions to include")

    # Verify subcommand
    ver_parser = subparsers.add_parser("verify", help="Verify files against a manifest")
    ver_parser.add_argument("--dir", type=str, required=True, help="Directory containing data to verify")
    ver_parser.add_argument("--manifest", type=str, required=True, help="Path to manifest file")
    ver_parser.add_argument("--strict", action="store_true", help="Fail on any mismatch")

    args = parser.parse_args()

    if args.command == "generate":
        data_dir = Path(args.dir)
        if args.output:
            output_path = Path(args.output)
        else:
            # Default output: data/results/manifest.json
            output_path = data_dir.parent / "results" / DEFAULT_MANIFEST_NAME
        
        generate_manifest(data_dir, output_path, extensions=args.ext)
        print(f"Manifest generated at {output_path}")

    elif args.command == "verify":
        data_dir = Path(args.dir)
        manifest_path = Path(args.manifest)
        is_valid, details = verify_manifest(data_dir, manifest_path, strict=args.strict)
        
        print(f"Verification Result: {'PASSED' if is_valid else 'FAILED'}")
        print(f"Valid: {len(details['valid_files'])}")
        print(f"Invalid: {len(details['invalid_files'])}")
        print(f"Missing: {len(details['missing_files'])}")
        print(f"New (unexpected): {len(details['new_files'])}")
        if not is_valid:
            if details['invalid_files']:
                print(f"Invalid files: {details['invalid_files']}")
            if details['missing_files']:
                print(f"Missing files: {details['missing_files']}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
