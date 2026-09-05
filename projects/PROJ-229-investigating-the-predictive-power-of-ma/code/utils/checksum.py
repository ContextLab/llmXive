"""
utils/checksum.py
-----------------

This module provides utilities to compute SHA256 checksums for files in a
directory and write them to an output manifest. It is used by task T008a to
generate checksums for all raw data files after they have been fetched, and
by task T008b to generate checksums for all *processed* data files after
feature engineering.

The script can be executed directly:

    python code/utils/checksum.py

By default it scans ``data/raw`` (the behaviour required for T008a) and
writes the results to ``data/checksums.txt``.  With the ``--stage`` flag set
to ``processed`` it scans ``data/processed`` and appends the new checksums
to the same manifest file (required for T008b).

Both paths can be overridden via command‑line arguments.
"""

import argparse
import hashlib
import logging
from pathlib import Path
from typing import List, Tuple

# Configure a simple module‑level logger. The project already provides a
# logger utility, but importing it would create a circular dependency for
# this low‑level module. Using the standard library logger keeps the module
# self‑contained and easy to test.
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 checksum of a single file.

    Parameters
    ----------
    file_path : Path
        Path to the file whose checksum should be calculated.

    Returns
    -------
    str
        Hexadecimal SHA256 digest.
    """
    logger.debug(f"Computing SHA256 for {file_path}")
    hasher = hashlib.sha256()
    # Read the file in chunks to avoid loading large files into memory.
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    checksum = hasher.hexdigest()
    logger.debug(f"Checksum for {file_path}: {checksum}")
    return checksum


def scan_directory(directory: Path) -> List[Path]:
    """
    Recursively list all regular files within ``directory``.

    Parameters
    ----------
    directory : Path
        The directory to scan.

    Returns
    -------
    List[Path]
        A list of absolute ``Path`` objects for each file found.
    """
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")
    logger.info(f"Scanning directory: {directory}")
    # ``rglob`` yields files matching the pattern; ``*`` matches everything.
    files = [p for p in directory.rglob("*") if p.is_file()]
    logger.debug(f"Found {len(files)} files")
    return files


def generate_checksums(
    input_dir: Path,
    output_file: Path,
    relative_to: Path = None,
    mode: str = "write",
) -> None:
    """
    Compute SHA256 checksums for all files in ``input_dir`` and write them
    to ``output_file``.

    The output format mirrors the classic ``sha256sum`` utility:

        <checksum>  <relative_path>

    Parameters
    ----------
    input_dir : Path
        Directory containing the data files.
    output_file : Path
        Destination file where the checksum manifest will be written.
    relative_to : Path, optional
        Base path used to compute the relative file path stored in the
        manifest. If ``None``, ``input_dir`` is used.
    mode : {"write", "append"}
        ``write`` overwrites any existing manifest (used for the raw stage);
        ``append`` adds new lines to the existing file (used for the processed
        stage) so that both raw and processed checksums coexist in a single
        ``checksums.txt`` file.
    """
    input_dir = input_dir.resolve()
    output_file = output_file.resolve()
    base_path = (relative_to or input_dir).resolve()

    logger.info(f"Generating checksums for {input_dir} (mode={mode})")
    files = scan_directory(input_dir)

    # Ensure the parent directory of the output file exists.
    output_file.parent.mkdir(parents=True, exist_ok=True)

    write_mode = "a" if mode == "append" else "w"
    with output_file.open(write_mode, encoding="utf-8") as out_f:
        for file_path in files:
            checksum = compute_sha256(file_path)
            rel_path = file_path.relative_to(base_path)
            out_f.write(f"{checksum}  {rel_path}\n")
            logger.debug(f"Wrote checksum for {rel_path}")

    logger.info(f"Checksum manifest {'appended to' if mode == 'append' else 'written to'} {output_file}")


def _parse_args() -> argparse.Namespace:
    """
    Parse command‑line arguments for the script entry point.
    """
    parser = argparse.ArgumentParser(
        description="Generate SHA256 checksums for all files in a directory."
    )
    parser.add_argument(
        "--stage",
        choices=["raw", "processed"],
        default="raw",
        help=(
            "Select which data stage to checksum. ``raw`` scans ``data/raw`` "
            "(default) and overwrites the manifest. ``processed`` scans "
            "``data/processed`` and appends to the existing manifest."
        ),
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help=(
            "Override the directory to scan. If omitted, the directory is "
            "chosen based on ``--stage`` (raw => data/raw, processed => data/processed)."
        ),
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("data/checksums.txt"),
        help="File to write the checksum manifest (default: data/checksums.txt).",
    )
    parser.add_argument(
        "--relative-to",
        type=Path,
        default=None,
        help=(
            "Base path for relative file names in the manifest. "
            "If omitted, defaults to the input directory."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """
    Script entry point.

    Determines the stage (raw or processed), selects the appropriate input
    directory, and generates (or appends) the checksum manifest.
    """
    args = _parse_args()

    # Resolve which directory to scan.
    if args.input_dir is not None:
        input_dir = args.input_dir
    else:
        input_dir = Path("data/raw") if args.stage == "raw" else Path("data/processed")

    mode = "write" if args.stage == "raw" else "append"

    try:
        generate_checksums(
            input_dir=input_dir,
            output_file=args.output_file,
            relative_to=args.relative_to,
            mode=mode,
        )
    except Exception as exc:
        logger.error(f"Failed to generate checksums: {exc}")
        raise


if __name__ == "__main__":
    main()