"""
Unit tests for the low‑level visual feature computation (T006).

The test creates a temporary raw data directory with a few synthetic
but *real* images, runs the feature generation script, and validates that
the resulting JSON file contains entries for every stimulus and that
each numeric feature falls within the expected ranges.
"""
import json
import numpy as np
import cv2
import pytest
from pathlib import Path

# Import the script's main entry point
from analysis.feature_gen import main as feature_main
from llmxive_toolkit import paths as toolkit_paths

@pytest.fixture
def temporary_dataset(tmp_path: Path):
    """
    Set up a minimal raw dataset with two simple images.
    The fixture patches ``paths.root`` so that all path helpers resolve
    inside the temporary directory.
    """
    # Patch the toolkit root
    toolkit_paths.root = tmp_path

    # Determine where raw images are expected
    from config import get_paths
    paths_obj = get_paths()
    # The raw data directory for stimuli – may be an attribute or a callable.
    if hasattr(paths_obj, "raw_data"):
        raw_dir = Path(paths_obj.raw_data)
    elif callable(getattr(paths_obj, "raw", None)):
        raw_dir = Path(paths_obj.raw())
    else:
        raise RuntimeError("Cannot locate raw data directory via get_paths().")

    raw_dir.mkdir(parents=True, exist_ok=True)

    # Create two simple images (solid colors)
    img1 = np.full((64, 64, 3), 50, dtype=np.uint8)   # dark gray
    img2 = np.full((64, 64, 3), 200, dtype=np.uint8)  # light gray

    img1_path = raw_dir / "dark_gray.png"
    img2_path = raw_dir / "light_gray.png"
    cv2.imwrite(str(img1_path), img1)
    cv2.imwrite(str(img2_path), img2)

    return {
        "raw_dir": raw_dir,
        "image_paths": [img1_path, img2_path],
    }

def test_feature_generation_creates_json_and_validates_entries(temporary_dataset):
    """
    Run the feature generation script and verify the JSON output.
    """
    # Execute the script
    feature_main()

    # Resolve the expected JSON output path
    from config import get_paths
    paths_obj = get_paths()
    if callable(getattr(paths_obj, "interim", None)):
        interim_dir = Path(paths_obj.interim())
    else:
        interim_dir = Path(paths_obj.interim)

    json_path = interim_dir / "low_level_features.json"
    assert json_path.is_file(), "low_level_features.json was not created"

    # Load JSON and perform checks
    data = json.loads(json_path.read_text())

    # There should be exactly two entries (one per image)
    assert len(data) == 2, "JSON should contain two stimulus entries"

    for stimulus_id, feats in data.items():
        # Verify required keys exist
        for key in ("luminance", "contrast", "edge_density", "scene_complexity"):
            assert key in feats, f"Missing key {key} for stimulus {stimulus_id}"

        # Luminance must be in [0, 255]
        lum = feats["luminance"]
        assert 0.0 <= lum <= 255.0, f"Luminance out of range: {lum}"

        # Contrast must be non‑negative
        contrast = feats["contrast"]
        assert contrast >= 0.0, f"Contrast negative: {contrast}"

        # Edge density must be a proportion in [0, 1]
        edge = feats["edge_density"]
        assert 0.0 <= edge <= 1.0, f"Edge density out of range: {edge}"

        # Scene complexity must be a non‑negative integer
        scene = feats["scene_complexity"]
        assert isinstance(scene, int) and scene >= 0, f"Invalid scene complexity: {scene}"