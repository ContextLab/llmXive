import os
import pathlib
import numpy as np

def test_shap_interaction_files_exist():
    """
    Verify that the SHAP interaction matrix and heatmap are created.
    This test assumes that the explainability script has been run
    beforehand (e.g., via the quickstart or CI pipeline).
    """
    interaction_path = pathlib.Path('data/derived/shap_interaction.npy')
    heatmap_path = pathlib.Path('data/derived/shap_interactions.png')

    assert interaction_path.is_file(), f"Missing SHAP interaction matrix: {interaction_path}"
    assert heatmap_path.is_file(), f"Missing SHAP interaction heatmap: {heatmap_path}"

    # Load the matrix and perform a minimal sanity check
    arr = np.load(interaction_path)
    # The interaction matrix should have at least 2 dimensions
    assert arr.ndim >= 2, f"SHAP interaction array has unexpected shape: {arr.shape}"