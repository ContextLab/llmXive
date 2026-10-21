"""
Checksum utility for verifying data integrity.
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

# Ensure the project root is on the import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import get_path, ensure_dir, PATHS

logger = logging.getLogger(__name__)


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path (Union[str, Path]): Path to the file.

    Returns:
        str: SHA-256 hash as hexadecimal string.
    """
    sha256_hash = hashlib.sha256()
    path_obj = Path(file_path) if isinstance(file_path, str) else file_path

    with open(path_obj, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def verify_raw_data_integrity(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify a file's integrity against an expected hash.

    Args:
        file_path (Union[str, Path]): Path to the file.
        expected_hash (str): Expected SHA-256 hash.

    Returns:
        bool: True if hash matches, False otherwise.
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash


def generate_checksum_file(file_path: Union[str, Path], output_path: Union[str, Path]) -> List[Dict[str, str]]:
    """
    Generate a checksum entry for a given file and write a JSON list
    containing that entry to ``output_path``.

    Args:
        file_path (Union[str, Path]): Path to the file.
        output_path (Union[str, Path]): Path for the checksum file.

    Returns:
        List[Dict[str, str]]: List with a single checksum dictionary.
    """
    file_hash = compute_sha256(file_path)
    checksum_entry = {"path": str(Path(file_path).as_posix()), "sha256": file_hash}

    output_obj = Path(output_path) if isinstance(output_path, str) else output_path
    ensure_dir(output_obj.parent)

    # Consistent schema: JSON list of {path, sha256} entries.
    with open(output_obj, "w", encoding="utf-8") as f:
        json.dump([checksum_entry], f, indent=2)

    logger.info(f"Wrote checksum for {file_path} to {output_path}")
    return [checksum_entry]


def verify_all_raw_data(checksum_file_path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None) -> Dict[str, bool]:
    """
    Verify all files listed in a checksum file.

    The checksum file must contain a JSON **list** where each element is a
    mapping with ``path`` and ``sha256`` keys.

    Args:
        checksum_file_path (Union[str, Path]): Path to the checksum file.
        base_dir (Optional[Union[str, Path]]): Base directory for relative paths.

    Returns:
        Dict[str, bool]: Mapping of file paths to verification results.
    """
    checksum_path = Path(checksum_file_path) if isinstance(checksum_file_path, str) else checksum_file_path

    with open(checksum_path, "r", encoding="utf-8") as f:
        checksum_data = json.load(f)

    if not isinstance(checksum_data, list):
        raise ValueError("Checksum file must contain a JSON list of entries")

    results: Dict[str, bool] = {}
    base_path = Path(base_dir) if base_dir else Path.cwd()

    for entry in checksum_data:
        file_path = entry["path"]
        expected_hash = entry["sha256"]

        # Resolve relative paths against ``base_path`` when needed
        resolved_path = base_path / file_path if not Path(file_path).is_absolute() else Path(file_path)

        if resolved_path.exists():
            results[str(resolved_path)] = verify_raw_data_integrity(resolved_path, expected_hash)
        else:
            results[str(resolved_path)] = False
            logger.warning(f"File listed in checksum not found: {resolved_path}")

    return results


def _create_checksums_for_directory(directory: Path) -> List[Dict[str, str]]:
    """
    Helper that walks ``directory`` and creates a checksum entry for every file.
    """
    entries: List[Dict[str, str]] = []
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            entries.append(
                {"path": str(file_path.relative_to(directory).as_posix()), "sha256": compute_sha256(file_path)}
            )
    return entries


def main() -> None:
    """
    Entry point for the checksum utility.

    - If ``data/raw/checksums.json`` exists, verify all listed files.
    - If the file does **not** exist, create it for every file under
      ``PATHS['raw']`` and then verify.

    The script prints a concise verification report and exits with a
    non‑zero status code if any file fails verification.
    """
    raw_dir: Path = PATHS["raw"]
    # Ensure the raw directory exists before trying to list its contents
    ensure_dir(raw_dir)

    checksum_path: Path = raw_dir / "checksums.json"

    if not checksum_path.exists():
        logger.info(f"No checksum file found at {checksum_path}. Generating one for all files in {raw_dir}...")
        entries = _create_checksums_for_directory(raw_dir)
        ensure_dir(checksum_path.parent)
        with open(checksum_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
        logger.info(f"Checksum file created with {len(entries)} entries.")

    # Perform verification
    logger.info(f"Verifying raw data using checksum file {checksum_path}...")
    verification_results = verify_all_raw_data(checksum_path, base_dir=raw_dir)

    # Summarise results
    all_passed = all(verification_results.values())
    for fp, ok in verification_results.items():
        status = "OK" if ok else "FAIL"
        logger.info(f"{fp}: {status}")

    if not all_passed:
        logger.error("One or more files failed checksum verification.")
        sys.exit(1)
    else:
        logger.info("All raw data files passed checksum verification.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()