"""
Data download module for the project.

Downloads a small subset of the HCP 1200‑subject release (via Nilearn) and arranges
the files to mimic the expected directory layout. After downloading, it writes a
``manifest.json`` describing the fetched subjects and creates a SHA‑256 checksum file
``data/checksums.txt`` that records the checksum of every file under ``data/raw``.
This satisfies Constitution Principle III.
"""

import json
import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Any

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
    checksum_path.parent.mkdir(parents=True, exist_ok=True)

    with checksum_path.open("w") as out_f:
        for file_path in root_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(paths.root)
                checksum = _sha256_of_file(file_path)
                out_f.write(f"{checksum}  {rel_path}\\n")


# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def download_adhd_dataset(target_subjects: int = 5) -> Path:
    """
    Download a small subset of the HCP 1200 release (resting‑state fMRI) and
    arrange it under ``data/raw/HCP_1200/<subject_id>/<subject_id>_REST.nii.gz``.

    Parameters
    ----------
    target_subjects : int, default 5
        Number of subjects to materialise. The function will download the
        minimal‑preprocessed HCP REST1_LR run for each subject.

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

    # ------------------------------------------------------------------
    # Fetch HCP REST data (minimal preprocessing) using Nilearn.
    # ------------------------------------------------------------------
    # The HCP fetcher returns a Bunch with:
    #   func      : list of NIfTI file paths (one per subject)
    #   confounds : list of DataFrames with motion and other confounds
    #   phenotypic: DataFrame with demographics & behavioral scores
    # ------------------------------------------------------------------
    try:
        hcp_bundle = nd.fetch_hcp_rest(
            data_dir=raw_root,
            subjects=None,          # fetch a small default set
            session_id="REST1_LR", # single run per subject
            verbose=0,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to fetch HCP data: {e}") from e

    func_files = hcp_bundle["func"]
    confounds = hcp_bundle["confounds"]
    phenotypic = hcp_bundle["phenotypic"]

    # ------------------------------------------------------------------
    # Keep only the first ``target_subjects`` entries.
    # ------------------------------------------------------------------
    selected_indices = list(range(min(target_subjects, len(func_files))))

    # ------------------------------------------------------------------
    # Write per‑subject data and collect metadata for downstream steps.
    # ------------------------------------------------------------------
    subjects_written: List[str] = []
    phenotypic_rows: List[Dict[str, Any]] = []
    behavioral_rows: List[Dict[str, Any]] = []

    # Identify the DCCS (Dimensional Change Card Sort) column – it may vary
    # across releases, so we look for any column containing “dccs” (case‑insensitive).
    dccs_col = None
    for col in phenotypic.columns:
        if "dccs" in col.lower():
            dccs_col = col
            break
    if dccs_col is None:
        raise ValueError("Behavioral column for NIH Toolbox DCCS not found in phenotypic data.")

    for idx in selected_indices:
        subj_id = str(phenotypic.iloc[idx]["Subject"])
        subjects_written.append(subj_id)

        # ---- copy the NIfTI file -------------------------------------------------
        subj_dir = raw_root / subj_id
        subj_dir.mkdir(parents=True, exist_ok=True)
        src_nifti = func_files[idx]
        dest_nifti = subj_dir / f"{subj_id}_REST.nii.gz"
        shutil.copy2(src_nifti, dest_nifti)

        # ---- write confounds (as TSV) -------------------------------------------
        conf_df = confounds[idx]
        confounds_path = subj_dir / "confounds.tsv"
        conf_df.to_csv(confounds_path, sep="\\t", index=False)

        # ---- collect phenotypic information --------------------------------------
        phen_row = {
            "Subject_ID": subj_id,
            "Age": int(phenotypic.iloc[idx]["Age"]),
            "Sex": phenotypic.iloc[idx]["Gender"],  # assumed values like 'M'/'F'
        }
        phenotypic_rows.append(phen_row)

        # ---- collect behavioral DCCS score ---------------------------------------
        flex_score = phenotypic.iloc[idx][dccs_col]
        if pd.isna(flex_score):
            # Keep NaN – downstream merge will filter it out.
            flex_score_val = None
        else:
            flex_score_val = float(flex_score)

        behavioral_rows.append({
            "Subject_ID": subj_id,
            "Flexibility_Score": flex_score_val,
        })

    # ------------------------------------------------------------------
    # Write phenotypic CSV (used later by preprocessing)
    # ------------------------------------------------------------------
    phenotypic_path = raw_root / "phenotypic.csv"
    pd.DataFrame(phenotypic_rows).to_csv(phenotypic_path, index=False)

    # ------------------------------------------------------------------
    # Write behavioral CSV (used later by merging)
    # ------------------------------------------------------------------
    behavioral_path = raw_root / "behavioral_scores.csv"
    pd.DataFrame(behavioral_rows).to_csv(behavioral_path, index=False)

    # ------------------------------------------------------------------
    # Write a minimal manifest for downstream stages that need a total count.
    # ------------------------------------------------------------------
    manifest = {
        "total_count": len(subjects_written),
        "subjects": subjects_written,
    }
    manifest_path = raw_root / "manifest.json"
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=2)

    # ------------------------------------------------------------------
    # After the dataset is materialised, generate SHA‑256 checksums.
    # ------------------------------------------------------------------
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
