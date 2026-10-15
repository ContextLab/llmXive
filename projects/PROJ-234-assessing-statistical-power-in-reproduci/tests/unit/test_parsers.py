"""
Unit tests for ``code.utils.parsers``.
"""

import pytest

from code.utils.parsers import (
    DataFetchError,
    extract_effect_size,
    extract_sample_size,
)

# ----------------------------------------------------------------------
def test_extract_sample_size_success():
    txt = "In this study we recruited N = 256 participants."
    assert extract_sample_size(txt) == 256

# ----------------------------------------------------------------------
def test_extract_sample_size_failure():
    with pytest.raises(DataFetchError):
        extract_sample_size("No sample size mentioned here.")

# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "text,expected",
    [
        ("Cohen's d = 0.45", (0.45, "Cohen's d", None)),
        ('Cohen’s d= -0.78', (-0.78, "Cohen's d", None)),
        ("F(2, 145) = 4.5", (4.5, "F", (2, 145))),
        ("F ( 3 , 200 ) = 2.1", (2.1, "F", (3, 200))),
    ],
)
def test_extract_effect_size_success(text, expected):
    assert extract_effect_size(text) == expected

# ----------------------------------------------------------------------
def test_extract_effect_size_no_match():
    with pytest.raises(DataFetchError):
        extract_effect_size("The p‑value was significant.")