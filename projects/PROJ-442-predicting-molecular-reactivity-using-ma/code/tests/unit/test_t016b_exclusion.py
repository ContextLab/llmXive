"""
Unit tests for T016b: class_exclusion_metadata generation.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest
import pandas as pd

from src.data.ingestion import filter_by_class_sample_size

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'reaction_smiles': ['CCOCC', 'CCOCC', 'CCOCC', 'CCOCC', 'CCOCC', 'CCOCC', 'CCOCC', 'CCOCC', 'CCOCC', 'CCOCC'],
        'reaction_type': ['SN1', 'SN1', 'SN1', 'SN1', 'SN1', 'SN2', 'SN2', 'Diels-Alder', 'Diels-Alder', 'Diels-Alder'],
        'target_value': [0.5, 0.6, 0.7, 0.8, 0.9, 0.5, 0.6, 0.5, 0.6, 0.7],
        'target_source': ['yield_pct', 'yield_pct', 'yield_pct', 'yield_pct', 'yield_pct', 'success_flag', 'success_flag', 'yield_pct', 'yield_pct', 'yield_pct']
    }
    # Add more SN1 samples to exceed threshold
    for i in range(1000):
        data['reaction_smiles'].append('CCOCC')
        data['reaction_type'].append('SN1')
        data['target_value'].append(0.5)
        data['target_source'].append('yield_pct')

    return pd.DataFrame(data)

def test_filter_by_class_sample_size_generates_metadata(sample_dataframe):
    """Test that filter_by_class_sample_size generates correct exclusion metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = os.path.join(tmpdir, "exclusion_metadata.json")
        validation_log_path = os.path.join(tmpdir, "target_validation.log")

        filtered_df, metadata = filter_by_class_sample_size(
            sample_dataframe,
            min_samples=1000,
            output_metadata_path=metadata_path,
            output_validation_log_path=validation_log_path
        )

        # Check metadata structure
        assert "excluded_classes" in metadata
        assert isinstance(metadata["excluded_classes"], list)

        # Check that SN2 and Diels-Alder are excluded (count < 1000)
        excluded_classes = {item["class"]: item["count"] for item in metadata["excluded_classes"]}
        assert "SN2" in excluded_classes
        assert excluded_classes["SN2"] == 2
        assert "Diels-Alder" in excluded_classes
        assert excluded_classes["Diels-Alder"] == 3

        # Check that SN1 is NOT in excluded list (count >= 1000)
        assert "SN1" not in excluded_classes

        # Check filtered dataframe
        assert len(filtered_df) == 1005  # 1000 SN1 + 5 original SN1
        assert filtered_df['reaction_type'].nunique() == 1
        assert 'SN1' in filtered_df['reaction_type'].values

        # Check metadata file exists and is valid JSON
        assert os.path.exists(metadata_path)
        with open(metadata_path, "r") as f:
            saved_metadata = json.load(f)
        assert saved_metadata == metadata

def test_filter_by_class_sample_size_all_removed():
    """Test filtering when all classes are below threshold."""
    df = pd.DataFrame({
        'reaction_smiles': ['CCOCC', 'CCOCC'],
        'reaction_type': ['SN1', 'SN2'],
        'target_value': [0.5, 0.6],
        'target_source': ['yield_pct', 'yield_pct']
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = os.path.join(tmpdir, "exclusion_metadata.json")
        validation_log_path = os.path.join(tmpdir, "target_validation.log")

        filtered_df, metadata = filter_by_class_sample_size(
            df,
            min_samples=1000,
            output_metadata_path=metadata_path,
            output_validation_log_path=validation_log_path
        )

        # All classes should be excluded
        assert len(metadata["excluded_classes"]) == 2
        assert len(filtered_df) == 0

def test_filter_by_class_sample_size_none_removed():
    """Test filtering when all classes meet threshold."""
    # Create a dataframe where all classes have >= 1000 samples
    data = {'reaction_smiles': [], 'reaction_type': [], 'target_value': [], 'target_source': []}
    for cls in ['SN1', 'SN2', 'Diels-Alder']:
        for i in range(1000):
            data['reaction_smiles'].append('CCOCC')
            data['reaction_type'].append(cls)
            data['target_value'].append(0.5)
            data['target_source'].append('yield_pct')

    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = os.path.join(tmpdir, "exclusion_metadata.json")
        validation_log_path = os.path.join(tmpdir, "target_validation.log")

        filtered_df, metadata = filter_by_class_sample_size(
            df,
            min_samples=1000,
            output_metadata_path=metadata_path,
            output_validation_log_path=validation_log_path
        )

        # No classes should be excluded
        assert len(metadata["excluded_classes"]) == 0
        assert len(filtered_df) == len(df)
