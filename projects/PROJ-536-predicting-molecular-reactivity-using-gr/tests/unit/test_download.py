import os
import sys
import pytest
import pandas as pd
from llmxive_toolkit import paths

# Ensure the module can be imported
from src.data.download import download_uspto_subset, validate_schema

def test_download_and_schema(tmp_path):
    """
    Integration test for the download function.
    It downloads a tiny public CSV and checks that the required columns exist.
    """
    output_file = tmp_path / "uspto_sample.csv"
    # Use the known 'ufukhaman' source which points to a minimal real dataset
    df = download_uspto_subset(
        output_path=str(output_file),
        source_name="ufukhaman"
    )
    # Basic sanity checks
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    # Verify required schema columns are present
    for col in ['reactants_smiles', 'product_smiles', 'yield', 'reaction_class']:
        assert col in df.columns

    # The validation function should return True without raising
    assert validate_schema(df) is True