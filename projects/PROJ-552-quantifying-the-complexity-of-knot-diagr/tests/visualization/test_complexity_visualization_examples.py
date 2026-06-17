"""Test that the complexity visualisation script runs and produces the expected PNG file."""

import os
from pathlib import Path

import pytest

# Import the function directly to avoid executing the whole pipeline
from analysis.complexity_visualization_examples import (
    generate_complexity_visualization_examples,
)


@pytest.fixture
def dummy_cleaned_data(tmp_path: Path) -> Path:
    """Create a tiny cleaned CSV with the minimal required columns."""
    csv_path = tmp_path / "knots_cleaned.csv"
    csv_path.write_text(
        "crossing_number,braid_index\\n"
        "3,2\\n"
        "4,3\\n"
        "5,2\\n"
    )
    return csv_path


def test_generate_complexity_visualization_examples(tmp_path: Path, dummy_cleaned_data: Path):
    output_png = tmp_path / "complexity_visualization_examples.png"
    # Run the generator
    generate_complexity_visualization_examples(dummy_cleaned_data, output_png)

    # Verify the file was created and is a non‑empty PNG
    assert output_png.is_file()
    assert output_png.stat().st_size > 0
    # Basic sanity: PNG header bytes
    with open(output_png, "rb") as f:
        header = f.read(8)
    assert header.startswith(b"\x89PNG\r\n\x1a\n")