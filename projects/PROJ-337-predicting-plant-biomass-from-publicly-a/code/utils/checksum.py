import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple

from code.utils.logger import get_logger


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file to compute the checksum for.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files without OOM
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def generate_checksums_for_directory(
    directory_path: Path,
    algorithm: str = "sha256",
    recursive: bool = True,
    extensions: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.

    Args:
        directory_path: Path to the directory to scan.
        algorithm: Hash algorithm to use.
        recursive: Whether to scan subdirectories.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                   If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their checksums.

    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")

    checksums = {}
    logger = get_logger(__name__)

    if recursive:
        iterator = directory_path.rglob("*")
    else:
        iterator = directory_path.glob("*")

    for file_path in iterator:
        if file_path.is_file():
            # Filter by extension if specified
            if extensions is not None:
                if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
                    continue

            try:
                relative_path = file_path.relative_to(directory_path)
                checksum = compute_file_checksum(file_path, algorithm)
                checksums[str(relative_path)] = checksum
                logger.debug(f"Computed checksum for {relative_path}")
            except Exception as e:
                logger.warning(f"Failed to compute checksum for {file_path}: {e}")

    return checksums


def save_checksums(checksums: Dict[str, str], output_path: Path, algorithm: str = "sha256") -> None:
    """
    Save checksums to a JSON manifest file.

    Args:
        checksums: Dictionary of relative paths to checksums.
        output_path: Path to the output manifest file.
        algorithm: The algorithm used to generate the checksums (stored in metadata).
    """
    manifest = {
        "algorithm": algorithm,
        "created_at": None,  # Could add timestamp if needed
        "checksums": checksums,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_checksums(manifest_path: Path) -> Tuple[str, Dict[str, str]]:
    """
    Load checksums from a manifest file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Tuple of (algorithm, checksums dictionary).

    Raises:
        FileNotFoundError: If the manifest does not exist.
        json.JSONDecodeError: If the manifest is invalid JSON.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if "checksums" not in manifest:
        raise ValueError("Invalid manifest format: missing 'checksums' key")
    if "algorithm" not in manifest:
        raise ValueError("Invalid manifest format: missing 'algorithm' key")

    return manifest["algorithm"], manifest["checksums"]


def verify_checksums(
    base_directory: Path,
    manifest_path: Path,
    strict: bool = True,
) -> Tuple[bool, List[str], List[str]]:
    """
    Verify file checksums against a manifest.

    Args:
        base_directory: The root directory where files are located (checksums are relative to this).
        manifest_path: Path to the checksum manifest file.
        strict: If True, fail if any file is missing or checksum mismatch.
               If False, return lists of issues.

    Returns:
        Tuple of (all_valid, missing_files, mismatched_files).
        all_valid is True only if no issues found.

    Raises:
        FileNotFoundError: If the manifest does not exist.
    """
    algorithm, expected_checksums = load_checksums(manifest_path)

    missing_files = []
    mismatched_files = []
    verified_count = 0

    for relative_path_str, expected_checksum in expected_checksums.items():
        file_path = base_directory / relative_path_str

        if not file_path.exists():
            missing_files.append(relative_path_str)
            continue

        try:
            actual_checksum = compute_file_checksum(file_path, algorithm)
            if actual_checksum != expected_checksum:
                mismatched_files.append(relative_path_str)
            else:
                verified_count += 1
        except Exception as e:
            mismatched_files.append(f"{relative_path_str} (error: {e})")

    all_valid = len(missing_files) == 0 and len(mismatched_files) == 0

    if strict and not all_valid:
        error_msg = []
        if missing_files:
            error_msg.append(f"Missing files ({len(missing_files)}): {', '.join(missing_files)}")
        if mismatched_files:
            error_msg.append(f"Mismatched files ({len(mismatched_files)}): {', '.join(mismatched_files)}")
        raise ValueError("Checksum verification failed: " + "; ".join(error_msg))

    return all_valid, missing_files, mismatched_files


def main() -> None:
    """
    CLI entry point for checksum utilities.

    Usage:
      # Generate checksums for a directory:
      python code/utils/checksum.py generate --dir data/raw --output data/raw_checksums.json

      # Verify checksums:
      python code/utils/checksum.py verify --dir data/raw --manifest data/raw_checksums.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Checksum verification utilities")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate checksums for a directory")
    gen_parser.add_argument("--dir", required=True, help="Directory to scan")
    gen_parser.add_argument("--output", required=True, help="Output manifest file path")
    gen_parser.add_argument("--algorithm", default="sha256", help="Hash algorithm (default: sha256)")
    gen_parser.add_argument("--recursive", action="store_true", default=True, help="Scan subdirectories (default: True)")
    gen_parser.add_argument("--extensions", nargs="+", help="File extensions to include (e.g., .csv .json)")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify checksums against a manifest")
    verify_parser.add_argument("--dir", required=True, help="Base directory containing files")
    verify_parser.add_argument("--manifest", required=True, help="Checksum manifest file path")
    verify_parser.add_argument("--strict", action="store_true", default=True, help="Fail on any error (default: True)")

    args = parser.parse_args()

    logger = get_logger(__name__)

    if args.command == "generate":
        dir_path = Path(args.dir)
        output_path = Path(args.output)

        extensions = [ext if ext.startswith(".") else f".{ext}" for ext in args.extensions] if args.extensions else None

        logger.info(f"Generating checksums for {dir_path}...")
        checksums = generate_checksums_for_directory(
            dir_path,
            algorithm=args.algorithm,
            recursive=args.recursive,
            extensions=extensions,
        )

        save_checksums(checksums, output_path, args.algorithm)
        logger.info(f"Saved {len(checksums)} checksums to {output_path}")

    elif args.command == "verify":
        base_dir = Path(args.dir)
        manifest_path = Path(args.manifest)

        logger.info(f"Verifying checksums for {base_dir} using {manifest_path}...")
        all_valid, missing, mismatched = verify_checksums(
            base_dir,
            manifest_path,
            strict=args.strict,
        )

        if all_valid:
            logger.info("✅ All checksums verified successfully.")
        else:
            if missing:
                logger.error(f"❌ Missing files ({len(missing)}): {missing}")
            if mismatched:
                logger.error(f"❌ Mismatched files ({len(mismatched)}): {mismatched}")
            if not args.strict:
                logger.warning("Verification completed with errors (non-strict mode).")
            else:
                raise SystemExit(1)
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
