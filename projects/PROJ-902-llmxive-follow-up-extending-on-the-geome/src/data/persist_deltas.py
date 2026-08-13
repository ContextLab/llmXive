"""
Persist per‑layer weight delta files produced by the OPD baseline training
script and generate SHA‑256 checksums for the persisted artifacts.

The script copies all regular files from a source directory to a destination
directory (creating it if necessary) and then writes a ``checksums.txt`` file
containing one ``<sha256>  <relative_path>`` line per file.

The implementation re‑uses the generic checksum utilities defined in
``src/data/checksums.py`` so that checksum handling is consistent across the
project.
"""

import argparse
import shutil
from pathlib import Path
from typing import Mapping, Optional

from src.data.checksums import compute_all_checksums, write_checksums


def persist_deltas(
    source_dir: Path,
    dest_dir: Path,
    checksum_file: Optional[Path] = None,
) -> Mapping[str, str]:
    """
    Copy per‑layer weight delta files from ``source_dir`` into ``dest_dir`` and
    generate SHA‑256 checksums for the copied files.

    Parameters
    ----------
    source_dir: Path
        Directory that already contains the delta files (produced by
        ``src.train.opd_baseline.save_weight_deltas`` or a similar routine).
    dest_dir: Path
        Target directory where the deltas will be persisted.  The directory is
        created if it does not exist.
    checksum_file: Optional[Path]
        Path to the file that will receive the checksum listing.  If ``None``,
        a file named ``checksums.txt`` inside ``dest_dir`` is used.

    Returns
    -------
    Mapping[str, str]
        Mapping from relative file name to its SHA‑256 hex digest.
    """
    source_dir = Path(source_dir)
    dest_dir = Path(dest_dir)

    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy each regular file (ignore sub‑directories – the baseline script writes
    # a flat collection of per‑layer files).
    for item in source_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, dest_dir / item.name)

    # Compute checksums for everything now present in the destination directory.
    checksums = compute_all_checksums(dest_dir)

    # Determine where to write the checksum manifest.
    if checksum_file is None:
        checksum_file = dest_dir / "checksums.txt"
    else:
        checksum_file = Path(checksum_file)

    write_checksums(checksums, checksum_file)

    return checksums


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Persist OPD baseline per‑layer weight deltas and generate SHA‑256 "
            "checksums."
        )
    )
    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Directory containing the per‑layer delta files produced by the baseline script.",
    )
    parser.add_argument(
        "--dest",
        default=Path("data/baseline_deltas"),
        type=Path,
        help="Directory where deltas will be persisted (default: data/baseline_deltas).",
    )
    parser.add_argument(
        "--checksum-file",
        type=Path,
        default=None,
        help=(
            "Optional explicit path for the checksum manifest. If omitted, "
            "a file named 'checksums.txt' inside the destination directory is used."
        ),
    )
    return parser


def main(argv: Optional[list] = None) -> None:
    """
    Command‑line entry point.

    Example
    -------
    >>> python -m src.data.persist_deltas --source data/opd_deltas --dest data/baseline_deltas
    """
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    persist_deltas(args.source, args.dest, args.checksum_file)


if __name__ == "__main__":
    main()
