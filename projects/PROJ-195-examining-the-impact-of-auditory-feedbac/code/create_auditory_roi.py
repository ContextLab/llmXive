"""
Create the Auditory Cortex ROI mask from the Harvard-Oxford Atlas.

This script fetches the Harvard-Oxford Cortical Structural Atlas using nilearn,
locates the 'Auditory Cortex' label, and saves the binary mask to
roi_masks/auditory_cortex.nii.gz.

Dependencies:
    nilearn, nibabel, numpy
"""
import os
from pathlib import Path
import numpy as np
import nibabel as nib
from nilearn import datasets

# Ensure the output directory exists
OUTPUT_DIR = Path("roi_masks")
OUTPUT_FILE = OUTPUT_DIR / "auditory_cortex.nii.gz"

def fetch_harvard_oxford_atlas():
    """
    Fetch the Harvard-Oxford Cortical Atlas (max probability, 1mm resolution).
    Returns the atlas image object and the labels list.
    """
    # fetch_atlas_harvard_oxford returns a dict with 'maps' and 'labels'
    atlas_data = datasets.fetch_atlas_harvard_oxford(
        'cort-maxprob-thr0-1mm', symmetric_split=False
    )
    atlas_img = atlas_data['maps']
    labels = atlas_data['labels']
    return atlas_img, labels

def create_auditory_cortex_mask(atlas_img, labels, target_label="Auditory Cortex"):
    """
    Extract the binary mask for the target label from the atlas.

    Args:
        atlas_img: Nifti1Image object from nilearn.
        labels: List of label strings corresponding to atlas indices.
        target_label: The name of the region to extract.

    Returns:
        Nifti1Image object containing the binary mask.
    """
    # Get the data array
    atlas_data = atlas_img.get_fdata()

    # Find the index of the target label
    # Labels usually start with an empty string for index 0
    label_index = None
    for i, label in enumerate(labels):
        if target_label in label:
            label_index = i
            break

    if label_index is None:
        raise ValueError(f"Label '{target_label}' not found in atlas labels. "
                         f"Available labels: {labels}")

    # Create a binary mask where data == label_index
    mask_data = (atlas_data == label_index).astype(np.int16)

    # Preserve affine and header from the original atlas
    mask_img = nib.Nifti1Image(mask_data, atlas_img.affine, header=atlas_img.header)

    return mask_img

def main():
    """Main entry point to generate the ROI mask."""
    print("Fetching Harvard-Oxford Cortical Atlas...")
    try:
        atlas_img, labels = fetch_harvard_oxford_atlas()
    except Exception as e:
        print(f"ERROR: Failed to fetch atlas: {e}")
        raise

    print("Extracting Auditory Cortex mask...")
    try:
        mask_img = create_auditory_cortex_mask(atlas_img, labels)
    except ValueError as e:
        print(f"ERROR: {e}")
        raise

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Saving mask to {OUTPUT_FILE}...")
    nib.save(mask_img, str(OUTPUT_FILE))

    print(f"Success! ROI mask saved to {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    main()
