import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

from config import get_config
from utils.logging import get_logger


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger = get_logger("hash_artifacts")
        logger.error(f"Failed to hash {file_path}: {e}")
        raise


def scan_directory(directory: Path, extensions: List[str] = None) -> List[Path]:
    """Recursively scan a directory for files, optionally filtering by extensions."""
    files: List[Path] = []
    if not directory.exists():
        return files

    for item in directory.rglob("*"):
        if item.is_file():
            if extensions is None:
                files.append(item)
            else:
                if item.suffix.lower() in extensions:
                    files.append(item)
    return files


def hash_artifacts(
    directories: List[Path],
    output_path: Path,
    extensions: List[str] = None,
) -> Dict[str, Any]:
    """
    Hash all artifacts in the given directories and write a manifest JSON file.

    Parameters
    ----------
    directories: List[Path]
        List of directories to walk recursively.
    output_path: Path
        Destination path for the JSON manifest.
    extensions: List[str] | None
        Optional list of file extensions to include (e.g., ['.csv', '.json']).
        If None, all files are hashed.

    Returns
    -------
    Dict[str, Any]
        Summary of the hashing operation.
    """
    logger = get_logger("hash_artifacts")
    logger.info(f"Starting artifact hashing for directories: {directories}")

    results: Dict[str, Any] = {
        "status": "success",
        "files": {},
        "summary": {
            "total_files": 0,
            "total_size_bytes": 0,
            "directories_processed": [],
        },
    }

    for directory in directories:
        if not directory.exists():
            logger.warning(f"Directory does not exist, skipping: {directory}")
            results["summary"]["directories_processed"].append(
                {"path": str(directory), "status": "skipped", "reason": "not_exists"}
            )
            continue

        logger.info(f"Processing directory: {directory}")
        files = scan_directory(directory, extensions)

        dir_status = {
            "path": str(directory),
            "status": "processed",
            "files_count": len(files),
            "total_size_bytes": 0,
        }

        for file_path in files:
            try:
                file_size = file_path.stat().st_size
                file_hash = calculate_sha256(file_path)
                # Store paths relative to the project root (cwd)
                relative_path = str(file_path.relative_to(Path.cwd()))

                results["files"][relative_path] = {
                    "hash": file_hash,
                    "size_bytes": file_size,
                }

                dir_status["total_size_bytes"] += file_size
                results["summary"]["total_size_bytes"] += file_size
                results["summary"]["total_files"] += 1
            except Exception as e:
                logger.error(f"Failed to hash {file_path}: {e}")
                results["files"][str(file_path)] = {
                    "error": str(e),
                    "hash": None,
                    "size_bytes": None,
                }

        results["summary"]["directories_processed"].append(dir_status)

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Hash manifest saved to {output_path}")
    logger.info(f"Total files processed: {results['summary']['total_files']}")
    return results


def main() -> int:
    """
    Entry point for the artifact hashing script.

    Hashes all files under the project's ``data/`` and ``code/`` directories
    and writes a manifest to ``state/hashes.json``.
    """
    logger = get_logger("hash_artifacts")
    config = get_config()

    # Resolve key directories via the configuration manager
    data_dir = config.get_path("data_root")
    code_dir = config.get_path("code_root")
    state_dir = config.get_path("state_root")

    directories_to_hash = [data_dir, code_dir]

    # Output manifest location
    output_path = state_dir / "hashes.json"

    # No extension filter – hash every file
    extensions: List[str] = None

    try:
        hash_artifacts(directories_to_hash, output_path, extensions)
        logger.info(
            f"Successfully hashed {len(directories_to_hash)} directories."
        )
        return 0
    except Exception as e:
        logger.error(f"Artifact hashing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())