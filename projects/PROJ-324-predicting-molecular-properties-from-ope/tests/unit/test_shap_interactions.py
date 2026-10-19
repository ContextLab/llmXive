"""
Unit test for the SHAP interaction heatmap generation (T102).
The test invokes the plot_shap_interactions function and verifies that:
- The interaction matrix file exists and has the expected 3‑D shape.
- The heatmap PNG file exists and is non‑empty.
"""
import os
from pathlib import Path

import numpy as np
from PIL import Image

# Import the function under test
from code.analysis.explainability import plot_shap_interactions

def test_shap_interaction_artifacts(tmp_path, monkeypatch):
    """
    Run the SHAP interaction pipeline and assert output artifacts.
    """
    # Ensure the project uses the real data directories under the repository root.
    # The function writes directly to the 'data/derived' folder, so we don't need to
    # redirect paths – we just clean up after the test.
    derived_dir = Path('data/derived')
    # Remove any pre‑existing artifacts to guarantee a fresh run.
    for f in ['shap_interaction.npy', 'shap_interactions.png']:
        p = derived_dir / f
        if p.is_file():
            p.unlink()

    # Run the pipeline
    plot_shap_interactions()

    # 1. Check that the .npy interaction matrix exists and has a 3‑D shape.
    interaction_path = derived_dir / 'shap_interaction.npy'
    assert interaction_path.is_file(), "shap_interaction.npy was not created"
    shap_array = np.load(interaction_path)
    assert shap_array.ndim == 3, f"Expected 3‑D SHAP interaction tensor, got shape {shap_array.shape}"

    # 2. Check that the heatmap PNG exists and is non‑empty.
    heatmap_path = derived_dir / 'shap_interactions.png'
    assert heatmap_path.is_file(), "shap_interactions.png was not created"
    # Open with Pillow to ensure it's a valid image.
    with Image.open(heatmap_path) as img:
        img.verify()  # will raise if the file is corrupted
    # Additionally, check that the image has non‑zero dimensions.
    with Image.open(heatmap_path) as img:
        width, height = img.size
        assert width > 0 and height > 0, "Generated heatmap has zero size"

    # Clean up generated files after verification to keep the repo tidy.
    interaction_path.unlink()
    heatmap_path.unlink()
