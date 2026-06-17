"""
Basic sanity test for the precision validation module.

The test checks that the module can be imported and that the ``main`` function
runs without raising an exception when the required data files are present.
It does **not** assert on the content of the generated report or plot – those
are verified in higher‑level integration tests.
"""
import os
from pathlib import Path

import pytest

# Import the module under test
from analysis.precision import main as precision_main

@pytest.mark.usefixtures("ensure_cleaned_data")
def test_precision_main_runs_successfully(tmp_path: Path):
    """
    Run the ``precision.main`` entry‑point and verify that the expected
    artefacts are created.
    """
    # Ensure a clean environment
    for p in ["docs/reproducibility/precision_report.md", "data/plots/crossing_vs_braid.png"]:
        if Path(p).exists():
            os.remove(p)

    # Execute the main function
    precision_main()

    # Verify artefacts
    assert Path("docs/reproducibility/precision_report.md").is_file()
    assert Path("data/plots/crossing_vs_braid.png").is_file()

# Fixture that ensures the cleaned dataset exists.
@pytest.fixture
def ensure_cleaned_data():
    """
    Load the cleaned data using the project's data loader. If the file does not
    exist, invoke the upstream pipeline steps that produce it.
    """
    from analysis.data_quantities import load_cleaned_knots_data

    df = load_cleaned_knots_data()
    if df.empty:
        # Trigger the full download‑parse‑save pipeline.
        from data.data_saver import main as data_saver_main
        data_saver_main()
        df = load_cleaned_knots_data()
    assert not df.empty, "Cleaned knot dataset should be non‑empty after pipeline run."