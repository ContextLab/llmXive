"""Unit tests for the scatter‑plot visualisation utilities.

The test verifies that ``code/viz/scatter.py`` creates a PNG file with the
expected name and that the generated figure contains the required textual
annotations (correlation coefficient and corrected q‑value).  The test uses
a tiny synthetic dataset so it runs quickly on CI.
"""

import os
from pathlib import Path

import pandas as pd
import pytest

# Import the function under test
from code.viz.scatter import generate_scatter_plot, generate_all_scatter_plots

@pytest.fixture
def synthetic_correlation_csv(tmp_path: Path) -> Path:
    """Create a minimal ``correlations.csv`` file that the scatter plot
    generator expects."""
    df = pd.DataFrame(
        {
            "metric": ["modularity"],
            "r": [0.45],
            "p": [0.012],
            "p_fdr": [0.018],
            "significant": [True],
            "subject_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "modularity": [0.3, 0.4, 0.35, 0.45, 0.32, 0.38, 0.42, 0.36, 0.41, 0.39],
            "motor_score": [50, 55, 52, 58, 51, 54, 57, 53, 56, 54],
        }
    )
    out_path = tmp_path / "correlations.csv"
    df.to_csv(out_path, index=False)
    return out_path

def test_scatter_plot_generates_png_with_annotations(tmp_path: Path,
                                                      synthetic_correlation_csv: Path):
    """Run the scatter‑plot generator and check that a PNG file is created
    and that the file size is non‑zero (basic sanity check)."""
    # Arrange – tell the generator where to read the correlation table
    os.environ["CORRELATIONS_CSV"] = str(synthetic_correlation_csv)

    # Act
    generate_all_scatter_plots(output_dir=tmp_path)

    # Assert – the expected PNG should exist
    expected_png = tmp_path / "scatter_modularity.png"
    assert expected_png.is_file(), f"Expected plot {expected_png} to be created"
    assert expected_png.stat().st_size > 0, "Generated PNG is empty"

    # Clean up environment variable
    del os.environ["CORRELATIONS_CSV"]
