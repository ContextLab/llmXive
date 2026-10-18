import pathlib
import numpy as np
import pandas as pd
import pytest
from nilearn import image

# Import the script as a module to reuse its main function
from code.data.run_preprocess import main as run_preprocess

def test_preprocess_creates_output(tmp_path, monkeypatch):
    """
    End‑to‑end test that the preprocessing script creates a
    NIfTI file that can be loaded with Nilearn and has the expected
    dimensions (MNI template shape with the original number of time points).
    """
    # Redirect the project data directories to a temporary location
    # so the test does not interfere with any real data on disk.
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed" / "fmri_clean"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Patch the llmxive_toolkit paths helpers to use the temporary root.
    # The helpers create folders under the project root; we replace the
    # root attribute temporarily.
    import llmxive_toolkit
    original_root = llmxive_toolkit.paths.root
    llmxive_toolkit.paths.root = tmp_path

    # Ensure that the path helpers now resolve under the temporary root.
    # No additional monkeypatching of the helpers themselves is required
    # because they compute paths relative to ``paths.root`` each call.

    # Run the preprocessing script – it will download the demo dataset
    # (a real small fMRI image) and process it.
    run_preprocess()

    # After execution, there should be exactly one output file.
    output_files = list(processed_dir.glob("*.nii.gz"))
    assert len(output_files) == 1, "Expected a single preprocessed NIfTI file"

    # Load the output with Nilearn and perform basic sanity checks.
    preproc_img = image.load_img(str(output_files[0]))
    data = preproc_img.get_fdata()
    assert data.ndim == 4, "Preprocessed image should be 4‑D (time + 3‑D space)"

    # The spatial dimensions should match the MNI152 template (91, 109, 91)
    # while preserving the original number of time points.
    assert data.shape[:3] == (91, 109, 91), "Spatial dimensions do not match MNI template"
    assert data.shape[3] > 0, "Time dimension should be non‑zero"

    # Clean up: restore the original root path.
    llmxive_toolkit.paths.root = original_root