import pathlib
import nibabel as nib
from llmxive_toolkit import paths

def test_demo_preprocessed_file_exists_and_loadable():
    """
    Verify that the demo preprocessing script produces a loadable NIfTI file.
    """
    processed_file = paths.data("processed", "fmri_clean", "demo.nii.gz")
    assert processed_file.is_file(), f"Expected preprocessed file at {processed_file}"
    # Attempt to load with nibabel (via nilearn) to ensure file integrity.
    img = nib.load(str(processed_file))
    assert img.shape[0] > 0, "Loaded image has no timepoints"
    # Basic sanity checks on affine and data type.
    assert img.affine.shape == (4, 4), "Affine matrix is malformed"
    assert img.get_fdata().size > 0, "Image data array is empty"