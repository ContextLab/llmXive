"""Utility for generating and verifying SHA‑256 checksums of files.

This module provides a small command‑line interface used by the project's
quick‑start run‑book. It supports two sub‑commands:

* ``generate`` – walk a directory (recursively) and write a JSON file that
  maps each file's relative path to its SHA‑256 hash.
* ``verify`` – read a previously generated JSON file and compare the stored
  hashes with the current contents of the files. A concise report is printed
  and the process exits with a non‑zero status code if any file fails the
  check.

The implementation is deliberately self‑contained and does not depend on
any third‑party packages beyond the Python standard library, satisfying the
project's constraint of using only declared dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable

__all__ = [
    "compute_sha256",
    "generate_checksums",
    "write_checksums_file",
    "load_checksums",
    "verify_checksums",
    "main",
]


def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """Return the SHA‑256 hex digest of *file_path*.

    The file is read in binary mode using a configurable chunk size to
    avoid loading large files completely into memory.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _iter_files(base_dir: Path) -> Iterable[Path]:
    """Yield all regular files under *base_dir* (recursively)."""
    for root, _, files in os.walk(base_dir):
        for name in files:
            yield Path(root) / name


def generate_checksums(base_dir: Path) -> Dict[str, str]:
    """Generate a mapping ``relative_path -> sha256`` for *base_dir*.

    The returned dictionary uses POSIX‑style (forward‑slash) relative paths
    so that the JSON file is portable across operating systems.
    """
    base_dir = base_dir.resolve()
    checksums: Dict[str, str] = {}
    for file_path in _iter_files(base_dir):
        # Skip the checksum file itself if it already exists inside *base_dir*
        if file_path.name == "checksums.json":
            continue
        rel_path = file_path.relative_to(base_dir).as_posix()
        checksums[rel_path] = compute_sha256(file_path)
    return checksums


def write_checksums_file(checksums: Dict[str, str], output_path: Path) -> None:
    """Write *checksums* as pretty‑printed JSON to *output_path*."""
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(checksums, fp, indent=2, sort_keys=True)


def load_checksums(checksums_path: Path) -> Dict[str, str]:
    """Load a JSON checksum mapping from *checksums_path*."""
    with checksums_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def verify_checksums(
    base_dir: Path,
    checksums_path: Path,
) -> bool:
    """Verify that files under *base_dir* match the hashes in *checksums_path*.

    Returns ``True`` if **all** files match, otherwise ``False``. A human‑readable
    report is printed to ``stdout``. Missing or extra files are also reported.
    """
    base_dir = base_dir.resolve()
    checksums_path = checksums_path.resolve()

    if not checksums_path.is_file():
        print("Checksum verification FAILED.")
        print("==================================================")
        print(f"Checksums file missing: {checksums_path}")
        print("==================================================")
        return False

    stored = load_checksums(checksums_path)

    # Gather current files (excluding the checksum file itself)
    current_files = {
        p.relative_to(base_dir).as_posix(): p
        for p in _iter_files(base_dir)
        if p.name != checksums_path.name
    }

    total = len(stored)
    valid = 0
    failed = 0
    missing = []

    for rel_path, expected_hash in stored.items():
        file_path = current_files.get(rel_path)
        if file_path is None or not file_path.is_file():
            missing.append(rel_path)
            continue
        actual_hash = compute_sha256(file_path)
        if actual_hash == expected_hash:
            valid += 1
        else:
            failed += 1
            print(f"✗ MISMATCH: {rel_path}")
            print(f"    expected: {expected_hash}")
            print(f"    actual  : {actual_hash}")

    # Report missing files
    for rel_path in missing:
        print(f"✗ MISSING: {rel_path}")

    print("==================================================")
    print(f"Total files checked: {total}")
    print(f"Valid files: {valid}")
    print(f"Failed files: {failed + len(missing)}")
    if failed or missing:
        print("\nFailed files:")
        for rel_path in missing:
            print(f"  ✗ {rel_path} (missing)")
        for rel_path, expected_hash in stored.items():
            if rel_path not in missing:
                file_path = current_files[rel_path]
                actual_hash = compute_sha256(file_path)
                if actual_hash != expected_hash:
                    print(f"  ✗ {rel_path}")
        print("==================================================")
        print("Checksum verification FAILED.")
        return False
    else:
        print("All checksums match.")
        print("==================================================")
        return True


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or verify SHA‑256 checksums for a directory."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate sub‑command
    gen_parser = subparsers.add_parser(
        "generate", help="Create a checksums.json file for a directory."
    )
    gen_parser.add_argument(
        "--directory",
        "-d",
        type=Path,
        default=Path("data/processed"),
        help="Directory to walk (default: data/processed).",
    )
    gen_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("data/processed/checksums.json"),
        help="Path of the JSON file to write (default: data/processed/checksums.json).",
    )

    # verify sub‑command
    ver_parser = subparsers.add_parser(
        "verify", help="Verify files against an existing checksums.json."
    )
    ver_parser.add_argument(
        "--directory",
        "-d",
        type=Path,
        default=Path("data/processed"),
        help="Directory containing the files to verify (default: data/processed).",
    )
    ver_parser.add_argument(
        "--checksums",
        "-c",
        type=Path,
        default=Path("data/processed/checksums.json"),
        help="Path to the checksums JSON file (default: data/processed/checksums.json).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the command‑line interface."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        checksums = generate_checksums(args.directory)
        write_checksums_file(checksums, args.output)
        print(f"Checksums written to {args.output}")
    elif args.command == "verify":
        success = verify_checksums(args.directory, args.checksums)
        # Exit code 0 on success, 1 on any failure
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
