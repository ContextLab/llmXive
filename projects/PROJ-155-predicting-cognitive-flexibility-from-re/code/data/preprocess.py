"""
Preprocessing module for rs-fMRI data.
Parsells fMRI time-series using the Schaefer 200-region atlas.
"""
import os
import logging
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
import nilearn.datasets as nd
from nilearn.maskers import NiftiLabelsMasker

from code.data.paths import get_raw_path, get_processed_path, ensure_dir
from code.utils.logging import init_logging

logger = logging.getLogger(__name__)

def run_preprocessing_pipeline(subject_ids: Optional[List[str]] = None) -> int:
    init_logging()
    raw_path = get_raw_path()
    processed_path = get_processed_path()
    parcellated_dir = os.path.join(processed_path, "parcellated")
    ensure_dir(parcellated_dir)

    # Fetch Schaefer 200 atlas
    try:
        atlas = nd.fetch_atlas_schaefer_2018(n_rois=200)
        atlas_filename = atlas.map
    except Exception as e:
        logger.error(f"Failed to fetch atlas: {e}")
        return 0

    if subject_ids is None:
        subject_ids = [d for d in os.listdir(raw_path) if os.path.isdir(os.path.join(raw_path, d))]

    processed_count = 0
    neuro_features = []

    masker = NiftiLabelsMasker(labels_img=atlas_filename, standardize=True)

    for sid in subject_ids:
        nifti_path = os.path.join(raw_path, sid, f"{sid}_REST.nii.gz")
        confounds_path = os.path.join(raw_path, sid, "confounds.tsv")
        if not os.path.exists(nifti_path):
            continue

        try:
            # Parcellation
            time_series = masker.fit_transform(nifti_path)
            
            # Save time series
            df_ts = pd.DataFrame(time_series, columns=[f"ROI_{i+1}" for i in range(time_series.shape[1])])
            df_ts.insert(0, "Subject_ID", sid)
            df_ts.to_csv(os.path.join(parcellated_dir, f"{sid}_timeseries.csv"), index=False)

            # Compute Mean FD
            conf_df = pd.read_csv(confounds_path, sep="\t")
            fd_col = next((c for c in conf_df.columns if "framewise_displacement" in c.lower() or "fd" == c.lower()), None)
            mean_fd = float(conf_df[fd_col].mean()) if fd_col else 0.0

            # Get Age/Sex from phenotypic
            phen_df = pd.read_csv(os.path.join(raw_path, "phenotypic.csv"))
            phen_row = phen_df[phen_df["Subject_ID"] == sid]
            age = phen_row.iloc[0]["Age"] if not phen_row.empty else None
            sex = phen_row.iloc[0]["Sex"] if not phen_row.empty else "Unknown"

            # Total scan time (placeholder since TR is usually 0.72 for HCP, but we'll use NIfTI header if possible)
            import nibabel as nib
            img = nib.load(nifti_path)
            total_scan_time = float(img.header.get_zooms()[3] * img.shape[3]) if len(img.header.get_zooms()) >= 4 else 0.0

            neuro_features.append({
                "Subject_ID": sid, "Mean_FD": mean_fd, "Age": age, "Sex": sex, "Total_Scan_Time": total_scan_time
            })
            processed_count += 1
        except Exception as e:
            logger.error(f"Error processing {sid}: {e}")

    pd.DataFrame(neuro_features).to_csv(os.path.join(processed_path, "neuro_features.csv"), index=False)
    return processed_count

def main():
    count = run_preprocessing_pipeline()
    print(f"Processed {count} subjects.")
    return 0 if count > 0 else 1

if __name__ == "__main__":
    exit(main())
