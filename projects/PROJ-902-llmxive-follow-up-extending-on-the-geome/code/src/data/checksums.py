"""
GSM8K checksum utility.

This module provides functions to compute SHA‑256 checksums for all files
under ``data/gsm8k/``, persist them to ``data/checksums.txt`` and validate the
stored hashes against the current files.

It is deliberately lightweight and depends only on the helper functions
already implemented in ``src.data.download_gsm8k`` (``compute_sha256``,
``save_checksums`` and ``load_checksums``).  The checksum file is a simple
JSON mapping from relative file path (relative to ``data/gsm8k/``) to the
hexadecimal SHA‑256 digest.

The script can be executed directly:

    $ python -m src.data.checksums

which will (re)compute the checksums, write ``data/checksums.txt`` and then
validate the freshly‑written file.
"""

import json
from pathlib import Path
from typing import Dict

# Re‑use the existing helpers from the download module.
from src.data.download_gsm8k import compute_sha256, save_checksums, load_checksums


def _project_root() -> Path:
    """Return the absolute path to the repository root."""
    # ``checksums.py`` lives in ``<repo>/src/data`` → two parents up is the root.
    return Path(__file__).resolve().parents[2]


def _gsm8k_dir() -> Path:
    """Return the path to the GSM8K dataset directory."""
    return _project_root() / "data" / "gsm8k"


def _checksums_file() -> Path:
    """Return the path to the checksum file."""
    return _project_root() / "data" / "checksums.txt"


def compute_all_checksums() -> Dict[str, str]:
    """
    Compute SHA‑256 checksums for every regular file inside ``data/gsm8k``.

    Returns
    -------
    dict
        Mapping from file path **relative to ``data/gsm8k``** to its hex digest.
    """
    base_dir = _gsm8k_dir()
    if not base_dir.is_dir():
        raise FileNotFoundError(f"GSM8K directory not found at {base_dir}")

    checksums: Dict[str, str] = {}
    for file_path in base_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(base_dir)
            checksums[str(rel_path)] = compute_sha256(file_path)

    return checksums


def write_checksums() -> None:
    """
    Compute the checksums and write them to ``data/checksums.txt`` using the
    ``save_checksums`` helper from ``download_gsm8k``.
    """
    checksums = compute_all_checksums()
    checksum_path = _checksums_file()
    # Ensure the parent directory exists (it always should, but be defensive).
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    save_checksums(checksums, checksum_path)


def validate_checksums() -> bool:
    """
    Validate that every file listed in ``data/checksums.txt`` exists and matches
    the stored SHA‑256 hash.

    Returns
    -------
    bool
        ``True`` if all files match; otherwise an exception is raised.

    Raises
    ------
    FileNotFoundError
        If a listed file is missing.
    ValueError
        If a file's checksum does not match the recorded value.
    """
    checksum_path = _checksums_file()
    if not checksum_path.is_file():
        raise FileNotFoundError(f"Checksum file not found at {checksum_path}")

    expected = load_checksums(checksum_path)
    base_dir = _gsm8k_dir()

    for rel_path_str, expected_hash in expected.items():
        file_path = base_dir / rel_path_str
        if not file_path.is_file():
            raise FileNotFoundError(f"Expected file missing: {file_path}")

        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"Checksum mismatch for {file_path}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
    return True


def main() -> None:
    """
    Entry‑point for the module when executed as a script.

    It recomputes the checksums, stores them, and then validates the stored
    values.  Any failure will raise an exception and cause a non‑zero exit
    status, which downstream pipelines can catch to abort execution.
    """
    write_checksums()
    validate_checksums()
    print(f"Checksums written to and validated against {_checksums_file()}")


if __name__ == "__main__":
    main()