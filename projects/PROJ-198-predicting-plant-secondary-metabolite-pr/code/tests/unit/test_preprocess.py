import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.preprocess import map_bgc_to_metabolite, map_bgc_to_metabolite_dataframe

def test_map_bgc_to_metabolite_known_types():
    """Test mapping of known BGC types to metabolite classes."""
    test_cases = [
        ("polyketide", "polyketide"),
        ("non-ribosomal peptide", "non-ribosomal peptide"),
        ("nrps", "non-ribosomal peptide"),
        ("terpene", "terpene"),
        ("alkaloid", "alkaloid"),
        ("siderophore", "siderophore"),
        ("polyketide", "polyketide"),
    ]

    for bgc_type, expected_class in test_cases:
        result = map_bgc_to_metabolite(bgc_type)
        assert result == expected_class, f"Expected '{expected_class}' for '{bgc_type}', got '{result}'"

def test_map_bgc_to_metabolite_unknown_type():
    """Test that unknown BGC types are mapped to 'unknown'."""
    unknown_types = [
        "unknown_type",
        "made_up_class",
        "random_string",
        "nonexistent_bgc",
    ]

    for bgc_type in unknown_types:
        result = map_bgc_to_metabolite(bgc_type)
        assert result == "unknown", f"Expected 'unknown' for '{bgc_type}', got '{result}'"

def test_map_bgc_to_metabolite_empty_and_none():
    """Test handling of empty and None inputs."""
    # Test empty string
    result_empty = map_bgc_to_metabolite("")
    assert result_empty == "unknown", f"Expected 'unknown' for empty string, got '{result_empty}'"

    # Test None
    result_none = map_bgc_to_metabolite(None)
    assert result_none == "unknown", f"Expected 'unknown' for None, got '{result_none}'"

def test_map_bgc_to_metabolite_case_insensitive():
    """Test that mapping is case-insensitive."""
    test_cases = [
        ("Polyketide", "polyketide"),
        ("POLYKETIDE", "polyketide"),
        ("Nrps", "non-ribosomal peptide"),
        ("NRPS", "non-ribosomal peptide"),
        ("Terpene", "terpene"),
    ]

    for bgc_type, expected_class in test_cases:
        result = map_bgc_to_metabolite(bgc_type)
        assert result == expected_class, f"Expected '{expected_class}' for '{bgc_type}', got '{result}'"

def test_map_bgc_to_metabolite_dataframe():
    """Test DataFrame mapping functionality."""
    data = {
        "species": ["Species_A", "Species_B", "Species_C", "Species_D", "Species_E"],
        "bgc_type": ["polyketide", "nrps", "unknown_type", "terpene", "alkaloid"]
    }
    df = pd.DataFrame(data)

    result_df = map_bgc_to_metabolite_dataframe(df, "bgc_type", "metabolite_class")

    assert "metabolite_class" in result_df.columns, "Output column 'metabolite_class' not found"
    assert len(result_df) == 5, "DataFrame length changed"

    # Check specific mappings
    expected_classes = ["polyketide", "non-ribosomal peptide", "unknown", "terpene", "alkaloid"]
    for i, expected in enumerate(expected_classes):
        assert result_df.iloc[i]["metabolite_class"] == expected, \
            f"Row {i}: Expected '{expected}', got '{result_df.iloc[i]['metabolite_class']}'"

def test_map_bgc_to_metabolite_dataframe_invalid_column():
    """Test that an error is raised if the BGC column does not exist."""
    data = {
        "species": ["Species_A", "Species_B"],
        "other_column": ["value1", "value2"]
    }
    df = pd.DataFrame(data)

    with pytest.raises(ValueError, match="Column 'bgc_type' not found"):
        map_bgc_to_metabolite_dataframe(df, "bgc_type")

def test_map_bgc_to_metabolite_partial_matches():
    """Test partial matching via category fallback."""
    # These should match via the category fallback logic
    test_cases = [
        ("polyketide-like", "polyketide"),
        ("terpenoid", "terpene"),
        ("nonribosomal peptide", "non-ribosomal peptide"), # Note: no hyphen
    ]

    for bgc_type, expected_class in test_cases:
        result = map_bgc_to_metabolite(bgc_type)
        assert result == expected_class, f"Expected '{expected_class}' for '{bgc_type}', got '{result}'"
