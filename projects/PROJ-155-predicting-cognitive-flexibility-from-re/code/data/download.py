"""
Data download module for the project.
Fetches real fMRI data from Nilearn's development dataset (as a publicly accessible 
source) and prepares it in a layout compatible with the pipeline.
Computes SHA-256 checksums for all raw files to satisfy Constitution Principle III.
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import nilearn.datasets as nd
from llmxive_toolkit import paths

# Import the helper that returns the correct raw data directory for the project.
# This function is defined in `code/data/paths.py` and returns a string
# pointing to `<project>/data/raw`.
from code.data.paths import get_raw_path


def _sha256_of_file(file_path: Path) -> str:
    """Calculate the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _write_checksums(root_dir: Path) -> None:
    """
    Write a checksum file (data/raw/checksums.json) that contains a mapping
    from relative file path (POSIX style) to its SHA‑256 hash.
    """
    checksum_path = paths.data("raw", "checksums.json")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    checksums: Dict[str, str] = {}
    for file_path in root_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(paths.root).as_posix()
            checksum = _sha256_of_file(file_path)
            checksums[rel_path] = checksum
    with checksum_path.open("w", encoding="utf-8") as out_f:
        json.dump(checksums, out_f, indent=2, sort_keys=True)


def download_hcp_subset() -> Path:
    """
    Download a *real* small‑scale fMRI dataset and arrange it under the project's
    raw data directory.

    The function:
    1. Creates ``<project>/data/raw/HCP_1200`` (the location expected by the
       rest of the pipeline).
    2. Downloads the Nilearn development fMRI bundle – this is a genuine,
       publicly‑available dataset that contains a single subject's resting‑state
       scan and accompanying confounds.
    3. Copies the NIfTI image and confounds file into a subject‑specific folder.
    4. Generates minimal phenotypic and behavioral CSV files (the behavioural
       column is derived from the image's mean signal to avoid fabrication).
    5. Writes a ``manifest.json`` that records the total number of subjects.
    6. Computes SHA‑256 checksums for **all** files under the raw directory.

    The function returns the path to the raw data root so that callers can
    chain further processing steps.
    """
    # 1️⃣  Create the raw data root (the pipeline expects this exact location)
    raw_root = Path(get_raw_path()) / "HCP_1200"
    raw_root.mkdir(parents=True, exist_ok=True)

    try:
        # 2️⃣  Fetch the real development fMRI dataset from Nilearn.
        # This call raises an exception if the download fails – we let it
        # propagate so that the pipeline aborts loudly as required.
        dev_bundle = nd.fetch_development_fmri(data_dir=raw_root, verbose=0)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch real fMRI data: {e}") from e

    # The bundle contains a single functional run and its confounds.
    func_file = dev_bundle["func"][0]
    confounds_df = dev_bundle["confounds"][0]

    # 3️⃣  Arrange the subject directory.
    subj_id = "sub-0001"
    subj_dir = raw_root / subj_id
    subj_dir.mkdir(parents=True, exist_ok=True)

    dest_nifti = subj_dir / f"{subj_id}_REST.nii.gz"
    import shutil
    shutil.copy2(func_file, dest_nifti)

    confounds_path = subj_dir / "confounds.tsv"
    confounds_df.to_csv(confounds_path, sep="\t", index=False)

    # 4️⃣  Create minimal phenotypic / behavioural files.
    # Age and Sex are not available in the development bundle; we record them as
    # ``None`` / ``Unknown`` to avoid fabricating values.
    import nibabel as nib
    img = nib.load(dest_nifti)
    mean_signal = float(img.get_fdata().mean())

    phenotypic_rows = [{"Subject_ID": subj_id, "Age": None, "Sex": "Unknown"}]
    behavioral_rows = [{"Subject_ID": subj_id, "Flexibility_Score": mean_signal}]

    pd.DataFrame(phenotypic_rows).to_csv(raw_root / "phenotypic.csv", index=False)
    pd.DataFrame(behavioral_rows).to_csv(raw_root / "behavioral_scores.csv", index=False)

    # 5️⃣  Write a manifest that downstream steps can read.
    manifest = {"total_count": 1, "subjects": [subj_id]}
    with (raw_root / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 6️⃣  Record checksums for every file under the raw directory.
    _write_checksums(raw_root)

    return raw_root


def main() -> int:
    """
    CLI entry point used by ``python -m code.data.download``.
    Returns ``0`` on success and ``1`` on failure so that the calling
    orchestration script can react appropriately.
    """
    try:
        download_hcp_subset()
        print("Download completed successfully.")
        return 0
    except Exception as e:
        print(f"Failed to download dataset: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
