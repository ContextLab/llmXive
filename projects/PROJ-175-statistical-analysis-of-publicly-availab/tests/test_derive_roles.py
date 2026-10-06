import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from data.derive_roles import (
    load_marginal_frequencies,
    load_positional_ranks,
    calculate_functional_role,
    verify_exclusion_of_co_occurrence,
    save_output
)

def test_load_marginal_frequencies(tmp_path):
    # Create a mock CSV
    data = {
        "ingredient_id": ["ing1", "ing2", "ing3"],
        "canonical_name": ["Onion", "Salt", "Parsley"],
        "frequency": [100, 200, 10]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "normalized_ingredients.csv"
    df.to_csv(csv_path, index=False)
    
    result = load_marginal_frequencies(csv_path)
    assert "ingredient_id" in result.columns
    assert "frequency" in result.columns
    assert len(result) == 3
    assert result.iloc[0]["ingredient_id"] == "ing1"

def test_load_positional_ranks_missing(tmp_path):
    # Test handling of missing file
    result = load_positional_ranks(tmp_path / "non_existent.csv")
    assert result.empty

def test_calculate_functional_role_frequency_only():
    # Mock marginal frequency data
    data = {
        "ingredient_id": ["ing1", "ing2", "ing3", "ing4", "ing5"],
        "canonical_name": ["A", "B", "C", "D", "E"],
        "frequency": [1000, 800, 500, 300, 50] # Sorted desc for logic
    }
    df = pd.DataFrame(data)
    
    # No positional data
    result = calculate_functional_role(df, pd.DataFrame())
    
    assert "functional_role" in result.columns
    assert len(result) == 5
    # Check that roles are assigned
    assert result["functional_role"].isin(["primary", "secondary", "garnish"]).all()

def test_calculate_functional_role_with_position():
    # Mock data
    freq_data = {
        "ingredient_id": ["ing1", "ing2", "ing3"],
        "canonical_name": ["A", "B", "C"],
        "frequency": [100, 100, 100] # Equal frequency
    }
    freq_df = pd.DataFrame(freq_data)
    
    pos_data = {
        "ingredient_id": ["ing1", "ing2", "ing3"],
        "avg_position": [1.0, 5.0, 10.0] # ing1 is first
    }
    pos_df = pd.DataFrame(pos_data)
    
    result = calculate_functional_role(freq_df, pos_df)
    
    # ing1 should be primary due to position <= 3
    assert result[result["ingredient_id"] == "ing1"]["functional_role"].iloc[0] == "primary"

def test_verify_exclusion_warning(caplog):
    # Create a dummy non-empty dataframe
    co_df = pd.DataFrame({"col": [1, 2, 3]})
    
    # This should log a warning but not raise
    with caplog.at_level("WARNING"):
        verify_exclusion_of_co_occurrence(co_df)
    
    assert "Co-occurrence data loaded but must be excluded" in caplog.text

def test_save_output(tmp_path):
    df = pd.DataFrame({
        "ingredient_id": ["ing1"],
        "functional_role": ["primary"]
    })
    output_path = tmp_path / "functional_roles.csv"
    save_output(df, output_path)
    
    assert output_path.exists()
    loaded = pd.read_csv(output_path)
    assert len(loaded) == 1
    assert loaded.iloc[0]["functional_role"] == "primary"
