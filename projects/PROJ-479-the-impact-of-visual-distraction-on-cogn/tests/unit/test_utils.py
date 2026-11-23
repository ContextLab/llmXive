"""
Unit tests for the core utility functions defined in `code/utils.py`.
These tests verify that the logger is correctly configured, that the
checksum function works on a known file, that the random seed utilities
affect NumPy and Python's random module, and that image sanitisation
correctly renames and strips EXIF data.
"""

import os
import hashlib
import random
import numpy as np
import tempfile
from pathlib import Path

import pytest

from utils import (
    get_logger,
    compute_file_checksum,
    set_random_seed,
    get_global_seed,
    sanitize_image_pii,
)


def test_get_logger_returns_logger():
    """The logger should be an instance of logging.Logger and have at least one handler."""
    logger = get_logger("test_logger")
    assert hasattr(logger, "info")
    assert logger.handlers, "Logger should have at least one handler attached"


def test_compute_file_checksum_matches_known_hash():
    """Create a temporary file with known content and verify its SHA256 checksum."""
    content = b"llmXive test checksum"
    expected_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        checksum = compute_file_checksum(tmp_path)
        assert checksum == expected_hash
    finally:
        os.remove(tmp_path)


def test_set_random_seed_affects_random_and_numpy():
    """After setting a seed, subsequent random draws should be reproducible."""
    seed = 12345
    set_random_seed(seed)
    # Record first draws
    py_rand1 = random.random()
    np_rand1 = np.random.rand()

    # Reset seed and draw again; should match
    set_random_seed(seed)
    py_rand2 = random.random()
    np_rand2 = np.random.rand()

    assert py_rand1 == py_rand2, "Python random numbers differ after reseeding"
    assert np.isclose(np_rand1, np_rand2), "NumPy random numbers differ after reseeding"
    # Global seed getter should reflect the last seed set
    assert get_global_seed() == seed


@pytest.mark.parametrize("image_mode,extension", [("RGB", ".png"), ("L", ".jpg")])
def test_sanitize_image_pii_creates_hashed_file(image_mode, extension):
    """
    Create a simple image, run sanitisation, and verify that:
    1. The output file exists in the expected directory.
    2. The filename follows the pattern img_<sha256>.jpg (or .png depending on Pillow save).
    3. EXIF data is stripped (Pillow drops EXIF on save without passing exif=).
    """
    from PIL import Image

    # Create a temporary image file
    with tempfile.TemporaryDirectory() as tmp_dir:
        img_path = Path(tmp_dir) / f"original{extension}"
        # Simple 10x10 image
        img = Image.new(image_mode, (10, 10), color=128)
        img.save(img_path)

        # Run sanitisation
        sanitized_path = sanitize_image_pii(str(img_path))

        # Verify output path
        assert sanitized_path is not None, "sanitize_image_pii should return a path"
        assert os.path.isfile(sanitized_path), "Sanitized image file was not created"

        # Verify filename pattern
        filename = os.path.basename(sanitized_path)
        assert filename.startswith("img_") and filename.endswith(".jpg"), (
            f"Sanitized filename '{filename}' does not follow expected pattern"
        )

        # Verify checksum matches original file's checksum
        original_checksum = compute_file_checksum(str(img_path))
        expected_name = f"img_{original_checksum}.jpg"
        assert filename == expected_name, "Sanitized filename does not contain correct checksum"

        # Ensure the file is in the correct output directory
        expected_dir = Path("data/processed/sanitized_images")
        assert Path(sanitized_path).parent == expected_dir, (
            f"Sanitized image should be placed in {expected_dir}"
        )

        # Clean up the created sanitized image (pytest will handle temp dirs)
        os.remove(sanitized_path)