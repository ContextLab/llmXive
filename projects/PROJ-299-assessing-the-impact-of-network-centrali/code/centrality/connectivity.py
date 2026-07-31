"""
Connectivity matrix construction module (FR-003).

Loads the AAL atlas, extracts mean BOLD time series for cortical and subcortical ROIs,
and computes standard Pearson correlation matrices for each participant.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn import image, masking
from scipy import stats

# Add project root to path for imports if running as script
if "code" not in sys.path:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)


def load_atlas_mask(atlas_path: Path, labels: Optional[List[str]] = None) -> nib.Nifti1Image:
    """
    Load the AAL atlas NIfTI file.

    Args:
        atlas_path: Path to the AAL atlas file.
        labels: Optional list of label names to filter (not implemented here,
                AAL is loaded as-is).

    Returns:
        Loaded NIfTI image object.
    """
    if not atlas_path.exists():
        raise FileNotFoundError(f"AAL Atlas not found at {atlas_path}")

    logger.info(f"Loading AAL atlas from {atlas_path}")
    atlas_img = nib.load(str(atlas_path))
    return atlas_img


def extract_roi_time_series(
    preprocessed_img: nib.Nifti1Image,
    atlas_img: nib.Nifti1Image,
    rois: Optional[List[int]] = None
) -> np.ndarray:
    """
    Extract mean BOLD time series for specified ROIs from the preprocessed image.

    Args:
        preprocessed_img: Preprocessed functional NIfTI image (4D).
        atlas_img: Atlas NIfTI image (3D) containing integer labels for regions.
        rois: Optional list of ROI integer labels. If None, all non-zero labels
              in the atlas are used.

    Returns:
        Array of shape (n_timepoints, n_rois) containing the mean time series
        for each ROI.
    """
    # Ensure images are in the same space (nilearn handles resampling if needed,
    # but here we assume they are already aligned as per T010 output)
    # If they are not aligned, nilearn's masking functions can handle resampling on the fly
    # or we can use resample_to_img. For safety, we rely on nilearn's masking which
    # expects aligned images or handles resampling.

    # Get unique labels from the atlas (excluding 0 which is background)
    atlas_data = atlas_img.get_fdata()
    unique_labels = np.unique(atlas_data)
    unique_labels = unique_labels[unique_labels != 0]

    if rois is not None:
        # Filter for requested ROIs
        valid_rois = [r for r in rois if r in unique_labels]
        if len(valid_rois) < len(rois):
            missing = set(rois) - set(unique_labels)
            logger.warning(f"Requested ROIs {missing} not found in atlas. Using {valid_rois}")
        labels_to_use = valid_rois if valid_rois else list(unique_labels)
    else:
        labels_to_use = list(unique_labels)

    if not labels_to_use:
        raise ValueError("No valid ROIs found to extract time series from.")

    logger.info(f"Extracting time series for {len(labels_to_use)} ROIs")

    # Use nilearn's NiftiLabelsMasker to extract mean time series
    # This handles the masking and averaging automatically
    from nilearn.input_data import NiftiLabelsMasker

    # Create a masker instance
    # We use the atlas image as the reference for labels
    # The preprocessed_img is the data to mask
    masker = NiftiLabelsMasker(
        labels_img=atlas_img,
        standardize=False,  # We standardize later if needed, or let correlation handle it
        detrend=False,      # Preprocessing should have handled detrending
        t_r=None,           # TR is not strictly needed for correlation, but good to have if known
        verbose=0
    )

    try:
        time_series = masker.fit_transform(preprocessed_img)
    except Exception as e:
        logger.error(f"Error extracting time series: {e}")
        raise

    # time_series shape: (n_timepoints, n_rois)
    # The columns correspond to the sorted unique labels in the atlas
    # We need to map the columns back to the specific labels we care about if we filtered
    # However, NiftiLabelsMasker returns columns in the order of sorted unique labels.
    # If we passed specific labels to a custom masker, it would be easier.
    # Let's verify the order. The masker uses the unique labels in the atlas_img.
    # We need to reorder the columns if we only want a subset, or just keep all if rois=None.

    # If 'rois' was specified, the masker might have returned all unique labels in the atlas
    # but we only wanted a subset. We need to filter the columns.
    if rois is not None:
        # Find the index of each requested ROI in the sorted unique labels
        sorted_labels = sorted(labels_to_use) # This is what the masker likely used internally?
        # Actually, NiftiLabelsMasker uses the unique labels found in the image.
        # Let's re-extract the unique labels from the image data to be sure.
        all_labels = sorted(list(np.unique(atlas_data)[1:])) # Exclude 0
        
        # Create a mapping from label to column index
        label_to_idx = {label: idx for idx, label in enumerate(all_labels)}
        
        # Select columns for the requested ROIs
        col_indices = [label_to_idx[r] for r in rois if r in label_to_idx]
        time_series = time_series[:, col_indices]
        logger.info(f"Filtered time series to {len(col_indices)} requested ROIs.")

    return time_series


def compute_correlation_matrix(time_series: np.ndarray) -> np.ndarray:
    """
    Compute the Pearson correlation matrix from the ROI time series.

    Args:
        time_series: Array of shape (n_timepoints, n_rois).

    Returns:
        Correlation matrix of shape (n_rois, n_rois).
    """
    if time_series.shape[0] < 2:
        raise ValueError("Need at least 2 time points to compute correlation.")

    # Use scipy.stats.pearsonr for pairwise correlation
    # np.corrcoef is faster and vectorized
    corr_matrix = np.corrcoef(time_series, rowvar=False)

    # Handle NaNs that might arise from constant time series (though preprocessing should prevent this)
    if np.any(np.isnan(corr_matrix)):
        logger.warning("NaN values detected in correlation matrix. Filling with 0.")
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

    return corr_matrix


def process_participant_connectivity(
    participant_id: str,
    preprocessed_nifti_path: Path,
    atlas_path: Path,
    output_dir: Path,
    rois: Optional[List[int]] = None
) -> Tuple[Path, Dict]:
    """
    Process a single participant to generate connectivity matrix and metadata.

    Args:
        participant_id: Unique identifier for the participant.
        preprocessed_nifti_path: Path to the preprocessed 4D NIfTI file.
        atlas_path: Path to the AAL atlas file.
        output_dir: Directory to save the output matrix and metadata.
        rois: Optional list of ROI indices to include.

    Returns:
        Tuple of (path_to_output_matrix, metadata_dict).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Processing connectivity for participant {participant_id}")

    if not preprocessed_nifti_path.exists():
        raise FileNotFoundError(f"Preprocessed image not found: {preprocessed_nifti_path}")

    # Load images
    func_img = nib.load(str(preprocessed_nifti_path))
    atlas_img = load_atlas_mask(atlas_path)

    # Extract time series
    try:
        ts = extract_roi_time_series(func_img, atlas_img, rois)
    except Exception as e:
        logger.error(f"Failed to extract time series for {participant_id}: {e}")
        raise

    # Compute correlation
    corr_mat = compute_correlation_matrix(ts)

    # Save results
    matrix_filename = f"conn_matrix_{participant_id}.npy"
    matrix_path = output_dir / matrix_filename
    np.save(str(matrix_path), corr_mat)

    # Metadata
    metadata = {
        "participant_id": participant_id,
        "n_rois": corr_mat.shape[0],
        "n_timepoints": ts.shape[0],
        "matrix_file": str(matrix_path),
        "status": "success"
    }

    logger.info(f"Saved connectivity matrix for {participant_id} to {matrix_path}")
    return matrix_path, metadata


def run_connectivity_pipeline(
    participant_ids: List[str],
    data_dir: Path,
    output_dir: Path,
    atlas_path: Optional[Path] = None,
    roi_config_path: Optional[Path] = None
) -> List[Dict]:
    """
    Run the connectivity pipeline for a list of participants.

    Args:
        participant_ids: List of participant IDs to process.
        data_dir: Base directory containing preprocessed data (e.g., data/processed).
        output_dir: Directory to save connectivity results.
        atlas_path: Path to AAL atlas. If None, tries to find a standard path or fails.
        roi_config_path: Path to a JSON config file containing specific ROI lists.

    Returns:
        List of metadata dictionaries for each participant.
    """
    # Default AAL atlas path (common location in nilearn or project data)
    # If not provided, we try a standard path or raise an error
    if atlas_path is None:
        # Try common nilearn atlas location or project specific
        # For this implementation, we assume the user provides the path or it's in data/
        # Let's check if it exists in data/raw or similar
        possible_paths = [
            data_dir.parent / "data" / "raw" / "aal_atlas.nii.gz",
            data_dir.parent / "data" / "raw" / "aal_atlas.nii",
            Path("/usr/share/fsl/data/atlases/AAL.nii"), # Fallback
        ]
        for p in possible_paths:
            if p.exists():
                atlas_path = p
                break
        
        if atlas_path is None:
            # Try to load from nilearn's built-in atlases if available?
            # nilearn.datasets.fetch_atlas_aal() returns a dict with 'maps'
            # But fetching might be slow or require internet.
            # For now, we require the path to be provided or found.
            raise FileNotFoundError(
                "AAL Atlas not found. Please provide --atlas-path or ensure it is in "
                "data/raw/aal_atlas.nii[.gz] or a standard FSL path."
            )

    # Load ROI config if provided
    rois = None
    if roi_config_path and roi_config_path.exists():
        with open(roi_config_path, 'r') as f:
            config = json.load(f)
            # Expecting a list of integers or a dict with specific keys
            if isinstance(config, list):
                rois = config
            elif isinstance(config, dict) and "rois" in config:
                rois = config["rois"]
            else:
                logger.warning("ROI config format not recognized. Using all atlas ROIs.")

    results = []
    for pid in participant_ids:
        # Construct expected path for preprocessed file
        # Assuming naming convention: preprocessed_<pid>.nii.gz
        preprocessed_path = data_dir / f"preprocessed_{pid}.nii.gz"
        if not preprocessed_path.exists():
            # Try without .gz
            preprocessed_path = data_dir / f"preprocessed_{pid}.nii"
        
        if not preprocessed_path.exists():
            logger.error(f"Preprocessed file for {pid} not found at {preprocessed_path}")
            results.append({
                "participant_id": pid,
                "status": "failed",
                "error": "Preprocessed file not found"
            })
            continue

        try:
            _, meta = process_participant_connectivity(
                pid, preprocessed_path, atlas_path, output_dir, rois
            )
            results.append(meta)
        except Exception as e:
            logger.error(f"Error processing {pid}: {e}")
            results.append({
                "participant_id": pid,
                "status": "failed",
                "error": str(e)
            })

    return results


def main():
    """CLI entry point for connectivity pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Compute connectivity matrices from preprocessed fMRI data.")
    parser.add_argument("--participants", nargs="+", required=True, help="List of participant IDs")
    parser.add_argument("--data-dir", type=Path, required=True, help="Directory containing preprocessed NIfTI files")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory to save connectivity matrices")
    parser.add_argument("--atlas-path", type=Path, help="Path to AAL atlas file (optional, auto-detected if missing)")
    parser.add_argument("--roi-config", type=Path, help="Path to ROI configuration JSON file")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    # Setup logging
    from utils.logging_config import setup_logging
    setup_logging(level=args.log_level)

    logger.info("Starting connectivity pipeline")
    
    results = run_connectivity_pipeline(
        participant_ids=args.participants,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        atlas_path=args.atlas_path,
        roi_config_path=args.roi_config
    )

    # Log summary
    success_count = sum(1 for r in results if r.get("status") == "success")
    fail_count = len(results) - success_count
    logger.info(f"Pipeline completed. Success: {success_count}, Failed: {fail_count}")

    # Save summary to JSON
    summary_path = args.output_dir / "connectivity_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Summary saved to {summary_path}")


if __name__ == "__main__":
    main()
