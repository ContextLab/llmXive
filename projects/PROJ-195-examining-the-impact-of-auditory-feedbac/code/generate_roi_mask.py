"""
Generate the Auditory Cortex ROI mask from the Harvard-Oxford atlas.

This script fetches the Harvard-Oxford cortical atlas (maxprob, 1mm threshold),
locates the 'Auditory' label, and saves a binary mask to `roi_masks/auditory_cortex.nii.gz`.

Constraints:
  - Uses nilearn.datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr-1mm').
  - If the 'Auditory' label is not found, it raises a RuntimeError.
  - No fallback to 'Superior Temporal Gyrus' or other labels.
"""
import os
import sys
from pathlib import Path
import numpy as np
import nibabel as nib
from nilearn import datasets


def fetch_harvard_oxford_atlas():
    """
    Fetch the Harvard-Oxford Cortical Atlas (maxprob, 1mm threshold).
    Returns the atlas image and the list of label names.
    """
    # Fetch the specific atlas variant
    atlas = datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr-1mm')
    atlas_img = atlas.maps
    label_names = atlas.labels

    return atlas_img, label_names


def create_auditory_cortex_mask(atlas_img, label_names, output_path):
    """
    Extract the 'Auditory' label from the atlas and save it as a binary mask.

    Args:
        atlas_img: Niimg-like object (the atlas image).
        label_names: List of string labels corresponding to atlas indices.
        output_path: Path where the mask will be saved.

    Raises:
        RuntimeError: If the 'Auditory' label is not found in the atlas.
    """
    # Load the atlas data
    atlas_data = atlas_img.get_fdata()

    # Find the index for 'Auditory'
    # Note: The first label in Harvard-Oxford is usually 'Background' or empty string.
    # We iterate to find the exact match.
    auditory_index = None
    for idx, label in enumerate(label_names):
        if label.strip().lower() == 'auditory':
            auditory_index = idx
            break

    if auditory_index is None:
        raise RuntimeError(
            "ERROR: 'Auditory' label not found in Harvard-Oxford atlas. "
            f"Available labels: {label_names}. "
            "The task requires an explicit error if 'Auditory' is absent. "
            "No fallback to 'Superior Temporal Gyrus' is allowed."
        )

    # Create binary mask
    mask_data = (atlas_data == auditory_index).astype(np.int16)

    # Create NiBabel image
    mask_img = nib.Nifti1Image(mask_data, atlas_img.affine, atlas_img.header)

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the mask
    nib.save(mask_img, str(output_path))
    print(f"Successfully saved Auditory Cortex mask to: {output_path}")
    return mask_img


def main():
    """Main entry point for the ROI mask generation."""
    # Define output path relative to project root
    # Assuming this script is run from the project root or code/ directory
    # The task requires output at `roi_masks/auditory_cortex.nii.gz`
    project_root = Path(__file__).parent.parent
    output_path = project_root / "roi_masks" / "auditory_cortex.nii.gz"

    print("Fetching Harvard-Oxford Cortical Atlas...")
    try:
        atlas_img, label_names = fetch_harvard_oxford_atlas()
    except Exception as e:
        print(f"Failed to fetch atlas: {e}", file=sys.stderr)
        sys.exit(1)

    print("Extracting 'Auditory' label...")
    try:
        create_auditory_cortex_mask(atlas_img, label_names, output_path)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()