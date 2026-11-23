"""
Generate a mock NIfTI file for unit testing purposes.

This script creates a 4D NIfTI file with moderate spatial resolution,
float32 data type, and valid header information (pixdim and sform).
The generated file is intended for unit testing only and should not
be used in production analysis unless explicitly invoked in test mode.

Output: data/mock/subject_001/func/task-rest_bold.nii.gz
"""

import os
import nibabel as nib
import numpy as np
from pathlib import Path

# Configuration
OUTPUT_DIR = Path("data/mock/subject_001/func")
OUTPUT_FILE = OUTPUT_DIR / "task-rest_bold.nii.gz"

# Dimensions: Moderate spatial resolution (e.g., 64x64x36) with 50 timepoints
# This is a standard EPI resolution for 3T fMRI
DIMENSIONS = (64, 64, 36, 50)

# Voxel dimensions (mm) - typical for 3T fMRI
# 3.75mm isotropic in-plane, 3.75mm slice thickness
PIXDIM = (3.75, 3.75, 3.75, 1.0)  # x, y, z, time

# Number of volumes (TRs)
N_TIMEPOINTS = 50

def generate_mock_nifti():
    """
    Generate a mock 4D NIfTI file with valid header information.
    
    Returns:
        nib.Nifti1Image: The generated NIfTI image object.
    """
    # Create 4D array of zeros with float32 dtype
    # Using zeros instead of random data to ensure reproducibility and avoid fabrication
    data = np.zeros(DIMENSIONS, dtype=np.float32)
    
    # Create NIfTI1 image
    img = nib.Nifti1Image(data, affine=np.eye(4))
    
    # Set header properties
    header = img.header
    header.set_data_dtype(np.float32)
    
    # Set pixdim (voxel dimensions)
    # pixdim[1:4] are spatial dimensions, pixdim[4] is time
    header.set_zooms(PIXDIM[:4])
    
    # Set sform (affine transformation matrix)
    # This maps voxel coordinates to world coordinates
    sform = np.eye(4)
    # Add a small offset to simulate realistic scanner position
    sform[0, 3] = -96.0  # x-offset
    sform[1, 3] = -96.0  # y-offset
    sform[2, 3] = -45.0  # z-offset
    img.set_sform(sform)
    img.set_qform(sform)
    
    return img

def main():
    """Main entry point for generating the mock NIfTI file."""
    print(f"Generating mock NIfTI file at: {OUTPUT_FILE}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate the mock NIfTI image
    img = generate_mock_nifti()
    
    # Save to disk
    nib.save(img, str(OUTPUT_FILE))
    
    # Verify the file was created and has correct properties
    loaded_img = nib.load(str(OUTPUT_FILE))
    loaded_data = loaded_img.get_fdata()
    loaded_header = loaded_img.header
    
    print(f"  - File created successfully: {OUTPUT_FILE}")
    print(f"  - Data shape: {loaded_data.shape}")
    print(f"  - Data dtype: {loaded_data.dtype}")
    print(f"  - Voxel dimensions (pixdim): {loaded_header.get_zooms()}")
    print(f"  - Sform matrix:\n{loaded_img.affine}")
    
    # Validate properties
    assert loaded_data.shape == DIMENSIONS, f"Shape mismatch: {loaded_data.shape} vs {DIMENSIONS}"
    assert loaded_data.dtype == np.float32, f"Dtype mismatch: {loaded_data.dtype} vs float32"
    assert loaded_header.get_zooms()[:3] == PIXDIM[:3], "Pixdim mismatch"
    
    print("  - All validations passed.")
    print("Mock NIfTI file generation complete.")

if __name__ == "__main__":
    main()
