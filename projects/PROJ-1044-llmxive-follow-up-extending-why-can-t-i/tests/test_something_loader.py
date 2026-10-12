"""
Unit test for the Something‑Something V2 streaming loader.

The test verifies that the iterator yields at least five (url, label) pairs
and that each URL appears to be a valid HTTP(S) address.
"""

import pathlib
import re
import sys

import pytest

# Ensure the project root is on the import path
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.data.something_loader import something_stream

URL_REGEX = re.compile(r"^https?://")

@pytest.mark.timeout(300)
def test_something_loader_yields_five():
    """
    Stream the dataset and assert that at least five items are produced,
    and that each video_url looks like a proper HTTP(S) URL.
    """
    iterator = something_stream(seed=42, max_examples=5)
    items = list(iterator)
    assert len(items) >= 5, "Expected at least 5 items from the loader"
    for url, label in items:
        assert isinstance(url, str) and URL_REGEX.match(url), f"Invalid video URL: {url}"
        assert isinstance(label, str) and label, "Label must be a non‑empty string"