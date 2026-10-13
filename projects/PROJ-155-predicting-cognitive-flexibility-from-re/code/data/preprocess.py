"""
Preprocessing module for rs-fMRI data.
Parcellates fMRI time‑series using the Schaefer 200‑region atlas and saves
region‑wise time‑series as NumPy ``.npy`` files.
"""
import os
import logging
from typing import List, Optional
import numpy as np
import pandas as pd
import nilearn.datasets as nd
from nilearn.maskers import NiftiLabelsMasker

from code.data.paths import get_raw_path, get_processed_path, ensure_dir
from code.utils.logging import init_logging

logger = logging.getLogger(__name__)


def run_preprocessing_pipeline(subject_ids: Optional[List[str]] = None) -> int:
    """
    Execute the preprocessing pipeline for the given subjects.

    Returns the number of subjects successfully processed.
    """
    init_logging()
    raw_path = Path(get_raw_path())
    processed_path = Path(get_processed_path())

    # Directory that will hold the per‑subject ``.npy`` time‑series.
    timeseries_dir = processed_path / "timeseries"
    ensure_dir(timeseries_dir)

    # Fetch Schaefer 200‑region atlas.
    try:
        atlas = nd.fetch_atlas_schaefer_2018(n_rois=200)
        atlas_img = atlas["maps"]
    except Exception as e:
        logger.error(f"Failed to fetch Schaefer atlas: {e}")
        return 0

    # Determine which subjects to process.
    if subject_ids is None:
        subject_ids = [
            d for d in os.listdir(raw_path)
            if os.path.isdir(os.path.join(raw_path, d))
        ]

    processed_count = 0
    neuro_features: List[dict] = []

    masker = NiftiLabelsMasker(labels_img=atlas_img, standardize=True)

    for sid in subject_ids:
        nifti_path = raw_path / sid / f"{sid}_REST.nii.gz"
        confounds_path = raw_path / sid / "confounds.tsv"

        if not nifti_path.is_file():
            logger.warning(f"NIfTI file missing for subject {sid}; skipping.")
            continue

        try:
            # ---- Parcellation -------------------------------------------------
            time_series = masker.fit_transform(str(nifti_path))
            # Save as .npy
            ts_path = timeseries_dir / f"{sid}_ts.npy"
            np.save(ts_path, time_series)

            # ---- Motion (Mean FD) --------------------------------------------
            conf_df = pd.read_csv(confounds_path, sep="\t")
            fd_col = next(
                (c for c in conf_df.columns if "framewise_displacement" in c.lower() or c.lower() == "fd"),
                None,
            )
            mean_fd = float(conf_df[fd_col].mean()) if fd_col else 0.0

            # ---- Demographics -------------------------------------------------
            phen_df = pd.read_csv(raw_path / "phenotypic.csv")
            phen_row = phen_df[phen_df["Subject_ID"] == sid]
            age = phen_row.iloc[0]["Age"] if not phen_row.empty else None
            sex = phen_row.iloc[0]["Sex"] if not phen_row.empty else "Unknown"

            # ---- Scan duration ------------------------------------------------
            import nibabel as nib

            img = nib.load(str(nifti_path))
            # TR is the 4th element of zooms if present
            zooms = img.header.get_zooms()
            tr = zooms[3] if len(zooms) >= 4 else 0.0
            total_scan_time = float(tr * img.shape[3]) if tr > 0 else 0.0

            neuro_features.append(
                {
                    "Subject_ID": sid,
                    "Mean_FD": mean_fd,
                    "Age": age,
                    "Sex": sex,
                    "Total_Scan_Time": total_scan_time,
                }
            )
            processed_count += 1
        except Exception as e:
            logger.error(f"Error processing subject {sid}: {e}")

    # Save the summary table used later by the merge step.
    neuro_df = pd.DataFrame(neuro_features)
    neuro_df.to_csv(processed_path / "neuro_features.csv", index=False)

    return processed_count


def main():
    count = run_preprocessing_pipeline()
    print(f"Processed {count} subjects.")
    return 0 if count > 0 else 1


if __name__ == "__main__":
    exit(main())
