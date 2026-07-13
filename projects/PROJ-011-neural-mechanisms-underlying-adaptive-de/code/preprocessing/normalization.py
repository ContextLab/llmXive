"""
Spatial normalization of fMRI data to MNI standard space.

This module handles the registration of individual subject fMRI data
to the MNI152 standard template using nilearn.
"""
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union

import nibabel as nib
from nilearn import image, registration
from nilearn.datasets import fetch_icbm152_2009

# Import from project utilities
from utils.io import IOLoadError, ensure_dir, file_exists, load_json
from utils.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def normalize_to_mni(
    functional_image_path: Union[str, Path],
    output_path: Union[str, Path],
    template: Optional[str] = "mni152",
    resampling_target: str = "target",
    interpolation: str = "continuous",
) -> Path:
    """
    Normalize a functional fMRI image to MNI standard space.

    Args:
        functional_image_path: Path to the input NIfTI file (motion corrected).
        output_path: Path where the normalized NIfTI file will be saved.
        template: Template identifier. Currently supports 'mni152'.
        resampling_target: Where to resample. 'target' means resample source to target grid.
        interpolation: Interpolation method for resampling ('continuous', 'nearest', etc.).

    Returns:
        Path to the created normalized image file.

    Raises:
        IOLoadError: If the input file does not exist or cannot be loaded.
        FileNotFoundError: If the template cannot be fetched.
    """
    func_path = Path(functional_image_path)
    out_path = Path(output_path)

    if not file_exists(func_path):
        raise IOLoadError(f"Input functional image not found: {func_path}")

    ensure_dir(out_path.parent)

    logger.info(f"Normalizing {func_path.name} to MNI space...")

    # Fetch MNI152 template
    try:
        logger.info("Fetching MNI152 template...")
        if template == "mni152":
            # Fetch standard MNI152 template
            icbm = fetch_icbm152_2009()
            # Use the T1 template, or the mean if available
            target_img = icbm['t1']
        else:
            raise ValueError(f"Unsupported template: {template}")
    except Exception as e:
        logger.error(f"Failed to fetch MNI template: {e}")
        raise FileNotFoundError(f"Could not fetch MNI template: {e}")

    # Load functional image
    try:
        func_img = image.load_img(func_path)
    except Exception as e:
        raise IOLoadError(f"Failed to load functional image: {e}")

    logger.info(f"Input shape: {func_img.shape}, Target shape: {target_img.shape}")

    # Perform registration and resampling
    # nilearn.image.resample_img is robust for this task
    # We resample the source (func_img) to match the target (template) geometry
    normalized_img = image.resample_img(
        func_img,
        target_affine=target_img.affine,
        target_shape=target_img.shape,
        interpolation=interpolation,
        copy=False,
        order=1,  # Trilinear interpolation
    )

    # Save the normalized image
    try:
      nib.save(normalized_img, str(out_path))
      logger.info(f"Normalized image saved to {out_path}")
    except Exception as e:
        logger.error(f"Failed to save normalized image: {e}")
        raise IOError(f"Failed to save normalized image: {e}")

    return out_path


def normalize_participant(
    participant_id: str,
    data_root: Union[str, Path],
    processed_root: Union[str, Path],
    session_id: str = "01",
) -> Dict[str, Union[str, Path]]:
    """
    Wrapper to normalize all functional runs for a specific participant.

    Args:
        participant_id: Participant identifier (e.g., 'sub-01').
        data_root: Root directory of the raw/processed data.
        processed_root: Root directory for processed outputs.
        session_id: Session identifier.

    Returns:
        Dictionary mapping run names to normalized file paths.
    """
    data_root = Path(data_root)
    processed_root = Path(processed_root)

    # Expected input path based on convention:
    # data/processed/{participant_id}/sub-{pid}_ses-{sid}_task-social_bold_preproc.nii.gz
    # Assuming motion correction output is in data/processed
    input_dir = data_root / "processed" / participant_id
    output_dir = processed_root / "normalized" / participant_id

    ensure_dir(output_dir)

    # Find all preprocessed bold images in the participant's processed folder
    # Pattern: *bold*preproc*.nii.gz
    input_files = list(input_dir.glob("*bold*preproc*.nii.gz"))

    if not input_files:
        logger.warning(f"No preprocessed bold images found for {participant_id} in {input_dir}")
        return {}

    results = {}
    for in_file in input_files:
        # Construct output filename: ..._norm.nii.gz
        stem = in_file.stem.replace("_preproc", "_norm")
        out_file = output_dir / f"{stem}.nii.gz"

        # Skip if already exists (idempotent)
        if out_file.exists():
            logger.info(f"Skipping {in_file.name} (already normalized)")
            results[in_file.stem] = out_file
            continue

        try:
            normalize_to_mni(in_file, out_file)
            results[in_file.stem] = out_file
        except Exception as e:
            logger.error(f"Normalization failed for {in_file}: {e}")
            # In a pipeline, we might want to raise or mark as failed
            raise

    return results


def main():
    """
    Entry point for running normalization via command line or script.
    Expects config to be set up via utils.config or environment variables.
    """
    config = get_config()
    logger.info("Starting normalization pipeline...")

    # Retrieve paths from config
    data_root = Path(config.get("data_root", "data"))
    processed_root = Path(config.get("processed_root", "data/processed"))

    # If specific participants are listed, process them; otherwise scan all
    participants = config.get("participants", None)

    if participants:
        pids = [p.strip() for p in participants.split(",")]
    else:
        # Scan processed directory for sub-* folders
        processed_dir = Path(processed_root)
        if not processed_dir.exists():
            logger.error(f"Processed directory not found: {processed_dir}")
            return

        pids = [d.name for d in processed_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]

    logger.info(f"Processing participants: {pids}")

    for pid in pids:
        try:
            results = normalize_participant(
                participant_id=pid,
                data_root=data_root,
                processed_root=processed_root,
            )
            logger.info(f"Normalization complete for {pid}: {len(results)} files")
        except Exception as e:
            logger.error(f"Failed to normalize participant {pid}: {e}")
            # Continue to next participant or exit depending on strictness
            if config.get("fail_fast", False):
                raise

    logger.info("Normalization pipeline finished.")


if __name__ == "__main__":
    main()
