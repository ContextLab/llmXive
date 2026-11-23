"""
Unit tests for Reduced Detail Manipulation in manipulator.py
"""

import tempfile
from pathlib import Path

from PIL import Image

from stimuli.manipulator import remove_minor_elements, process_single_image


def test_reduce_removes_objects():
    """
    Test that remove_minor_elements applies blur to reduce detail.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a source image with some variation
        src_path = tmpdir / "src.png"
        # Create a gradient image
        img = Image.new("RGB", (100, 100))
        pixels = img.load()
        for x in range(100):
            for y in range(100):
                pixels[x, y] = (x * 2, y * 2, 128)
        img.save(src_path)

        output_path = tmpdir / "reduced.png"

        # Run reduction
        result = remove_minor_elements(src_path, output_path, reduction_factor=0.5)

        # Assertions
        assert result["status"] == "success"
        assert output_path.exists()
        assert result["blur_radius"] > 0
        assert result["reduction_factor"] == 0.5

        # Verify the output is blurrier (lower variance) than input
        # This is a heuristic check
        from stimuli.manipulator import calculate_local_density
        orig_density = calculate_local_density(src_path)
        red_density = calculate_local_density(output_path)

        # Reduced density should be <= original (blur reduces high-frequency detail)
        # Note: due to unsharp mask, it might be slightly different, but generally lower
        assert red_density <= orig_density + 0.05  # Allow small tolerance


def test_process_single_image_reduce_mode():
    """
    Test process_single_image with mode='reduce'.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        src_path = tmpdir / "src.png"
        img = Image.new("RGB", (100, 100), color=(100, 150, 200))
        img.save(src_path)

        output_path = tmpdir / "out.png"

        result = process_single_image(src_path, output_path, mode="reduce",
                                      reduction_factor=0.4)

        assert result["status"] == "success"
        assert output_path.exists()
