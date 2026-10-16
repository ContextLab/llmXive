"""
Unit tests for ``src.ingest.image_detection``.
"""

import pandas as pd
import pytest

from src.ingest.image_detection import detect_image_psd, is_image_path

@pytest.mark.parametrize(
    "value,expected",
    [
        ("psd_plot.png", True),
        ("folder/subdir/image.JPG", True),
        ("http://example.com/psd.tiff", True),
        ("https://example.org/plots/curve.svg", True),
        ("not_an_image.txt", False),
        ("just_a_string", False),
        ("", False),
        (None, False),
        (123, False),
        (pd.NA, False),
    ],
)
def test_is_image_path(value, expected):
    """Verify that ``is_image_path`` correctly recognises image references."""
    assert is_image_path(value) is expected


def test_detect_image_psd_basic():
    """Create a small DataFrame and ensure the detector flags the right rows."""
    df = pd.DataFrame(
        {
            "experiment_id": ["exp0", "exp1", "exp2", "exp3"],
            "d10": [10.0, "psd_1.png", 12.5, 9.0],
            "d50": [50.0, 55.0, "http://example.com/psd2.jpg", 48.0],
            "d90": [90.0, 95.0, 92.0, "image.tiff"],
        }
    )

    mask = detect_image_psd(df)

    # Expected: rows 1, 2, and 3 contain at least one image reference.
    expected = pd.Series([False, True, True, True], index=df.index)
    pd.testing.assert_series_equal(mask, expected, check_dtype=False)