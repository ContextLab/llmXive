"""
Unit tests for the real-world dataset ingestion pipeline.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import yaml

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocessing.ingestion import (
    RealWorldDataset,
    load_dataset_config,
    download_dataset,
    clean_dataset,
    compute_checksum,
    update_manifest,
    process_real_world_dataset,
    run_ingestion_pipeline,
    validate_dataset_availability
)


class TestDatasetIngestion:
    """Tests for the ingestion pipeline components."""

    def test_load_dataset_config_success(self, tmp_path):
        """Test loading a valid YAML config."""
        config_content = """
        datasets:
          - id: "test/dataset"
            source: "Test Source"
            splits: ["train"]
        """
        config_file = tmp_path / "datasets.yaml"
        config_file.write_text(config_content)
        
        result = load_dataset_config(str(config_file))
        
        assert len(result) == 1
        assert result[0]['id'] == "test/dataset"
        assert result[0]['source'] == "Test Source"

    def test_load_dataset_config_missing_file(self):
        """Test loading a non-existent config file."""
        with pytest.raises(FileNotFoundError):
            load_dataset_config("non_existent_path.yaml")

    def test_load_dataset_config_empty(self, tmp_path):
        """Test loading an empty config file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("datasets: []")
        
        result = load_dataset_config(str(config_file))
        assert result == []

    def test_clean_dataset_drops_all_nan_rows(self):
        """Test that clean_dataset removes rows where all values are NaN."""
        df = pd.DataFrame({
            'A': [1.0, np.nan, 3.0],
            'B': [4.0, np.nan, 6.0],
            'C': [7.0, np.nan, 9.0]
        })
        
        # Row 1 is all NaN
        cleaned = clean_dataset(df)
        
        assert len(cleaned) == 2
        assert list(cleaned.index) == [0, 2]

    def test_clean_dataset_empty_dataframe(self):
        """Test cleaning an empty DataFrame."""
        df = pd.DataFrame()
        cleaned = clean_dataset(df)
        assert cleaned.empty

    def test_compute_checksum_consistency(self):
        """Test that the same DataFrame produces the same checksum."""
        df1 = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        df2 = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        
        checksum1 = compute_checksum(df1)
        checksum2 = compute_checksum(df2)
        
        assert checksum1 == checksum2

    def test_update_manifest_creates_file(self, tmp_path):
        """Test that update_manifest creates the CSV file."""
        output_file = tmp_path / "log.csv"
        entries = [
            RealWorldDataset(
                dataset_id="id1",
                source_url="url1",
                data=pd.DataFrame(),
                row_count=10,
                checksum="abc123",
                status="success"
            )
        ]
        
        update_manifest(entries, str(output_file))
        
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r') as f:
            content = f.read()
            assert "id1" in content
            assert "success" in content
            assert "10" in content

    @patch('preprocessing.ingestion.load_dataset')
    def test_download_dataset_streaming(self, mock_load_dataset, tmp_path):
        """Test downloading a dataset in streaming mode."""
        # Mock the streaming dataset object
        mock_ds = MagicMock()
        mock_ds.__iter__ = lambda self: iter([{'a': 1}, {'a': 2}])
        mock_load_dataset.return_value = mock_ds
        
        config = {'id': 'test/id', 'splits': ['train']}
        
        df = download_dataset('test/id', config, streaming=True)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        mock_load_dataset.assert_called_once_with('test/id', split='train', streaming=True)

    @patch('preprocessing.ingestion.load_dataset')
    def test_download_dataset_failure(self, mock_load_dataset):
        """Test that download_dataset raises RuntimeError on failure."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        config = {'id': 'test/id', 'splits': ['train']}
        
        with pytest.raises(RuntimeError, match="Failed to download dataset"):
            download_dataset('test/id', config, streaming=True)

    @patch('preprocessing.ingestion.download_dataset')
    @patch('preprocessing.ingestion.clean_dataset')
    def test_process_real_world_dataset_success(self, mock_clean, mock_download):
        """Test successful processing of a real-world dataset."""
        mock_download.return_value = pd.DataFrame({'A': [1, 2, 3]})
        mock_clean.return_value = pd.DataFrame({'A': [1, 2, 3]})
        
        config = {'id': 'test/id', 'source': 'test_source', 'splits': ['train']}
        
        result = process_real_world_dataset(config)
        
        assert result.status == "success"
        assert result.row_count == 3
        assert result.dataset_id == "test/id"

    @patch('preprocessing.ingestion.download_dataset')
    def test_process_real_world_dataset_failure(self, mock_download):
        """Test processing a dataset that fails to download."""
        mock_download.side_effect = RuntimeError("Fetch failed")
        
        config = {'id': 'test/id', 'source': 'test_source', 'splits': ['train']}
        
        result = process_real_world_dataset(config)
        
        assert result.status == "failed"
        assert "Fetch failed" in result.error_message

    @patch('preprocessing.ingestion.load_dataset_config')
    @patch('preprocessing.ingestion.process_real_world_dataset')
    @patch('preprocessing.ingestion.update_manifest')
    def test_run_ingestion_pipeline(self, mock_update, mock_process, mock_load_config):
        """Test the full ingestion pipeline."""
        mock_load_config.return_value = [{'id': 'id1', 'source': 'src1', 'splits': ['train']}]
        mock_process.return_value = RealWorldDataset(
            dataset_id="id1", source_url="src1", data=pd.DataFrame(), 
            row_count=10, checksum="c1", status="success"
        )
        
        results = run_ingestion_pipeline("fake/path.yaml", "fake/output.csv")
        
        assert len(results) == 1
        assert results[0].status == "success"
        mock_update.assert_called_once()

    @patch('preprocessing.ingestion.load_dataset_config')
    def test_run_ingestion_pipeline_empty_config(self, mock_load_config):
        """Test pipeline with empty config."""
        mock_load_config.return_value = []
        
        results = run_ingestion_pipeline("fake/path.yaml", "fake/output.csv")
        
        assert results == []