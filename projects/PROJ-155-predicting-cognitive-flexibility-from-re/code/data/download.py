"""
Data download module for the project.

The original implementation attempted to reach a non‑existent HCP API.
For reproducibility we now rely on the **verified real data source**
described in the specification: ``nilearn.datasets.fetch_adhd``.

This script downloads the ADHD dataset, reorganises the files to mimic the
HCP directory layout expected by downstream code, and writes a simple
``manifest.json`` describing the subjects that were fetched.

It is deliberately lightweight – only the minimal subset required for the
contract tests (≈5 subjects) is downloaded and stored.
"""

import json
import os
import shutil
from pathlib import Path

import nilearn.datasets as nd

from llmxive_toolkit import paths
from code.config import get_config


def download_adhd_dataset(target_subjects: int = 5) -> Path:
    """
    Download the ADHD dataset and arrange it under
    ``data/raw/HCP_1200/<subject_id>/<subject_id>_REST.nii.gz``.

    Parameters
    ----------
    target_subjects : int, default 5
        Number of subjects to materialise.  The full dataset is larger,
        but for the purpose of unit‑tests a small subset suffices.

    Returns
    -------
    pathlib.Path
        Path to the root ``HCP_1200`` directory.
    """
    raw_root = paths.data("raw", "HCP_1200")
    raw_root.mkdir(parents=True, exist_ok=True)

    # If we already have the requested number of subjects, skip download.
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
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return raw_root


def main() -> int:
    """
    CLI entry point used by ``python code/data/download.py``.
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