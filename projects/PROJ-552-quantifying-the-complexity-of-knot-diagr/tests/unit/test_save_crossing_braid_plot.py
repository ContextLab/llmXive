"""Basic unit test for the crossing‑vs‑braid plot script.

The test verifies that the script creates the expected PNG file without
raising an exception. It uses a tiny synthetic DataFrame to keep the test
fast and deterministic.
"""

import pathlib
from pathlib import Path

import pandas as pd

# Import the function directly to avoid running the full pipeline.
from analysis.save_crossing_braid_plot import (
    create_crossing_vs_braid_plot,
)


def test_create_crossing_vs_braid_plot(tmp_path: Path) -> None:
    # Small synthetic dataset.
    df = pd.DataFrame(
        {
            "crossing_number": [3, 4, 5, 6],
            "braid_index": [2, 2, 3, 3],
            "alternating": [True, False, True, False],
        }
    )

    output_file = tmp_path / "crossing_vs_braid.png"

    # Should run without error.
    create_crossing_vs_braid_plot(df, output_file)

    # Verify that the file was created and is a PNG.
    assert output_file.is_file()
    assert output_file.suffix.lower() == ".png"

    # Simple sanity check on file size (non‑empty PNG).
    assert output_file.stat().st_size > 100  # bytes

# The test can be executed with:
#   pytest -q tests/unit/test_save_crossing_braid_plot.py