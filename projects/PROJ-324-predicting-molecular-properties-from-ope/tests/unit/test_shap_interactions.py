import os
import pathlib
import numpy as np
import pandas as pd

from code.analysis.explainability import plot_shap_interactions

def test_shap_interaction_artifacts(tmp_path, monkeypatch):
    """
    Run the SHAP interaction pipeline and verify that the expected
    artifacts are created with plausible shapes.
    """
    # Ensure the script uses the project-relative paths; no monkeypatch needed
    # Execute the function (it will write to the actual data/derived directory)
    plot_shap_interactions()

    # Verify the .npy file exists and has a 3‑D shape
    npy_path = pathlib.Path('data/derived/shap_interaction.npy')
    assert npy_path.is_file(), "SHAP interaction .npy file was not created"

    arr = np.load(npy_path)
    assert isinstance(arr, np.ndarray), ".npy file did not contain a NumPy array"
    assert arr.ndim == 3, "SHAP interaction tensor should be 3‑dimensional (n_samples, n_bits, n_bits)"

    # Verify the heatmap PNG exists and is non‑empty
    png_path = pathlib.Path('data/derived/shap_interactions.png')
    assert png_path.is_file(), "SHAP interaction heatmap PNG was not created"
    assert png_path.stat().st_size > 0, "SHAP interaction heatmap PNG is empty"