"""
Unit tests for T016c: Filtering by class sample size.
Tests the generation of filtered_reactions_clean.csv and exclusion metadata.
"""
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.data.ingestion import filter_by_class_sample_size

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with varying class sizes."""
    data = {
        "reaction_smiles": ["A>B", "C>D", "E>F", "G>H", "I>J", "K>L"],
        "reaction_type": ["SN1", "SN1", "SN2", "SN2", "Diels-Alder", "Diels-Alder"],
        "target_value": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "target_source": ["yield_pct"] * 6,
        "row_id": [1, 2, 3, 4, 5, 6],
    }
    # Expand to meet sample size thresholds for testing
    # SN1: 2 samples, SN2: 2 samples, Diels-Alder: 2 samples
    # We will simulate a larger dataset in the test logic
    return pd.DataFrame(data)

def test_filter_by_class_sample_size():
    """Test filtering with a threshold that excludes some classes."""
    # Create a dataset where SN1 has 500, SN2 has 1500, Diels-Alder has 500
    # Threshold = 1000 -> SN1 and Diels-Alder should be excluded
    data = {
        "reaction_smiles": ["A"] * 500 + ["B"] * 1500 + ["C"] * 500,
        "reaction_type": ["SN1"] * 500 + ["SN2"] * 1500 + ["Diels-Alder"] * 500,
        "target_value": [1.0] * 2500,
        "target_source": ["yield_pct"] * 2500,
        "row_id": list(range(2500)),
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        meta_path = os.path.join(tmpdir, "metadata.json")
        df_filtered, meta = filter_by_class_sample_size(
            df, min_samples=1000, metadata_output=meta_path
        )

        # Check counts
        assert len(df_filtered) == 1500
        assert df_filtered["reaction_type"].unique().tolist() == ["SN2"]

        # Check metadata
        assert meta is not None
        assert os.path.exists(meta)
        with open(meta, "r") as f:
            metadata = json.load(f)
        
        assert len(metadata["excluded_classes"]) == 2
        excluded_names = [c["class"] for c in metadata["excluded_classes"]]
        assert "SN1" in excluded_names
        assert "Diels-Alder" in excluded_names

def test_filter_by_class_sample_size_all_removed():
    """Test filtering when all classes are below threshold."""
    data = {
        "reaction_smiles": ["A"] * 100 + ["B"] * 100,
        "reaction_type": ["SN1"] * 100 + ["SN2"] * 100,
        "target_value": [1.0] * 200,
        "target_source": ["yield_pct"] * 200,
        "row_id": list(range(200)),
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        meta_path = os.path.join(tmpdir, "metadata.json")
        df_filtered, meta = filter_by_class_sample_size(
            df, min_samples=1000, metadata_output=meta_path
        )

        assert len(df_filtered) == 0
        assert meta is not None
        with open(meta, "r") as f:
            metadata = json.load(f)
        assert len(metadata["excluded_classes"]) == 2

def test_filter_by_class_sample_size_none_removed():
    """Test filtering when all classes meet threshold."""
    data = {
        "reaction_smiles": ["A"] * 1500 + ["B"] * 2000,
        "reaction_type": ["SN1"] * 1500 + ["SN2"] * 2000,
        "target_value": [1.0] * 3500,
        "target_source": ["yield_pct"] * 3500,
        "row_id": list(range(3500)),
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        meta_path = os.path.join(tmpdir, "metadata.json")
        df_filtered, meta = filter_by_class_sample_size(
            df, min_samples=1000, metadata_output=meta_path
        )

        assert len(df_filtered) == 3500
        assert meta is None # No metadata written if no exclusions