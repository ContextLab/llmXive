"""
Unit tests for the ingestion module.

Tests verify that:
1. Microbiome and cognitive data are loaded correctly
2. Merge operation works as expected
3. Invalid files raise appropriate errors
4. Column conflicts are handled properly
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
    ingest_synthetic_cohort
)
from code.src.utils.config import RAW_DATA_DIR, DATA_DIR


class TestLoadMicrobiomeData:
    """Tests for load_microbiome_data function."""
    
    def test_load_valid_microbiome_data(self, tmp_path):
        """Test loading valid microbiome data."""
        # Create test data
        data = {
            'participant_id': ['P001', 'P002', 'P003'],
            'shannon_diversity': [3.5, 4.2, 3.8],
            'simpson_diversity': [0.85, 0.92, 0.88],
            'chao1_diversity': [150, 180, 165],
            'age': [65, 70, 75],
            'sex': ['M', 'F', 'M'],
            'bmi': [25.0, 27.0, 24.0],
            'fiber_intake': [20.0, 25.0, 22.0],
            'antibiotics_use': [0, 1, 0]
        }
        df = pd.DataFrame(data)
        
        file_path = tmp_path / "microbiome.csv"
        df.to_csv(file_path, index=False)
        
        # Load and verify
        loaded = load_microbiome_data(file_path)
        
        assert len(loaded) == 3
        assert list(loaded.columns) == list(df.columns)
        assert loaded['participant_id'].tolist() == ['P001', 'P002', 'P003']
    
    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        file_path = tmp_path / "nonexistent.csv"
        
        with pytest.raises(FileNotFoundError):
            load_microbiome_data(file_path)
    
    def test_load_missing_columns(self, tmp_path):
        """Test that ValueError is raised for missing required columns."""
        data = {
            'participant_id': ['P001', 'P002'],
            'shannon_diversity': [3.5, 4.2]
            # Missing other required columns
        }
        df = pd.DataFrame(data)
        
        file_path = tmp_path / "incomplete.csv"
        df.to_csv(file_path, index=False)
        
        with pytest.raises(ValueError) as exc_info:
            load_microbiome_data(file_path)
        
        assert "missing required columns" in str(exc_info.value)


class TestLoadCognitiveData:
    """Tests for load_cognitive_data function."""
    
    def test_load_valid_cognitive_data(self, tmp_path):
        """Test loading valid cognitive data."""
        data = {
            'participant_id': ['P001', 'P002', 'P003'],
            'cognitive_flexibility_score': [45.0, 52.0, 48.0],
            'age': [65, 70, 75],
            'sex': ['M', 'F', 'M'],
            'bmi': [25.0, 27.0, 24.0],
            'fiber_intake': [20.0, 25.0, 22.0],
            'antibiotics_use': [0, 1, 0]
        }
        df = pd.DataFrame(data)
        
        file_path = tmp_path / "cognitive.csv"
        df.to_csv(file_path, index=False)
        
        # Load and verify
        loaded = load_cognitive_data(file_path)
        
        assert len(loaded) == 3
        assert 'cognitive_flexibility_score' in loaded.columns
        assert loaded['participant_id'].tolist() == ['P001', 'P002', 'P003']
    
    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        file_path = tmp_path / "nonexistent.csv"
        
        with pytest.raises(FileNotFoundError):
            load_cognitive_data(file_path)
    
    def test_load_missing_columns(self, tmp_path):
        """Test that ValueError is raised for missing required columns."""
        data = {
            'participant_id': ['P001', 'P002'],
            'cognitive_flexibility_score': [45.0, 52.0]
            # Missing other required columns
        }
        df = pd.DataFrame(data)
        
        file_path = tmp_path / "incomplete.csv"
        df.to_csv(file_path, index=False)
        
        with pytest.raises(ValueError) as exc_info:
            load_cognitive_data(file_path)
        
        assert "missing required columns" in str(exc_info.value)


class TestMergeDatasets:
    """Tests for merge_datasets function."""
    
    def test_merge_successful(self):
        """Test successful merge of microbiome and cognitive data."""
        microbiome_df = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003'],
            'shannon_diversity': [3.5, 4.2, 3.8],
            'age': [65, 70, 75],
            'sex': ['M', 'F', 'M'],
            'bmi': [25.0, 27.0, 24.0],
            'fiber_intake': [20.0, 25.0, 22.0],
            'antibiotics_use': [0, 1, 0]
        })
        
        cognitive_df = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003'],
            'cognitive_flexibility_score': [45.0, 52.0, 48.0],
            'age': [65, 70, 75],
            'sex': ['M', 'F', 'M'],
            'bmi': [25.0, 27.0, 24.0],
            'fiber_intake': [20.0, 25.0, 22.0],
            'antibiotics_use': [0, 1, 0]
        })
        
        merged = merge_datasets(microbiome_df, cognitive_df)
        
        assert len(merged) == 3
        assert 'shannon_diversity' in merged.columns
        assert 'cognitive_flexibility_score' in merged.columns
        assert 'participant_id' in merged.columns
        # Should not have duplicate columns
        assert merged.shape[1] == len(set(merged.columns))
    
    def test_merge_partial_overlap(self):
        """Test merge with only partial participant overlap."""
        microbiome_df = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003'],
            'shannon_diversity': [3.5, 4.2, 3.8],
            'age': [65, 70, 75],
            'sex': ['M', 'F', 'M'],
            'bmi': [25.0, 27.0, 24.0],
            'fiber_intake': [20.0, 25.0, 22.0],
            'antibiotics_use': [0, 1, 0]
        })
        
        cognitive_df = pd.DataFrame({
            'participant_id': ['P002', 'P003', 'P004'],
            'cognitive_flexibility_score': [52.0, 48.0, 55.0],
            'age': [70, 75, 80],
            'sex': ['F', 'M', 'F'],
            'bmi': [27.0, 24.0, 26.0],
            'fiber_intake': [25.0, 22.0, 28.0],
            'antibiotics_use': [1, 0, 1]
        })
        
        merged = merge_datasets(microbiome_df, cognitive_df)
        
        # Should only have P002 and P003 (inner join)
        assert len(merged) == 2
        assert 'P001' not in merged['participant_id'].tolist()
        assert 'P004' not in merged['participant_id'].tolist()
    
    def test_merge_empty_result(self):
        """Test that ValueError is raised when merge results in empty DataFrame."""
        microbiome_df = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'shannon_diversity': [3.5, 4.2],
            'age': [65, 70],
            'sex': ['M', 'F'],
            'bmi': [25.0, 27.0],
            'fiber_intake': [20.0, 25.0],
            'antibiotics_use': [0, 1]
        })
        
        cognitive_df = pd.DataFrame({
            'participant_id': ['P003', 'P004'],
            'cognitive_flexibility_score': [48.0, 55.0],
            'age': [75, 80],
            'sex': ['M', 'F'],
            'bmi': [24.0, 26.0],
            'fiber_intake': [22.0, 28.0],
            'antibiotics_use': [0, 1]
        })
        
        with pytest.raises(ValueError) as exc_info:
            merge_datasets(microbiome_df, cognitive_df)
        
        assert "empty DataFrame" in str(exc_info.value)
    
    def test_merge_covariate_conflict_handling(self):
        """Test that matching covariates are handled correctly."""
        microbiome_df = pd.DataFrame({
            'participant_id': ['P001'],
            'shannon_diversity': [3.5],
            'age': [65],
            'sex': ['M'],
            'bmi': [25.0],
            'fiber_intake': [20.0],
            'antibiotics_use': [0]
        })
        
        cognitive_df = pd.DataFrame({
            'participant_id': ['P001'],
            'cognitive_flexibility_score': [45.0],
            'age': [65],  # Same value
            'sex': ['M'],
            'bmi': [25.0],
            'fiber_intake': [20.0],
            'antibiotics_use': [0]
        })
        
        merged = merge_datasets(microbiome_df, cognitive_df)
        
        # Should have only one 'age' column, not 'age_micro' and 'age_cog'
        assert 'age' in merged.columns
        assert 'age_micro' not in merged.columns
        assert 'age_cog' not in merged.columns


class TestIngestSyntheticCohort:
    """Tests for the main ingestion function."""
    
    def test_ingest_synthetic_cohort_integration(self):
        """Test end-to-end ingestion of synthetic data."""
        # This test relies on generate_synthetic_cohort creating valid files
        # We verify the merged result has expected structure
        merged_df = ingest_synthetic_cohort()
        
        assert isinstance(merged_df, pd.DataFrame)
        assert len(merged_df) > 0
        assert 'participant_id' in merged_df.columns
        assert 'shannon_diversity' in merged_df.columns
        assert 'cognitive_flexibility_score' in merged_df.columns
        
        # Verify no duplicate columns
        assert merged_df.shape[1] == len(set(merged_df.columns))