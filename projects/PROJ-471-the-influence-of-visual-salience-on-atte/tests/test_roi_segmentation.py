"""
Tests for the ROI‑segmentation script (T004).

Two scenarios are covered:
1. No pre‑existing masks → the script should run the detectors,
   generate ``*_face.png`` and ``*_weapon.png`` masks for each stimulus
   image, and create the expected metadata files.
2. Pre‑existing masks are present → the script should copy them to the
   interim directory without invoking the detectors.
"""
import json
import os
import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest

# Import the module under test
from code.eye_tracking import segment_roi

# Helper to create a simple synthetic image (256×256 with a white square)
def _create_dummy_image(path: Path):
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    cv2.rectangle(img, (60, 60), (196, 196), (255, 255, 255), -1)
    cv2.imwrite(str(path), img)

@pytest.fixture
def dataset_structure(tmp_path: Path):
    """
    Build a minimal dataset layout under the project ``data/`` folder:

    data/
        raw/
            ds003123/
                stimuli/
                    sample.png
    """
    # Resolve absolute project ``data`` directory via llmxive toolkit
    from llmxive_toolkit import paths

    raw_stimuli = paths.data("raw", "ds003123", "stimuli")
    raw_stimuli.mkdir(parents=True, exist_ok=True)

    # Create a dummy stimulus image
    stimulus_path = raw_stimuli / "sample.png"
    _create_dummy_image(stimulus_path)

    # Ensure masks and interim directories are clean
    raw_masks = paths.data("raw", "ds003123", "masks")
    if raw_masks.exists():
        shutil.rmtree(raw_masks)
    interim_masks = paths.interim("masks")
    if interim_masks.exists():
        shutil.rmtree(interim_masks)

    # Return the paths we will need in the test
    return {
        "raw_stimuli": raw_stimuli,
        "raw_masks": raw_masks,
        "interim_masks": interim_masks,
    }

def test_masks_generated_when_absent(dataset_structure):
    """
    Verify that masks are generated for a stimulus image when no
    pre‑existing masks are present.
    """
    # Run the segmentation script
    exit_code = segment_roi.main()
    assert exit_code == 0, "segment_roi.main() should exit cleanly"

    interim_masks = dataset_structure["interim_masks"]
    # Expected mask filenames
    face_mask = interim_masks / "sample_face.png"
    weapon_mask = interim_masks / "sample_weapon.png"

    # Masks must exist
    assert face_mask.is_file(), "Face mask was not created"
    assert weapon_mask.is_file(), "Weapon mask was not created"

    # Masks must have the same dimensions as the source image
    src_img = cv2.imread(str(dataset_structure["raw_stimuli"] / "sample.png"))
    src_h, src_w = src_img.shape[:2]

    for mask_path in (face_mask, weapon_mask):
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        assert mask is not None, f"Unable to read generated mask {mask_path.name}"
        assert mask.shape == (src_h, src_w), "Mask dimensions do not match source image"

    # Detection metadata JSON should be created and contain entries for both ROI types
    detection_meta_path = Path("data") / "interim" / "detection_metadata.json"
    assert detection_meta_path.is_file(), "Detection metadata JSON missing"
    with open(detection_meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert isinstance(meta, list) and len(meta) >= 2, "Metadata should contain at least two entries"
    roi_types = {entry["roi_type"] for entry in meta}
    assert {"face", "weapon"} <= roi_types, "Metadata missing face or weapon entries"

    # Flagged CSV should exist (may be empty if detections succeeded)
    flagged_csv = Path("data") / "interim" / "flagged_images.csv"
    assert flagged_csv.is_file(), "Flagged images CSV missing"

def test_preexisting_masks_are_copied(tmp_path: Path):
    """
    When masks already exist under ``data/raw/ds003123/masks/``,
    the script should copy them to ``data/interim/masks/`` and
    produce a provenance file. No new masks should be generated.
    """
    from llmxive_toolkit import paths

    # Create raw masks directory and dummy mask files
    raw_masks_dir = paths.data("raw", "ds003123", "masks")
    raw_masks_dir.mkdir(parents=True, exist_ok=True)
    dummy_face = raw_masks_dir / "sample_face.png"
    dummy_weapon = raw_masks_dir / "sample_weapon.png"
    # Write simple binary masks (all zeros)
    cv2.imwrite(str(dummy_face), np.zeros((256, 256), dtype=np.uint8))
    cv2.imwrite(str(dummy_weapon), np.zeros((256, 256), dtype=np.uint8))

    # Ensure interim masks dir is empty
    interim_masks_dir = paths.interim("masks")
    if interim_masks_dir.exists():
        shutil.rmtree(interim_masks_dir)

    # Run the segmentation script
    exit_code = segment_roi.main()
    assert exit_code == 0, "segment_roi.main() should succeed when copying masks"

    # Verify that the masks were copied
    copied_face = interim_masks_dir / "sample_face.png"
    copied_weapon = interim_masks_dir / "sample_weapon.png"
    assert copied_face.is_file(), "Face mask was not copied to interim"
    assert copied_weapon.is_file(), "Weapon mask was not copied to interim"

    # Verify that the copied files are identical (size check)
    assert os.path.getsize(copied_face) == os.path.getsize(dummy_face)
    assert os.path.getsize(copied_weapon) == os.path.getsize(dummy_weapon)

    # Verify provenance JSON
    provenance_path = Path("data") / "interim" / "mask_provenance.json"
    assert provenance_path.is_file(), "Mask provenance JSON missing"
    with open(provenance_path, "r", encoding="utf-8") as f:
        provenance = json.load(f)
    assert isinstance(provenance, list) and len(provenance) == 2
    src_paths = {Path(entry["source"]).name for entry in provenance}
    assert src_paths == {"sample_face.png", "sample_weapon.png"}

    # No detection metadata or flagged CSV should be produced because the
    # script short‑circuits after copying.
    assert not (Path("data") / "interim" / "detection_metadata.json").exists()
    assert not (Path("data") / "interim" / "flagged_images.csv").exists()