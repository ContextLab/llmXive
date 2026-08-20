import os
import json
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from utils.logging_config import get_logger, error, info, warning
from config import get_config

logger = get_logger(__name__)


def load_mask_from_json(mask_json_path: Path) -> np.ndarray:
    """
    Load ROI mask from a JSON file containing mask coordinates or path.
    Expected format: {"mask_path": "/path/to/mask.nii.gz"} or {"coords": [...]}
    """
    if not mask_json_path.exists():
        raise FileNotFoundError(f"Mask JSON file not found: {mask_json_path}")

    with open(mask_json_path, 'r') as f:
        mask_data = json.load(f)

    if "mask_path" in mask_data:
        mask_nib_path = Path(mask_data["mask_path"])
        if not mask_nib_path.exists():
            raise FileNotFoundError(f"Referenced mask file not found: {mask_nib_path}")
        mask_img = nib.load(mask_nib_path)
        mask_array = mask_img.get_fdata()
    elif "coords" in mask_data:
        # Generate mask from coordinates if provided
        coords = np.array(mask_data["coords"])
        shape = mask_data.get("shape", (64, 64, 32))
        mask_array = np.zeros(shape, dtype=np.float32)
        for coord in coords:
            if all(0 <= c < s for c, s in zip(coord, shape)):
                mask_array[tuple(coord)] = 1.0
    else:
        raise ValueError("Mask JSON must contain 'mask_path' or 'coords'")

    return mask_array


def extract_roi_timecourse(
    functional_img: nib.Nifti1Image,
    mask_array: np.ndarray,
    subject_id: str
) -> Tuple[np.ndarray, int]:
    """
    Extract mean BOLD timecourse from a functional run using a binary mask.
    Returns (timecourse_array, num_voxels_used).
    """
    func_data = functional_img.get_fdata()
    # Ensure mask is boolean or 0/1
    mask_bool = mask_array > 0.5

    if not np.any(mask_bool):
        raise ValueError("Mask is empty; no voxels selected.")

    # Reshape to 4D if necessary (x, y, z, t)
    if func_data.ndim == 3:
        # Single volume, not a time series
        raise ValueError("Functional image is 3D; expected 4D time series.")
    elif func_data.ndim == 4:
        x, y, z, t = func_data.shape
    else:
        raise ValueError(f"Unexpected functional image dimensions: {func_data.ndim}")

    # Apply mask across all timepoints
    masked_data = func_data[mask_bool, :]  # Shape: (num_voxels, timepoints)

    if masked_data.shape[0] == 0:
        raise ValueError("No voxels selected by mask in functional image.")

    # Mean signal across voxels for each timepoint
    mean_timecourse = masked_data.mean(axis=0)

    return mean_timecourse, masked_data.shape[0]


def find_functional_runs(subject_dir: Path) -> List[Path]:
    """
    Find all functional NIfTI runs for a subject in the raw data directory.
    Looks for files matching pattern: sub-<id>_task-*_bold.nii.gz
    """
    patterns = [
        "sub-*_task-*_bold.nii.gz",
        "sub-*_task-*_bold.nii",
        "func/*.nii.gz",
        "func/*.nii"
    ]

    runs = []
    for pattern in patterns:
        runs.extend(subject_dir.glob(pattern))

    if not runs:
        # Fallback: look for any .nii.gz in the subject dir
        runs = list(subject_dir.glob("*.nii.gz")) + list(subject_dir.glob("*.nii"))

    return sorted([r for r in runs if r.is_file()])


def process_subject(
    subject_id: str,
    raw_data_dir: Path,
    mask_json_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Process a single subject: load mask, extract timecourses from all functional runs,
    concatenate, and save as .npy.
    """
    subject_dir = raw_data_dir / subject_id
    if not subject_dir.exists():
        raise FileNotFoundError(f"Subject directory not found: {subject_dir}")

    mask_array = load_mask_from_json(mask_json_path)
    info(f"Loaded mask for {subject_id}: {mask_array.sum()} voxels")

    func_runs = find_functional_runs(subject_dir)
    if not func_runs:
        raise FileNotFoundError(f"No functional runs found for subject {subject_id}")

    all_timecourses = []
    for run_path in func_runs:
        try:
            func_img = nib.load(run_path)
            tc, num_voxels = extract_roi_timecourse(func_img, mask_array, subject_id)
            all_timecourses.append(tc)
            info(f"  Run {run_path.name}: {len(tc)} timepoints, {num_voxels} voxels")
        except Exception as e:
            warning(f"Skipping run {run_path} due to error: {e}")
            continue

    if not all_timecourses:
        raise ValueError(f"No valid timecourses extracted for subject {subject_id}")

    # Concatenate timecourses across runs
    combined_timecourse = np.concatenate(all_timecourses, axis=0)

    if combined_timecourse.size == 0:
        raise ValueError(f"Combined timecourse is empty for subject {subject_id}")

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, combined_timecourse)

    info(f"Saved timecourse for {subject_id} to {output_path}: shape={combined_timecourse.shape}")

    return {
        "subject_id": subject_id,
        "output_path": str(output_path),
        "num_timepoints": len(combined_timecourse),
        "num_runs": len(all_timecourses)
    }


def main():
    """
    Main entry point for DLPFC timecourse extraction.
    Expects mask_paths.json to exist (from T013) and raw data in data/raw/.
    """
    config = get_config()
    raw_data_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    mask_paths_file = processed_dir / "mask_paths.json"
    output_file = processed_dir / "roi_dlpfc.npy"

    logger.info("Starting DLPFC timecourse extraction (T016)")

    # Check mask paths
    if not mask_paths_file.exists():
        error("E001: Mask paths file not found. Run T013 first.")
        raise FileNotFoundError("E001: Mask paths file not found. Run T013 first.")

    with open(mask_paths_file, 'r') as f:
        mask_paths = json.load(f)

    if "dlpfc" not in mask_paths:
        error("E001: DLPFC mask path not found in mask_paths.json")
        raise KeyError("E001: DLPFC mask path not found in mask_paths.json")

    dlpfc_mask_path = Path(mask_paths["dlpfc"])
    if not dlpfc_mask_path.exists():
        error("E001: DLPFC mask file not found at specified path")
        raise FileNotFoundError("E001: DLPFC mask file not found at specified path")

    # Find subjects in raw data
    subjects = [d.name for d in raw_data_dir.iterdir() if d.is_dir()]
    if not subjects:
        error("E001: No subject directories found in data/raw/")
        raise FileNotFoundError("E001: No subject directories found in data/raw/")

    all_subject_results = []
    for subject_id in subjects:
        try:
            result = process_subject(
                subject_id=subject_id,
                raw_data_dir=raw_data_dir,
                mask_json_path=dlpfc_mask_path,
                output_path=output_file
            )
            all_subject_results.append(result)
        except Exception as e:
            error(f"Failed to process subject {subject_id}: {e}")
            raise

    if not all_subject_results:
        error("E002: No valid timecourses extracted for any subject")
        raise ValueError("E002: No valid timecourses extracted for any subject")

    # Verify output file exists and is not empty
    if not output_file.exists():
        error("E002: Output file was not created")
        raise FileNotFoundError("E002: Output file was not created")

    loaded = np.load(output_file)
    if loaded.size == 0:
        error("E002: Output timecourse array is empty")
        raise ValueError("E002: Output timecourse array is empty")

    info(f"T016 completed successfully. Output: {output_file}, shape: {loaded.shape}")
    return output_file


if __name__ == "__main__":
    main()
