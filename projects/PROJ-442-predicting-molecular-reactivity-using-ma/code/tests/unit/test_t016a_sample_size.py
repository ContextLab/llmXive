"""
Unit tests for T016a: Sample size check and logging.
"""
import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path

from src.data.ingestion import filter_by_class_sample_size
from src.utils.logging import setup_logger


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe with known class distribution."""
    data = {
        "id": range(2500),
        "reaction_smiles": ["CCO" for _ in range(2500)],
        "reactants": [["CCO"]] * 2500,
        "products": [["CC"]] * 2500,
        "reaction_type": (
            ["SN1"] * 1500 + 
            ["SN2"] * 800 + 
            ["Diels-Alder"] * 200
        ),
        "target_value": [50.0] * 2500,
        "target_source": ["yield_pct"] * 2500
    }
    return pd.DataFrame(data)


def test_filter_by_class_sample_size(sample_dataframe):
    """Test that low-sample classes are correctly identified and excluded."""
    # Run filter
    filtered_df, excluded_classes = filter_by_class_sample_size(sample_dataframe, min_samples=1000)
    
    # Check results
    assert "SN1" not in excluded_classes[0]["class"] or excluded_classes[0]["class"] == "SN1"
    
    # SN1 has 1500 samples, should be included
    # SN2 has 800 samples, should be excluded
    # Diels-Alder has 200 samples, should be excluded
    
    excluded_class_names = [c["class"] for c in excluded_classes]
    assert "SN2" in excluded_class_names
    assert "Diels-Alder" in excluded_class_names
    assert "SN1" not in excluded_class_names
    
    # Check filtered dataframe
    assert len(filtered_df) == 1500
    assert set(filtered_df["reaction_type"].unique()) == {"SN1"}


def test_filter_by_class_sample_size_all_removed(sample_dataframe):
    """Test behavior when all classes have < min_samples."""
    # Modify dataframe to have all small classes
    small_df = sample_dataframe.head(500).copy()
    small_df["reaction_type"] = ["SN1"] * 500
    
    filtered_df, excluded_classes = filter_by_class_sample_size(small_df, min_samples=1000)
    
    assert len(excluded_classes) == 1
    assert excluded_classes[0]["class"] == "SN1"
    assert len(filtered_df) == 0


def test_filter_by_class_sample_size_none_removed(sample_dataframe):
    """Test behavior when all classes have >= min_samples."""
    # Modify dataframe to have all large classes
    large_df = sample_dataframe.copy()
    # Make SN2 and Diels-Alder large
    large_df.loc[large_df["reaction_type"] == "SN2", "reaction_type"] = "SN1"
    large_df.loc[large_df["reaction_type"] == "Diels-Alder", "reaction_type"] = "SN1"
    
    filtered_df, excluded_classes = filter_by_class_sample_size(large_df, min_samples=1000)
    
    assert len(excluded_classes) == 0
    assert len(filtered_df) == len(large_df)