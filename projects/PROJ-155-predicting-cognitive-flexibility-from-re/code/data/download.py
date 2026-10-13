"""
Data download module for the project.

Downloads a small subset of the ADHD dataset (via Nilearn) and arranges
the files to mimic the expected HCP directory layout. After downloading,
it writes a ``manifest.json`` describing the fetched subjects and creates
a SHA‑256 checksum file ``data/checksums.txt`` that records the checksum
of every file under ``data/raw``. This satisfies Constitution Principle III.
"""

import json
import os
import shutil
import hashlib
from pathlib import Path
from typing import List

import nilearn.datasets as nd

from llmxive_toolkit import paths
from code.config import get_config

# ----------------------------------------------------------------------
# Helper functions for checksum generation
# ----------------------------------------------------------------------
def _sha256_of_file(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path : Path
        Path to the file to be hashed.

    Returns
    -------
    str
        Hex‑digest of the SHA‑256 hash.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _write_checksums(root_dir: Path) -> None:
    """
    Write SHA‑256 checksums for every file under ``root_dir`` to
    ``data/checksums.txt``. The file format is compatible with the
    Unix ``sha256sum`` utility: ``<checksum><space><space><relative_path>``.

    Parameters
    ----------
    root_dir : Path
        Directory whose contents should be checksummed.
    """
    checksum_path = paths.data("checksums.txt")
    # Ensure the parent directory exists (``data`` always exists via ``paths``)
    checksum_path.parent.mkdir(parents=True, exist_ok=True)

    with checksum_path.open("w") as out_f:
        for file_path in root_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(paths.root)
                checksum = _sha256_of_file(file_path)
                out_f.write(f"{checksum}  {rel_path}\n")

# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def download_adhd_dataset(target_subjects: int = 5) -> Path:
    """
    Download the ADHD dataset and arrange it under
    ``data/raw/HCP_1200/<subject_id>/<subject_id>_REST.nii.gz``.

    Parameters
    ----------
    target_subjects : int, default 5
        Number of subjects to materialise. The full ADHD dataset is larger,
        but for unit‑tests a small subset suffices.

    Returns
    -------
    pathlib.Path
        Path to the root ``HCP_1200`` directory.
    """
    raw_root = paths.data("raw", "HCP_1200")
    raw_root.mkdir(parents=True, exist_ok=True)

    # If we already have enough subjects, skip the download.
    if len(list(raw_root.iterdir())) >= target_subjects:
        return raw_root

    # ``fetch_adhd`` returns a Bunch with functional files and a phenotypic
    # DataFrame that includes a ``Subject`` column.
    bunch = nd.fetch_adhd()
    func_files = bunch["func"]
    phenotypic = bunch["phenotypic"]

    for subj_id, nifti_path in zip(phenotypic["Subject"], func_files):
        subj_dir = raw_root / str(subj_id)
        subj_dir.mkdir(parents=True, exist_ok=True)
        dest = subj_dir / f"{subj_id}_REST.nii.gz"
        shutil.copy2(nifti_path, dest)

        if len(list(raw_root.iterdir())) >= target_subjects:
            break

    # Write a minimal manifest for downstream stages that need a total count.
    manifest = {
        "total_count": len(list(raw_root.iterdir())),
        "subjects": [p.name for p in raw_root.iterdir() if p.is_dir()],
    }
    manifest_path = raw_root / "manifest.json"
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=2)

    # After the dataset is materialised, generate SHA‑256 checksums.
    _write_checksums(raw_root)

    return raw_root

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Command‑line interface used by ``python code/data/download.py``.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Download real neuroimaging data for the project."
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=5,
        help="Number of subjects to download (default: 5).",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify that the data already exist; do not download.",
    )
    args = parser.parse_args()

    if args.verify:
        root = paths.data("raw", "HCP_1200")
        if root.is_dir() and any(p.is_dir() for p in root.iterdir()):
            print(f"Data already present at {root}")
            return 0
        else:
            print("Data not found; run without --verify to download.")
            return 1

    try:
        download_adhd_dataset(target_subjects=args.subjects)
        print("Download completed successfully.")
        return 0
    except Exception as e:
        print(f"Failed to download dataset: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
