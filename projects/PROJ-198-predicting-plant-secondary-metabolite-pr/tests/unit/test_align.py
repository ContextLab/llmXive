"""
Unit tests for the alignment utilities.
"""

import pandas as pd
import pytest

from code.data.align import align_data, calculate_alignment_success_rate

@pytest.fixture
def genomes_df():
    """Genome DataFrame with some zero‑BGC rows."""
    return pd.DataFrame({
        "species": ["sp1", "sp2", "sp3"],
        "total_bgc_count": [0, 5, 0],
        "bgc_type_a": [0, 2, 0],
        "bgc_type_b": [0, 3, 0],
    })

@pytest.fixture
def metabolites_df():
    """Metabolite DataFrame with matching and non‑matching species."""
    return pd.DataFrame({
        "species": ["sp1", "sp2", "sp4"],
        "log_abundance": [1.2, 0.8, 0.5],
    })

def test_align_data_retains_zero_bgc_rows(genomes_df, metabolites_df):
    aligned, _ = align_data(genomes_df, metabolites_df)
    # Rows for sp1 and sp2 should be present; sp3 has no metabolite data and is dropped
    assert set(aligned["species"]) == {"sp1", "sp2"}
    # Verify that zero‑BGC rows are kept (sp1 has total_bgc_count == 0)
    sp1_row = aligned[aligned["species"] == "sp1"].iloc[0]
    assert sp1_row["total_bgc_count"] == 0

def test_alignment_success_rate_counts_valid_species(genomes_df, metabolites_df):
    aligned, rate = align_data(genomes_df, metabolites_df)
    # Only sp1 and sp2 are aligned; both have non‑null required columns
    expected_rate = 2 / 3  # 2 valid species out of 3 total species in aligned_df
    assert pytest.approx(rate, 0.01) == expected_rate

def test_calculate_alignment_success_rate_direct():
    df = pd.DataFrame({
        "species": ["a", "b", "c"],
        "total_bgc_count": [0, 1, 2],
        "log_abundance": [0.5, 0.7, 0.9],
    })
    rate = calculate_alignment_success_rate(df)
    assert rate == 1.0  # all rows have required data