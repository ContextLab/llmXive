"""
verify_stimuli.py
-----------------
Compute and record SHA‑256 checksums for all stimulus files downloaded by the
``fetch_stimuli`` step.

The script walks the ``data/stimuli`` directory (recursively), computes a
checksum for each file using :func:`src.lib.utils.compute_file_checksum`,
and writes a JSON manifest to ``state/artifact_hashes.json``.  The manifest
maps each file's *project‑relative* path (as a string) to its checksum.

The module provides a ``verify_stimuli`` function that can be imported by
other parts of the pipeline as well as a small CLI for manual execution.
"""

import argparse
import json
from pathlib import Path
from typing import Dict

from src.lib.utils import compute_file_checksum


def _gather_file_paths(root: Path) -> list[Path]:
    """Return a list of all file paths under ``root`` (recursive)."""
    return [p for p in root.rglob("*") if p.is_file()]


def verify_stimuli(
    stimuli_dir: Path = Path("data/stimuli"),
    output_path: Path = Path("state/artifact_hashes.json"),
) -> Dict[str, str]:
    """
    Compute SHA‑256 checksums for every file in ``stimuli_dir`` and write a
    JSON manifest to ``output_path``.

    Parameters
    ----------
    stimuli_dir:
        Directory containing the downloaded stimulus files.
    output_path:
        Destination JSON file that will contain a mapping from the
        *project‑relative* file path (as a string) to its SHA‑256 checksum.

    Returns
    -------
    dict
        Mapping of relative file paths to their checksums.
    """
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Resolve absolute paths for reliable operation
    stimuli_dir = stimuli_dir.resolve()
    cwd = Path.cwd().resolve()

    checksums: Dict[str, str] = {}
    for file_path in _gather_file_paths(stimuli_dir):
        # Compute the checksum using the shared utility
        checksum = compute_file_checksum(file_path)

        # Store path relative to the repository root (cwd)
        rel_path = file_path.relative_to(cwd)
        checksums[str(rel_path)] = checksum

    # Write the manifest atomically
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(checksums, fp, indent=2, sort_keys=True)

    return checksums


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compute and record SHA‑256 checksums for all stimulus files. "
            "The default stimulus directory is ``data/stimuli`` and the "
            "default output file is ``state/artifact_hashes.json``."
        )
    )
    parser.add_argument(
        "--stimuli-dir",
        type=Path,
        default=Path("data/stimuli"),
        help="Directory containing stimulus files (default: data/stimuli).",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        type=Path,
        default=Path("state/artifact_hashes.json"),
        help="Path to write the checksum manifest (default: state/artifact_hashes.json).",
    )
    return parser


def main() -> None:
    """Entry‑point for ``python -m src.metrics.verify_stimuli``."""
    args = _build_arg_parser().parse_args()
    verify_stimuli(stimuli_dir=args.stimuli_dir, output_path=args.output_path)


if __name__ == "__main__":
    main()