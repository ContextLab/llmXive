"""Create an auditory cortex ROI mask using the Harvard-Oxford Cortical Structural Atlas.

This script downloads the Harvard-Oxford cortical atlas (maximum-probability,
threshold 0, 1mm MNI space) via Nilearn, extracts the left and right
Heschl's Gyrus regions (commonly used as a proxy for primary auditory cortex),
combines them into a binary mask, and writes the result to
``roi_masks/auditory_cortex.nii.gz`` in the project root.

The script can be executed directly:

    python code/create_auditory_roi.py

After execution the file ``roi_masks/auditory_cortex.nii.gz`` will exist
and be ready for downstream analyses.
"""

import os
from pathlib import Path

import numpy as np
import nibabel as nib
from nilearn import datasets


def fetch_harvard_oxford_atlas():
    """Fetch the Harvard‑Oxford cortical structural atlas (max‑probability, 1 mm).

    Returns
    -------
    atlas_img : nibabel.Nifti1Image
        The atlas image where each voxel value corresponds to a region index.
    labels : list of str
        List of region labels (index 0 is background).
    """
    # Deterministic fetch: max‑probability atlas, no threshold, 1 mm resolution
    atlas = datasets.fetch_atlas_harvard_oxford(
        "cort-maxprob-thr0-1mm",  # max‑probability, threshold 0, 1 mm MNI space
        data_dir=None,  # use default cache location
        verbose=0,
    )
    atlas_img = nib.load(atlas["maps"])
    labels = atlas["labels"]
    return atlas_img, labels


def create_auditory_cortex_mask(atlas_img: nib.Nifti1Image, labels):
    """Create a binary mask for left and right Heschl's Gyrus (auditory cortex).

    Parameters
    ----------
    atlas_img : nibabel.Nifti1Image
        Atlas image with integer region labels.
    labels : list of str
        Corresponding region names.

    Returns
    -------
    mask_img : nibabel.Nifti1Image
        Binary mask (dtype uint8) where voxels belonging to the auditory cortex
        are 1, all other voxels are 0.
    """
    data = atlas_img.get_fdata()
    # Identify region indices whose label contains "Heschl"
    auditory_indices = [
        idx for idx, name in enumerate(labels) if "Heschl" in name
    ]

    if not auditory_indices:
        raise RuntimeError(
            "Auditory cortex regions not found in Harvard‑Oxford atlas labels."
        )

    # Create binary mask
    mask_data = np.isin(data, auditory_indices).astype(np.uint8)

    # Preserve affine and header (but update datatype)
    mask_img = nib.Nifti1Image(mask_data, affine=atlas_img.affine, header=atlas_img.header)
    # Ensure datatype is uint8
    mask_img.set_data_dtype(np.uint8)
    return mask_img


def main(output_path: Path = Path("roi_masks") / "auditory_cortex.nii.gz"):
    """Generate the auditory cortex ROI mask and write it to disk."""
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Fetch atlas and create mask
    atlas_img, labels = fetch_harvard_oxford_atlas()
    mask_img = create_auditory_cortex_mask(atlas_img, labels)

    # Save mask
    nib.save(mask_img, str(output_path))
    print(f"Auditory cortex ROI mask saved to: {output_path}")


if __name__ == "__main__":
    main()