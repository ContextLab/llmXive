"""Unit test for the complexity visualisation example generator.

The test simply ensures that the generator runs without error and writes
the expected PNG file.
"""
import os
from pathlib import Path

import pytest

from analysis.complexity_visualization_examples import (
    generate_complexity_visualization_examples,
)

@pytest.mark.parametrize(
    "output_path",
    [
        Path("data/plots/complexity_visualization_examples.png"),
    ],
)
def test_generate_complexity_visualization_examples(output_path: Path):
    # Ensure a clean state
    if output_path.is_file():
        output_path.unlink()
    # Run the generator
    result_path = generate_complexity_visualization_examples(output_path=output_path)
    # Verify the file was created
    assert result_path.is_file()
    # Basic sanity check on file size (non‑empty image)
    assert result_path.stat().st_size > 0
    # Cleanup after test
    os.remove(result_path)