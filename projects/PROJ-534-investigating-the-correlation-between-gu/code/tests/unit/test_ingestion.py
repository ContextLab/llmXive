import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Adjust import path based on project structure (code/src/data/ingestion.py)
from code.src.data.ingestion import (
    load_microbiome_data,
    load_cognitive_data,
    merge_datasets,
    ingest_synthetic_cohort,
    save_merged_cohort
)

@pytest.fixture
def sample_data_dir(tmp_path):
    """Create a temporary directory with sample CSV files."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    # Create a synthetic data file matching T008 output structure
    data = {
        "participant_id": ["P001", "P002", "P003"],
        "age": [65, 70, 80],
        "sex": ["M", "F", "F"],
        "bmi": [24.5, 26.1, 22.3],
        "cognitive_flexibility_score": [0.85, 0.72, 0.91],
        "shannon_diversity": [3.2, 3.5, 3.1],
        "simpson_diversity": [0.92, 0.94, 0.91],
        "chao1": [150.0, 160.0, 145.0],
        "dietary_fiber": [25.0, 30.0, 20.0],
        "antibiotic_use": [False, True, False]
    }
    df = pd.DataFrame(data)
    csv_path = raw_dir / "synthetic_data.csv"
    df.to_csv(csv_path, index=False)
    
    return raw_dir, csv_path

class TestLoadMicrobiomeData:
    def test_load_microbiome_data_success(self, sample_data_dir):
        raw_dir, csv_path = sample_data_dir
        # In this simplified synthetic setup, load_microbiome_data reads the combined file
        # and we expect it to handle the columns present.
        # Note: The real implementation might filter columns, but for T010 we just load.
        df = load_microbiome_data(csv_path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "participant_id" in df.columns
        assert "shannon_diversity" in df.columns

    def test_load_microbiome_data_file_not_found(self, tmp_path):
        non_existent = tmp_path / "missing.csv"
        with pytest.raises(FileNotFoundError):
            load_microbiome_data(non_existent)

class TestLoadCognitiveData:
    def test_load_cognitive_data_success(self, sample_data_dir):
        raw_dir, csv_path = sample_data_dir
        df = load_cognitive_data(csv_path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "cognitive_flexibility_score" in df.columns

    def test_load_cognitive_data_file_not_found(self, tmp_path):
        non_existent = tmp_path / "missing.csv"
        with pytest.raises(FileNotFoundError):
            load_cognitive_data(non_existent)

class TestMergeDatasets:
    def test_merge_datasets_success(self, sample_data_dir):
        raw_dir, csv_path = sample_data_dir
        df = pd.read_csv(csv_path)
        
        # Split into two frames to test merge logic
        micro_df = df[["participant_id", "shannon_diversity", "simpson_diversity"]].copy()
        cog_df = df[["participant_id", "cognitive_flexibility_score", "age"]].copy()
        
        merged = merge_datasets(micro_df, cog_df, key="participant_id")
        
        assert len(merged) == 3
        assert "shannon_diversity" in merged.columns
        assert "cognitive_flexibility_score" in merged.columns
        assert "age" in merged.columns

    def test_merge_datasets_missing_key(self, sample_data_dir):
        raw_dir, csv_path = sample_data_dir
        df = pd.read_csv(csv_path)
        
        micro_df = df[["participant_id", "shannon_diversity"]].copy()
        cog_df = df[["age", "cognitive_flexibility_score"]].copy() # Missing participant_id
        
        with pytest.raises(ValueError):
            merge_datasets(micro_df, cog_df, key="participant_id")

    def test_merge_datasets_empty_result(self, sample_data_dir):
        raw_dir, csv_path = sample_data_dir
        df = pd.read_csv(csv_path)
        
        micro_df = df[["participant_id", "shannon_diversity"]].copy()
        # Change IDs in cog_df so no match
        cog_df = df[["participant_id", "cognitive_flexibility_score"]].copy()
        cog_df["participant_id"] = ["X001", "X002", "X003"]
        
        with pytest.raises(ValueError, match="Merge resulted in an empty dataset"):
            merge_datasets(micro_df, cog_df, key="participant_id")

class TestIngestSyntheticCohort:
    def test_ingest_synthetic_cohort_success(self, sample_data_dir, tmp_path):
        raw_dir, csv_path = sample_data_dir
        # Mock the RAW_DATA_DIR path to point to our temp dir
        with patch('code.src.data.ingestion.RAW_DATA_DIR', raw_dir.parent):
            df = ingest_synthetic_cohort()
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3
            assert "participant_id" in df.columns

    def test_ingest_synthetic_cohort_file_not_found(self, tmp_path):
        fake_raw_dir = tmp_path / "data" / "raw"
        fake_raw_dir.mkdir(parents=True)
        
        with patch('code.src.data.ingestion.RAW_DATA_DIR', fake_raw_dir):
            with pytest.raises(FileNotFoundError):
                ingest_synthetic_cohort()

class TestSaveMergedCohort:
    def test_save_merged_cohort_success(self, sample_data_dir, tmp_path):
        raw_dir, csv_path = sample_data_dir
        df = pd.read_csv(csv_path)
        
        output_path = tmp_path / "processed" / "merged.csv"
        save_merged_cohort(df, output_path)
        
        assert output_path.exists()
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == len(df)