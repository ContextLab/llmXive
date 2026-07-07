"""
Unit tests for synthetic genomic data generation consistency (seed 42).
This test suite verifies that the synthetic genomic data generation logic
in `code/data/generate.py` produces deterministic, reproducible results
when `random_state=42` is used, as required by the project specification.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.generate import generate_synthetic_genomic_features
from config import get_config


@pytest.fixture
def config():
    """Load project configuration."""
    return get_config()


@pytest.fixture
def standard_species_list():
    """Standard list of species for testing."""
    # Using a subset of species to ensure consistency with real data logic
    return [
        "Arabidopsis_thaliana",
        "Oryza_sativa",
        "Zea_mays",
        "Sorghum_bicolor",
        "Triticum_aestivum"
    ]


@pytest.fixture
def standard_gene_list():
    """
    Standard list of 20 genes as defined in T012.
    Logic: label = 1 if sum(genomic_markers) >= 12, else 0.
    """
    return [
        "NCED3", "ABF3", "P5CS", "DREB2A", "ERF1",
        "ABI5", "RD29A", "COR15A", "LEA3", "HSP70",
        "SOD", "APX1", "CAT1", "GPX1", "MDHAR",
        "DHAR", "GSTU", "ZAT12", "WRKY33", "MYB96"
    ]


def test_generate_synthetic_genomic_features_shape(config, standard_species_list, standard_gene_list):
    """
    Test that the generated DataFrame has the correct shape and columns.
    Expected columns: species_id, 20 gene columns, label.
    """
    df = generate_synthetic_genomic_features(
        standard_species_list,
        standard_gene_list,
        random_state=42
    )

    expected_shape = (len(standard_species_list), len(standard_gene_list) + 2)
    assert df.shape == expected_shape, f"Expected shape {expected_shape}, got {df.shape}"

    expected_columns = ['species_id'] + standard_gene_list + ['label']
    assert list(df.columns) == expected_columns, f"Columns mismatch: {list(df.columns)} vs {expected_columns}"


def test_generate_synthetic_genomic_features_reproducibility(standard_species_list, standard_gene_list):
    """
    Test that the generation is reproducible with the same random state (42).
    Running the function twice with seed 42 must yield identical DataFrames.
    """
    df1 = generate_synthetic_genomic_features(standard_species_list, standard_gene_list, random_state=42)
    df2 = generate_synthetic_genomic_features(standard_species_list, standard_gene_list, random_state=42)

    pd.testing.assert_frame_equal(df1, df2)


def test_generate_synthetic_genomic_features_label_logic(standard_species_list, standard_gene_list):
    """
    Test that the label logic is correctly applied:
    label = 1 if sum(genomic_markers) >= 12, else 0.
    """
    df = generate_synthetic_genomic_features(standard_species_list, standard_gene_list, random_state=42)

    # Verify label is binary
    assert df['label'].isin([0, 1]).all(), "Label column must contain only 0 or 1"

    # Verify logic for each row
    for _, row in df.iterrows():
        gene_values = row[standard_gene_list]
        gene_sum = gene_values.sum()
        expected_label = 1 if gene_sum >= 12 else 0
        assert row['label'] == expected_label, (
            f"Label mismatch for species {row['species_id']}: "
            f"sum={gene_sum}, expected_label={expected_label}, actual_label={row['label']}"
        )


def test_generate_synthetic_genomic_features_random_state_effect(standard_species_list, standard_gene_list):
    """
    Test that changing the random_state produces different data.
    """
    df_seed_42 = generate_synthetic_genomic_features(standard_species_list, standard_gene_list, random_state=42)
    df_seed_123 = generate_synthetic_genomic_features(standard_species_list, standard_gene_list, random_state=123)

    # The DataFrames should NOT be equal if random states differ
    try:
        pd.testing.assert_frame_equal(df_seed_42, df_seed_123)
        # If this passes, the seeds didn't change the output (unexpected for random data)
        # However, for binary labels, it's possible labels are same but gene values differ.
        # We check if the underlying gene values differ.
        gene_cols = standard_gene_list
        if df_seed_42[gene_cols].equals(df_seed_123[gene_cols]):
            pytest.fail("Different random states produced identical gene data.")
    except AssertionError:
        # Expected: DataFrames are different
        pass


def test_generate_synthetic_genomic_features_empty_species():
    """Test that an empty species list raises a ValueError."""
    with pytest.raises(ValueError):
        generate_synthetic_genomic_features([], ["Gene1"], random_state=42)


def test_generate_synthetic_genomic_features_empty_genes():
    """Test that an empty gene list raises a ValueError."""
    with pytest.raises(ValueError):
        generate_synthetic_genomic_features(["Species1"], [], random_state=42)