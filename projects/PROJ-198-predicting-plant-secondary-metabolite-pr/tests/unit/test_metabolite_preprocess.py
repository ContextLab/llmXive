"""
Unit tests for the metabolite preprocessing script (T008).
"""

import pathlib

import pandas as pd
import pytest

from code.data.metabolite_preprocess import (
    _load_and_validate,
    harmonize_metabolites,
)

@pytest.fixture
def tmp_metabolite_files(tmp_path):
    """
    Create two minimal metabolite TSV files with the required columns.
    """
    species_data = [
        ("sp1", 10, "AAAABBBBCCCCDDDD-EEEEEEEEEE-F"),
        ("sp2", 0, "1111222233334444-5555555555-G"),
    ]

    file_paths = []
    for i, (species, abundance, inchikey) in enumerate(species_data, start=1):
        df = pd.DataFrame(
            {
                "species": [species],
                "abundance": [abundance],
                "InChIKey": [inchikey],
            }
        )
        file = tmp_path / f"species_{i}" / "metabolites.tsv"
        file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(file, sep="\t", index=False)
        file_paths.append(file)

    return file_paths

def test_load_and_validate_success(tmp_metabolite_files):
    df = _load_and_validate(tmp_metabolite_files[0])
    assert set(df.columns) == {"species", "abundance", "inchikey"}
    assert df["species"].iloc[0] == "sp1"
    assert df["abundance"].iloc[0] == 10

def test_load_and_validate_missing_column(tmp_path):
    # Create a file missing the InChIKey column
    df = pd.DataFrame(
        {"species": ["spX"], "abundance": [5]}
    )
    file = tmp_path / "bad" / "metabolites.tsv"
    file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file, sep="\t", index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        _load_and_validate(file)

def test_harmonize_metabolites(tmp_metabolite_files, tmp_path):
    output = tmp_path / "metabolite_harmonized.csv"
    result = harmonize_metabolites(tmp_metabolite_files, output)

    # Verify output file exists
    assert output.exists()

    # Verify expected columns and numeric range
    expected_cols = {"inchikey", "abundance_log"}
    assert set(result.columns) == expected_cols

    # Check that log values are computed correctly
    # For abundance 10 -> log(11) ≈ 2.3979, for 0 -> log(1) = 0
    log_vals = result.sort_values("inchikey")["abundance_log"].tolist()
    assert pytest.approx(log_vals[0], rel=1e-4) == 0.0
    assert pytest.approx(log_vals[1], rel=1e-4) == pytest.approx(2.397895, rel=1e-4)