import re
import os
from pathlib import Path

import pytest

# The project structure places tests in code/tests, data in code/data relative to root.
# However, standard Python execution often assumes the repo root is the working directory.
# We resolve the path relative to the test file's location to ensure robustness.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_FILE_PATH = BASE_DIR / "data" / "processed" / "sample_prompts.txt"

def test_no_lat_lon_regex():
    """
    Unit test to verify that the input prompts contain zero geographic coordinates.
    Input: data/processed/sample_prompts.txt
    Assert: zero matches for regex r'lat[=:\s]*[-\d.]+|lon[=:\s]*[-\d.]+'
    """
    if not DATA_FILE_PATH.exists():
        pytest.fail(f"Input file not found: {DATA_FILE_PATH}. "
                    "Ensure data generation tasks have run or create a sample file.")

    pattern = re.compile(r'lat[=:\s]*[-\d.]+|lon[=:\s]*[-\d.]+', re.IGNORECASE)
    
    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    matches = pattern.findall(content)
    
    assert len(matches) == 0, (
        f"Found {len(matches)} potential coordinate leaks in the dataset. "
        f"Matches found: {matches}. "
        "The map-free dataset must not contain latitude/longitude data."
    )