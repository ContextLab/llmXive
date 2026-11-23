import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.src.data.ingestion import (
    load_microbiome_data,
    load_cognitive_data,
    merge_datasets,
    ingest_synthetic_cohort,
    save_merged_cohort
)
from code.src.utils.config import get_raw_data_dir

@pytest.fixture
def sample_data_dir(tmp_path):
    """Create a temporary directory with sample synthetic data."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample synthetic data
    data = {
        'participant_id': ['P001', 'P002', 'P003'],
        'age': [65, 72, 68],
        'sex': ['M', 'F', 'M'],
        'bmi': [24.5, 27.1, 22.8],
        'cognitive_flexibility_score': [0.85, 0.72, 0.91],
        'shannon_diversity': [3.2, 3.5, 3.1],
        'simpson_diversity': [0.88, 0.92, 0.85],
        'chao1': [120.5, 135.2, 118.9],
        'dietary_fiber_intake': [25.0, 18.5, 30.2],
        'antibiotic_use_history': [False, True, False]
    }
    
    df = pd.DataFrame(data)
    csv_path = raw_dir / "synthetic_data.csv"
    df.to_csv(csv_path, index=False)
    
    return raw_dir

class TestLoadMicrobiomeData:
    def test_load_microbiome_data_success(self, sample_data_dir, tmp_path):
        """Test successful loading of microbiome data."""
        with patch('code.src.data.ingestion.get_raw_data_dir', return_value=sample_data_dir):
            df = load_microbiome_data(sample_data_dir)
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3
            assert 'participant_id' in df.columns
            assert df['participant_id'].dtype == object  # Should be string
            assert df.iloc[0]['participant_id'] == 'P001'

    def test_load_microbiome_data_file_not_found(self, tmp_path):
        """Test error handling when file does not exist."""
        non_existent_dir = tmp_path / "non_existent"
        with pytest.raises(FileNotFoundError):
            load_microbiome_data(non_existent_dir)

class TestLoadCognitiveData:
    def test_load_cognitive_data_success(self, sample_data_dir, tmp_path):
        """Test successful loading of cognitive data."""
        with patch('code.src.data.ingestion.get_raw_data_dir', return_value=sample_data_dir):
            df = load_cognitive_data(sample_data_dir)
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3
            assert 'cognitive_flexibility_score' in df.columns
            assert df.iloc[0]['cognitive_flexibility_score'] == 0.85

    def test_load_cognitive_data_file_not_found(self, tmp_path):
        """Test error handling when file does not exist."""
        non_existent_dir = tmp_path / "non_existent"
        with pytest.raises(FileNotFoundError):
            load_cognitive_data(non_existent_dir)

class TestMergeDatasets:
    def test_merge_datasets_success(self, sample_data_dir, tmp_path):
        """Test successful merging of datasets."""
        with patch('code.src.data.ingestion.get_raw_data_dir', return_value=sample_data_dir):
            micro_df = load_microbiome_data(sample_data_dir)
            cog_df = load_cognitive_data(sample_data_dir)
            
            merged = merge_datasets(micro_df, cog_df)
            
            assert isinstance(merged, pd.DataFrame)
            assert len(merged) == 3
            assert 'participant_id' in merged.columns
            assert 'age' in merged.columns
            assert 'cognitive_flexibility_score' in merged.columns

    def test_merge_datasets_missing_column(self, tmp_path):
        """Test error when required column is missing."""
        micro_df = pd.DataFrame({'other_col': [1, 2, 3]})
        cog_df = pd.DataFrame({'participant_id': ['P1', 'P2', 'P3']})
        
        with pytest.raises(ValueError, match="missing required column"):
            merge_datasets(micro_df, cog_df)

    def test_merge_datasets_different_ids(self, tmp_path):
        """Test merge with non-matching IDs results in empty or fewer rows."""
        micro_df = pd.DataFrame({'participant_id': ['P1', 'P2', 'P3']})
        cog_df = pd.DataFrame({'participant_id': ['P4', 'P5', 'P6']})
        
        merged = merge_datasets(micro_df, cog_df)
        
        assert len(merged) == 0  # Inner join with no matches

class TestIngestSyntheticCohort:
    @patch('code.src.data.ingestion.load_schema')
    @patch('code.src.data.ingestion.validate_dataframe_against_schema', return_value=[])
    def test_ingest_synthetic_cohort_success(self, mock_validate, mock_load_schema, sample_data_dir, tmp_path):
        """Test successful ingestion pipeline."""
        with patch('code.src.data.ingestion.get_raw_data_dir', return_value=sample_data_dir):
            df = ingest_synthetic_cohort()
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3
            mock_load_schema.assert_called_once_with("dataset")
            mock_validate.assert_called_once()

    @patch('code.src.data.ingestion.load_schema')
    @patch('code.src.data.ingestion.validate_dataframe_against_schema', return_value=["Error: Invalid type"])
    def test_ingest_synthetic_cohort_validation_fail(self, mock_validate, mock_load_schema, sample_data_dir, tmp_path):
        """Test ingestion fails on schema validation error."""
        with patch('code.src.data.ingestion.get_raw_data_dir', return_value=sample_data_dir):
            with pytest.raises(ValueError, match="Schema validation failed"):
                ingest_synthetic_cohort()

class TestSaveMergedCohort:
    def test_save_merged_cohort(self, sample_data_dir, tmp_path):
        """Test saving merged cohort to CSV."""
        with patch('code.src.data.ingestion.get_raw_data_dir', return_value=sample_data_dir):
            df = ingest_synthetic_cohort()
            
            output_path = tmp_path / "output" / "merged_cohort.csv"
            result_path = save_merged_cohort(df, output_path)
            
            assert result_path == output_path
            assert output_path.exists()
            
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == 3
            assert 'participant_id' in saved_df.columns