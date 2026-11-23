"""
verify_stimuli.py

This script verifies the integrity of stimulus files by computing their SHA‑256
checksums and comparing them against a reference manifest. The computed checksums
are also recorded in ``state/artifact_hashes.json`` for downstream tasks.

The reference manifest is expected to be a JSON file mapping relative stimulus file
paths (relative to the stimuli directory) to their expected SHA‑256 hash strings.
By default the manifest is located at ``data/stimuli/raw/checksums.json`` and the
output is written to ``state/artifact_hashes.json``.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict

from src.lib.utils import compute_file_checksum

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Load the JSON manifest containing expected checksums.

    Parameters
    ----------
    manifest_path: Path
        Path to the JSON manifest file.

    Returns
    ----------
    Dict[str, str]
        Mapping of relative file paths (as strings) to expected SHA‑256 hex digests.
    """
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Checksum manifest must be a JSON object mapping file names to hashes.")
    return {str(k): str(v) for k, v in data.items()}


def compute_checksums(stimuli_dir: Path) -> Dict[str, str]:
    """
    Compute SHA‑256 checksums for all files in ``stimuli_dir`` (non‑recursive).

    Parameters
    ----------
    stimuli_dir: Path
        Directory containing stimulus files.

    Returns
    ----------
    Dict[str, str]
        Mapping of relative file paths (as strings) to computed SHA‑256 hex digests.
    """
    if not stimuli_dir.is_dir():
        raise NotADirectoryError(f"Stimuli directory does not exist: {stimuli_dir}")

    checksums: Dict[str, str] = {}
    for file_path in sorted(stimuli_dir.iterdir()):
        if file_path.is_file():
            rel_path = file_path.relative_to(stimuli_dir).as_posix()
            checksum = compute_file_checksum(file_path)
            checksums[rel_path] = checksum
            logger.debug("Computed checksum for %s: %s", rel_path, checksum)
    return checksums


def verify_stimuli(
    stimuli_dir: Path,
    manifest_path: Path,
    output_path: Path,
) -> None:
    """
    Verify stimulus checksums against a reference manifest.

    The function will:
    1. Load the reference manifest.
    2. Compute checksums for all files present in ``stimuli_dir``.
    3. Compare each computed checksum with the expected value.
    4. Write the computed checksums to ``output_path`` (JSON).
    5. Raise ``SystemExit`` with a non‑zero status if any mismatch or missing file is found.

    Parameters
    ----------
    stimuli_dir: Path
        Directory containing the stimulus files.
    manifest_path: Path
        Path to the JSON manifest with expected checksums.
    output_path: Path
        Path where the computed checksum mapping will be saved.
    """
    logger.info("Loading reference checksum manifest from %s", manifest_path)
    expected = load_manifest(manifest_path)

    logger.info("Computing checksums for stimuli in %s", stimuli_dir)
    computed = compute_checksums(stimuli_dir)

    # Write computed checksums to the output location for downstream consumption.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(computed, f, indent=2, sort_keys=True)
    logger.info("Recorded computed checksums to %s", output_path)

    # Verify presence and equality.
    mismatches = []
    missing = []

    for rel_path, expected_hash in expected.items():
        if rel_path not in computed:
            missing.append(rel_path)
        elif computed[rel_path] != expected_hash:
            mismatches.append((rel_path, expected_hash, computed[rel_path]))

    if missing:
        logger.error("Missing stimulus files: %s", ", ".join(missing))
    if mismatches:
        for rel_path, exp, got in mismatches:
            logger.error(
                "Checksum mismatch for %s – expected %s, got %s",
                rel_path,
                exp,
                got,
            )

    if missing or mismatches:
        raise SystemExit(1)

    logger.info("All stimulus checksums match the reference manifest.")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify stimulus file integrity by comparing SHA‑256 checksums."
    )
    parser.add_argument(
        "--stimuli-dir",
        type=Path,
        default=Path("data/stimuli/raw"),
        help="Directory containing stimulus files (default: data/stimuli/raw).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/stimuli/raw/checksums.json"),
        help="JSON file mapping stimulus relative paths to expected SHA‑256 hashes.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("state/artifact_hashes.json"),
        help="Path where computed checksums will be stored (default: state/artifact_hashes.json).",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    try:
        verify_stimuli(
            stimuli_dir=args.stimuli_dir,
            manifest_path=args.manifest,
            output_path=args.output,
        )
    except Exception as exc:
        logger.exception("Verification failed: %s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()