"""
Preprocessing module for rs-fMRI data.
Handles loading of preprocessed NIfTI files and application of Schaefer atlas
parcellation. Updated to write ROI time‑series CSVs into
``data/processed/parcellated/`` and to generate a realistic ``neuro_features.csv``
containing Subject_ID, Mean_FD, Age, Sex, and Total_Scan_Time.
The function now returns the *count* of successfully processed subjects (an ``int``)
so that the orchestration script can correctly interpret success.
"""

import os
import logging
import tarfile
import tempfile
import csv
from typing import List, Optional, Tuple
import numpy as np
import nibabel as nib
import pandas as pd
from scipy import ndimage

from code.config import get_config
from code.data.paths import get_raw_path, get_processed_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging

logger = logging.getLogger(__name__)

# Atlas configuration
ATLAS_URL = "https://schaefer2018.atlases.nitrc.org/Schaefer2018_200Parcels_7Networks_order_FSLMNI152.tar.gz"
ATLAS_FILENAME = "Schaefer2018_200Parcels_7Networks_order_FSLMNI152.nii.gz"
ATLAS_DIR_NAME = "Schaefer2018"


def _get_atlas_local_path() -> str:
    """Returns the local path where the atlas should be stored."""
    raw_path = get_raw_path()
    atlas_dir = os.path.join(raw_path, ATLAS_DIR_NAME)
    ensure_dir(atlas_dir)
    return os.path.join(atlas_dir, ATLAS_FILENAME)


def _download_atlas(atlas_url: str, local_path: str) -> str:
    """Download the Schaefer atlas if it does not already exist."""
    if os.path.exists(local_path):
        logger.info(f"Atlas already exists at {local_path}")
        return local_path

    import requests

    logger.info(f"Downloading atlas from {atlas_url}...")

    temp_dir = tempfile.gettempdir()
    temp_tar = os.path.join(temp_dir, "schaefer_atlas.tar.gz")

    try:
        response = requests.get(atlas_url, stream=True, timeout=300)
        response.raise_for_status()
        with open(temp_tar, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"Downloaded atlas to {temp_tar}, extracting...")

        with tarfile.open(temp_tar, "r:gz") as tar:
            members = tar.getmembers()
            target_member = None
            for member in members:
                if ATLAS_FILENAME in member.name:
                    target_member = member
                    break

            if target_member:
                tar.extract(target_member, path=os.path.dirname(local_path))
                extracted_path = os.path.join(os.path.dirname(local_path), target_member.name)
                if not os.path.exists(local_path) and os.path.exists(extracted_path):
                    os.rename(extracted_path, local_path)
            else:
                raise FileNotFoundError(f"Could not find {ATLAS_FILENAME} in the archive")

        os.remove(temp_tar)
        logger.info("Atlas extraction complete.")
    except requests.RequestException as e:
        log_error(f"Failed to download atlas: {e}")
        raise RuntimeError(f"Data Gap: Real atlas unavailable at {atlas_url}") from e
    except Exception as e:
        log_error(f"Failed to extract atlas: {e}")
        raise

    return local_path


def load_schaefer_parcellation(atlas_url: str = ATLAS_URL) -> nib.Nifti1Image:
    """Load (or download) the Schaefer 200‑parcel atlas."""
    local_path = _get_atlas_local_path()
    _download_atlas(atlas_url, local_path)

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Atlas file not found at {local_path} after download attempt")
    atlas_img = nib.load(local_path)
    logger.info(f"Loaded Schaefer atlas: shape={atlas_img.shape}")
    return atlas_img


def extract_roi_time_series(
    subject_nifti_path: str,
    atlas_img: nib.Nifti1Image,
) -> np.ndarray:
    """Extract mean ROI time‑series from a 4‑D fMRI image."""
    subject_img = nib.load(subject_nifti_path)
    subject_data = subject_img.get_fdata()
    atlas_data = atlas_img.get_fdata()

    unique_labels = np.unique(atlas_data)
    roi_labels = unique_labels[unique_labels > 0]
    roi_labels = np.sort(roi_labels)

    if subject_data.ndim != 4:
        raise ValueError(f"Subject data must be 4D, got {subject_data.ndim}D")

    if atlas_data.shape != subject_data.shape[:3]:
        logger.warning(
            f"Shape mismatch: Subject {subject_data.shape[:3]} vs Atlas {atlas_data.shape}. "
            "Resampling atlas to subject space."
        )
        atlas_data = ndimage.zoom(
            atlas_data,
            np.array(subject_data.shape[:3]) / np.array(atlas_data.shape),
            order=0,
        )
        atlas_data = np.round(atlas_data).astype(int)
        roi_labels = np.unique(atlas_data)[np.unique(atlas_data) > 0]

    n_timepoints = subject_data.shape[3]
    n_rois = len(roi_labels)
    time_series = np.zeros((n_timepoints, n_rois), dtype=np.float32)

    logger.info(f"Extracting time series for {n_rois} ROIs...")

    # Flatten spatial dimensions for efficient indexing
    voxels_total = np.prod(subject_data.shape[:3])
    subject_2d = subject_data.reshape(voxels_total, n_timepoints)

    for i, label in enumerate(roi_labels):
        mask = (atlas_data == label).reshape(-1)
        selected = subject_2d[mask, :]
        if selected.shape[0] > 0:
            time_series[:, i] = np.mean(selected, axis=0)
        else:
            time_series[:, i] = np.nan

    return time_series


def preprocess_subject(
    subject_id: str,
    subject_nifti_path: str,
    atlas_img: Optional[nib.Nifti1Image] = None,
) -> Tuple[str, np.ndarray]:
    """Preprocess a single subject and write ROI time‑series CSV."""
    if atlas_img is None:
        atlas_img = load_schaefer_parcellation()

    if not os.path.exists(subject_nifti_path):
        log_error(f"Subject NIfTI not found: {subject_nifti_path}")
        raise FileNotFoundError(f"Subject data missing: {subject_nifti_path}")

    time_series = extract_roi_time_series(subject_nifti_path, atlas_img)

    # Write CSV under ``data/processed/parcellated/``
    parcellated_dir = os.path.join(get_processed_path(), "parcellated")
    ensure_dir(parcellated_dir)
    output_filename = f"{subject_id}_timeseries.csv"
    output_path = os.path.join(parcellated_dir, output_filename)

    df = pd.DataFrame(time_series)
    df.columns = [f"ROI_{i+1}" for i in range(df.shape[1])]
    df.insert(0, "Timepoint", range(df.shape[0]))
    df.insert(0, "Subject_ID", subject_id)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed time series for {subject_id} to {output_path}")

    return output_path, time_series


def _load_phenotypic_df() -> pd.DataFrame:
    """Load phenotypic CSV generated by the download step."""
    phen_path = os.path.join(get_raw_path(), "phenotypic.csv")
    if not os.path.exists(phen_path):
        raise FileNotFoundError(f"Phenotypic file not found at {phen_path}")
    return pd.read_csv(phen_path, dtype=str)


def _compute_mean_fd(subject_id: str) -> float:
    """Compute the mean framewise displacement for a subject from its confounds."""
    confounds_path = os.path.join(get_raw_path(), subject_id, "confounds.tsv")
    if not os.path.exists(confounds_path):
        raise FileNotFoundError(f"Confounds file missing for subject {subject_id}")

    conf_df = pd.read_csv(confounds_path, sep="\\t")
    # Look for a column containing 'framewise_displacement' (case‑insensitive)
    fd_col = None
    for col in conf_df.columns:
        if "framewise_displacement" in col.lower() or "fd" == col.lower():
            fd_col = col
            break
    if fd_col is None:
        raise ValueError(f"Framewise displacement column not found in confounds for {subject_id}")

    mean_fd = conf_df[fd_col].mean()
    return float(mean_fd)


def _compute_total_scan_time(subject_nifti_path: str) -> float:
    """Compute total scan time (seconds) from NIfTI header."""
    img = nib.load(subject_nifti_path)
    header = img.header
    zooms = header.get_zooms()
    if len(zooms) < 4:
        raise ValueError("NIfTI header does not contain TR information.")
    tr = zooms[3]  # Repetition time in seconds
    n_timepoints = img.shape[3]
    total_seconds = tr * n_timepoints
    return float(total_seconds)


def _write_neuro_features_row(csv_path: str, subject_id: str, mean_fd: float,
                             age: int, sex: str, total_scan_time: float) -> None:
    """
    Append a row to ``neuro_features.csv`` with real subject‑specific values.
    """
    exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["Subject_ID", "Mean_FD", "Age", "Sex", "Total_Scan_Time"])
        writer.writerow([subject_id, f"{mean_fd:.6f}", age, sex, f"{total_scan_time:.2f}"])


def run_preprocessing_pipeline(subject_ids: Optional[List[str]] = None) -> int:
    """
    Run preprocessing for a list of subjects.

    Returns:
        int: Number of subjects successfully processed. 0 indicates failure.
    """
    init_logging()
    logger.info("Starting preprocessing pipeline...")

    phenotypic_df = _load_phenotypic_df()

    if subject_ids is None:
        # Discover subjects from raw directory (subjects are directories)
        raw_path = get_raw_path()
        subject_ids = []
        for entry in os.listdir(raw_path):
            entry_path = os.path.join(raw_path, entry)
            if os.path.isdir(entry_path):
                # Expect a NIfTI file named <id>_REST.nii.gz inside the dir
                nifti_candidate = os.path.join(entry_path, f"{entry}_REST.nii.gz")
                if os.path.isfile(nifti_candidate):
                    subject_ids.append(entry)

    if not subject_ids:
        logger.warning("No subjects found to process.")
        return 0

    atlas_img = load_schaefer_parcellation()
    processed_paths = []
    neuro_features_path = os.path.join(get_processed_path(), "neuro_features.csv")

    for sid in subject_ids:
        nifti_path = os.path.join(get_raw_path(), sid, f"{sid}_REST.nii.gz")
        if not os.path.exists(nifti_path):
            log_warning(f"NIfTI not found for subject {sid}")
            continue
        try:
            out_path, _ = preprocess_subject(sid, nifti_path, atlas_img)
            processed_paths.append(out_path)

            # ---- compute real neuro‑feature values -------------------------
            mean_fd = _compute_mean_fd(sid)
            # Pull age/sex from phenotypic dataframe
            phen_row = phenotypic_df[phenotypic_df["Subject_ID"] == sid]
            if phen_row.empty:
                raise ValueError(f"Phenotypic info missing for subject {sid}")
            age = int(phen_row.iloc[0]["Age"])
            sex = phen_row.iloc[0]["Sex"]
            total_scan_time = _compute_total_scan_time(nifti_path)

            _write_neuro_features_row(
                neuro_features_path,
                subject_id=sid,
                mean_fd=mean_fd,
                age=age,
                sex=sex,
                total_scan_time=total_scan_time,
            )
        except Exception as e:
            log_error(f"Skipping subject {sid} due to error: {e}")
            continue

    logger.info(
        f"Preprocessing pipeline complete. Processed {len(processed_paths)} subjects."
    )
    return len(processed_paths)


def main():
    """CLI entry point for preprocessing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Preprocess HCP fMRI data with Schaefer atlas."
    )
    parser.add_argument("--subject", type=str, help="Specific subject ID to process.")
    parser.add_argument("--verify", action="store_true", help="Verify atlas download and run a test.")
    args = parser.parse_args()

    if args.verify:
        logger.info("Verifying atlas download...")
        try:
            img = load_schaefer_parcellation()
            logger.info(f"Atlas verification successful: {img.shape}")
        except Exception as e:
            logger.error(f"Atlas verification failed: {e}")
            return 1
        return 0

    if args.subject:
        nifti_path = os.path.join(get_raw_path(), f"{args.subject}_REST.nii.gz")
        if not os.path.exists(nifti_path):
            logger.error(f"NIfTI not found for {args.subject}")
            return 1
        try:
            out_path, _ = preprocess_subject(args.subject, nifti_path)
            logger.info(f"Done. Output: {out_path}")
        except Exception as e:
            logger.error(f"Failed: {e}")
            return 1
    else:
        processed_count = run_preprocessing_pipeline()
        if processed_count == 0:
            logger.warning("No subjects processed.")
            return 1

    return 0


if __name__ == "__main__":
    exit(main())
