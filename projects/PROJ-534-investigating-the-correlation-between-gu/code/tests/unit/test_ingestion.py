"""
Unit tests for the ingestion module.
"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from code.src.data.ingestion import (
    load_microbiome_data,
    load_cognitive_data,
    merge_datasets,
    ingest_synthetic_cohort,
    save_merged_cohort
)
from code.src.utils.config import RAW_DATA_DIR


class TestLoadMicrobiomeData:
    """Tests for load_microbiome_data function."""

    def test_load_valid_microbiome_data(self, tmp_path):
        """Test loading a valid microbiome CSV file."""
        # Create test data
        data = {
            'participant_id': [1, 2, 3],
            'shannon_diversity': [3.5, 4.2, 3.8],
            'simpson_diversity': [0.85, 0.92, 0.88],
            'chao1': [45, 52, 48]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / 'microbiome.csv'
        df.to_csv(file_path, index=False)

        # Load and verify
        result = load_microbiome_data(file_path)
        assert len(result) == 3
        assert list(result.columns) == ['participant_id', 'shannon_diversity', 'simpson_diversity', 'chao1']

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        file_path = tmp_path / 'nonexistent.csv'
        with pytest.raises(FileNotFoundError):
            load_microbiome_data(file_path)

    def test_load_missing_columns(self, tmp_path):
        """Test that ValueError is raised when required columns are missing."""
        data = {
            'participant_id': [1, 2],
            'shannon_diversity': [3.5, 4.2]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / 'incomplete.csv'
        df.to_csv(file_path, index=False)

        with pytest.raises(ValueError, match="missing required columns"):
            load_microbiome_data(file_path)


class TestLoadCognitiveData:
    """Tests for load_cognitive_data function."""

    def test_load_valid_cognitive_data(self, tmp_path):
        """Test loading a valid cognitive CSV file."""
        data = {
            'participant_id': [1, 2, 3],
            'cognitive_score': [85, 92, 78],
            'age': [68, 72, 65],
            'sex': ['M', 'F', 'M'],
            'bmi': [24.5, 26.1, 23.8],
            'fiber_intake': [25, 30, 22],
            'antibiotics_use': [0, 1, 0]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / 'cognitive.csv'
        df.to_csv(file_path, index=False)

        result = load_cognitive_data(file_path)
        assert len(result) == 3
        assert 'cognitive_score' in result.columns
        assert 'age' in result.columns

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        file_path = tmp_path / 'nonexistent.csv'
        with pytest.raises(FileNotFoundError):
            load_cognitive_data(file_path)

    def test_load_missing_columns(self, tmp_path):
        """Test that ValueError is raised when required columns are missing."""
        data = {
            'participant_id': [1, 2],
            'cognitive_score': [85, 92]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / 'incomplete.csv'
        df.to_csv(file_path, index=False)

        with pytest.raises(ValueError, match="missing required columns"):
            load_cognitive_data(file_path)


class TestMergeDatasets:
    """Tests for merge_datasets function."""

    def test_merge_successful(self):
        """Test successful merge of two valid datasets."""
        microbiome_df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'shannon_diversity': [3.5, 4.2, 3.8],
            'simpson_diversity': [0.85, 0.92, 0.88],
            'chao1': [45, 52, 48]
        })

        cognitive_df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'cognitive_score': [85, 92, 78],
            'age': [68, 72, 65],
            'sex': ['M', 'F', 'M'],
            'bmi': [24.5, 26.1, 23.8],
            'fiber_intake': [25, 30, 22],
            'antibiotics_use': [0, 1, 0]
        })

        result = merge_datasets(microbiome_df, cognitive_df)
        assert len(result) == 3
        assert 'shannon_diversity' in result.columns
        assert 'cognitive_score' in result.columns

    def test_merge_no_overlap(self):
        """Test that merge raises ValueError when no participant IDs overlap."""
        microbiome_df = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'shannon_diversity': [3.5, 4.2, 3.8],
            'simpson_diversity': [0.85, 0.92, 0.88],
            'chao1': [45, 52, 48]
        })

        cognitive_df = pd.DataFrame({
            'participant_id': [4, 5, 6],
            'cognitive_score': [85, 92, 78],
            'age': [68, 72, 65],
            'sex': ['M', 'F', 'M'],
            'bmi': [24.5, 26.1, 23.8],
            'fiber_intake': [25, 30, 22],
            'antibiotics_use': [0, 1, 0]
        })

        with pytest.raises(ValueError, match="Merge resulted in no rows"):
            merge_datasets(microbiome_df, cognitive_df)

    def test_merge_deduplicates(self):
        """Test that merge handles duplicate participant IDs."""
        microbiome_df = pd.DataFrame({
            'participant_id': [1, 1, 2],
            'shannon_diversity': [3.5, 3.6, 4.2],
            'simpson_diversity': [0.85, 0.86, 0.92],
            'chao1': [45, 46, 52]
        })

        cognitive_df = pd.DataFrame({
            'participant_id': [1, 2],
            'cognitive_score': [85, 92],
            'age': [68, 72],
            'sex': ['M', 'F'],
            'bmi': [24.5, 26.1],
            'fiber_intake': [25, 30],
            'antibiotics_use': [0, 1]
        })

        # Should not raise, but should deduplicate
        result = merge_datasets(microbiome_df, cognitive_df)
        assert len(result) <= 2  # At most 2 unique IDs


class TestIngestSyntheticCohort:
    """Tests for ingest_synthetic_cohort function."""

    def test_ingest_generates_and_merges(self):
        """Test that ingestion generates data and returns a merged dataframe."""
        # This test relies on the synthetic_gen module working correctly
        result = ingest_synthetic_cohort()
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'participant_id' in result.columns
        assert 'shannon_diversity' in result.columns
        assert 'cognitive_score' in result.columns
        assert 'age' in result.columns

    def test_ingest_creates_files(self, tmp_path, monkeypatch):
        """Test that ingestion creates the expected files on disk."""
        # Temporarily override RAW_DATA_DIR
        monkeypatch.setattr('code.src.data.ingestion.RAW_DATA_DIR', tmp_path)
        monkeypatch.setattr('code.src.data.synthetic_gen.RAW_DATA_DIR', tmp_path)
        
        # Run ingestion
        ingest_synthetic_cohort()
        
        # Verify files exist
        assert (tmp_path / 'microbiome_data.csv').exists()
        assert (tmp_path / 'cognitive_data.csv').exists()
        # Note: merged_cohort.csv is created by save_merged_cohort, not ingest_synthetic_cohort


class TestSaveMergedCohort:
    """Tests for save_merged_cohort function."""

    def test_save_creates_file(self, tmp_path):
        """Test that save creates a CSV file."""
        df = pd.DataFrame({
            'participant_id': [1, 2],
            'value': [10, 20]
        })
        output_path = tmp_path / 'output.csv'
        
        save_merged_cohort(df, output_path)
        
        assert output_path.exists()
        
        # Verify content
        loaded = pd.read_csv(output_path)
        assert len(loaded) == 2
        assert 'participant_id' in loaded.columns

    def test_save_creates_directories(self, tmp_path):
        """Test that save creates parent directories if they don't exist."""
        df = pd.DataFrame({
            'participant_id': [1],
            'value': [10]
        })
        output_path = tmp_path / 'subdir' / 'nested' / 'output.csv'
        
        save_merged_cohort(df, output_path)
        
        assert output_path.exists()