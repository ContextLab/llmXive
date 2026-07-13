"""
Spatial smoothing of fMRI data.

Applies a Gaussian kernel to normalize spatial noise and improve signal-to-noise ratio
before statistical analysis.
"""
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union

import nibabel as nib
from nilearn import image

# Local imports using the project's established API surface
from utils.io import ensure_dir, file_exists, load_json
from utils.config import get_config
from utils.logger import get_logger


logger = get_logger(__name__)


def smooth_volume(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    fwhm: float = 6.0,
    mask_img: Optional[Union[str, Path, nib.Nifti1Image]] = None
) -> nib.Nifti1Image:
    """
    Apply spatial smoothing to a single NIfTI volume using nilearn.

    Args:
        input_path: Path to the input NIfTI file (normalized space).
        output_path: Path where the smoothed NIfTI file will be saved.
        fwhm: Full Width at Half Maximum for the Gaussian kernel (in mm).
            Standard values are 4-8mm for fMRI.
        mask_img: Optional mask image to restrict smoothing to brain voxels.

    Returns:
        The smoothed NIfTI image object.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not file_exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Smoothing {input_path.name} with FWHM={fwhm}mm")

    # Load input image
    input_img = image.load_img(input_path)

    # Apply smoothing
    # nilearn.image.smooth_img handles the Gaussian convolution
    smoothed_img = image.smooth_img(input_img, fwhm=fwhm, mask_img=mask_img)

    # Ensure output directory exists
    ensure_dir(output_path)

    # Save result
    smoothed_img.to_filename(str(output_path))
    logger.info(f"Saved smoothed image to {output_path}")

    return smoothed_img


def smooth_participant_data(
    participant_id: str,
    data_dir: Union[str, Path],
    config: Optional[Dict] = None
) -> Path:
    """
    Process smoothing for a single participant.

    Expects normalized data to be in:
        {data_dir}/preprocessed/{participant_id}/func/
        looking for *_space-MNI_desc-preproc_bold.nii.gz

    Outputs to:
        {data_dir}/preprocessed/{participant_id}/func/
        *_space-MNI_desc-preproc_desc-smooth_bold.nii.gz

    Args:
        participant_id: Unique participant identifier.
        data_dir: Root directory of the project data.
        config: Configuration dictionary (optional, overrides default).

    Returns:
        Path to the generated smoothed file.
    """
    data_dir = Path(data_dir)
    
    # Default configuration
    default_config = {
        "smoothing_fwhm": 6.0
    }
    
    if config:
        default_config.update(config)
        
    fwhm = default_config.get("smoothing_fwhm", 6.0)

    # Define paths
    input_dir = data_dir / "processed" / participant_id / "func"
    output_dir = input_dir  # Save in same directory with new suffix

    if not input_dir.exists():
        raise FileNotFoundError(f"Preprocessed functional directory not found: {input_dir}")

    # Find the preprocessed file (standard naming convention based on T015 output)
    # Assuming T015 produced: *_space-MNI_desc-preproc_bold.nii.gz
    input_files = list(input_dir.glob("*_space-MNI_desc-preproc_bold.nii.gz"))
    
    if not input_files:
        raise FileNotFoundError(
            f"No preprocessed bold files found in {input_dir}. "
            f"Expected pattern: *_space-MNI_desc-preproc_bold.nii.gz"
        )

    if len(input_files) > 1:
        logger.warning(f"Multiple preprocessed files found in {input_dir}. Using the first one: {input_files[0].name}")

    input_file = input_files[0]
    stem = input_file.stem
    # Remove 'bold' from stem if present to append 'smooth_bold'
    if stem.endswith('_bold'):
        stem = stem[:-5]
    
    output_filename = f"{stem}_desc-smooth_bold.nii.gz"
    output_file = output_dir / output_filename

    logger.info(f"Processing participant {participant_id}: {input_file.name} -> {output_filename}")

    # Perform smoothing
    smooth_volume(
        input_path=input_file,
        output_path=output_file,
        fwhm=fwhm
    )

    return output_file


def main():
    """
    CLI entry point for spatial smoothing.
    Reads config from environment or defaults, processes all available participants.
    """
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    
    # Load participant list if available, otherwise scan directory
    # Assuming participants are in data/processed/
    processed_dir = data_dir / "processed"
    
    if not processed_dir.exists():
        logger.error(f"Processed data directory not found: {processed_dir}")
        return

    participants = [p.name for p in processed_dir.iterdir() if p.is_dir()]
    
    if not participants:
        logger.warning("No participants found in processed directory.")
        return

    logger.info(f"Found {len(participants)} participants to smooth.")

    smoothing_config = {
        "smoothing_fwhm": config.get("smoothing_fwhm", 6.0)
    }

    successful = 0
    failed = 0

    for pid in participants:
        try:
            output_path = smooth_participant_data(
                participant_id=pid,
                data_dir=data_dir,
                config=smoothing_config
            )
            logger.info(f"Successfully smoothed {pid}: {output_path}")
            successful += 1
        except Exception as e:
            logger.error(f"Failed to smooth {pid}: {str(e)}")
            failed += 1

    logger.info(f"Smoothing complete. Successful: {successful}, Failed: {failed}")


if __name__ == "__main__":
    main()