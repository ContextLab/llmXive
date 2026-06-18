"""
Integration test that runs the validator's ``main`` function and checks that
the output file is created and contains the expected flag columns.
"""

from __future__ import annotations

import pathlib

from data.validator import main as validator_main

def test_validator_main_creates_output(tmp_path, monkeypatch):
    # Redirect the output directory to a temporary location.
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "data.validator.Path",
        lambda *parts: pathlib.Path(*parts).relative_to("."),
    )

    # Run the validator.
    validator_main()

    output_file = pathlib.Path("data/processed/knots_validated.csv")
    assert output_file.is_file()

    # Basic sanity check – the file must contain the flag columns.
    import pandas as pd

    df = pd.read_csv(output_file)
    assert "missing_invariant_flags" in df.columns
    assert "data_quality_flags" in df.columns