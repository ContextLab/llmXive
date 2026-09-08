"""
Unit tests for T010: code/ingest.py

Tests verify:
- research.md parsing logic
- Error handling for missing/invalid sources
- (Mocked) data fetching behavior
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

# Add code directory to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from ingest import parse_research_md, fetch_openml_data, fetch_huggingface_data, ingest_all_data

class TestParseResearchMd:
    def test_valid_research_md(self, tmp_path):
        """Test parsing a valid research.md file."""
        research_content = """
        # Research Data Sources
        ## Data Sources
        - OpenML: 43667
        - HuggingFace: lst-wear-dataset
        - Literature: https://example.com/data1.csv, https://example.com/data2.csv
        """
        research_file = tmp_path / "research.md"
        research_file.write_text(research_content)
        
        with patch("ingest.RESEARCH_FILE", research_file):
            result = parse_research_md()
            
            assert result['openml_id'] == "43667"
            assert result['huggingface_dataset_id'] == "lst-wear-dataset"
            assert len(result['literature_urls']) == 2
            assert "https://example.com/data1.csv" in result['literature_urls']

    def test_missing_research_md(self):
        """Test error when research.md is missing."""
        with patch("ingest.RESEARCH_FILE", Path("/nonexistent/research.md")):
            with pytest.raises(FileNotFoundError, match="research.md not found"):
                parse_research_md()

    def test_missing_required_ids(self, tmp_path):
        """Test error when required IDs are missing."""
        research_content = """
        # Research Data Sources
        ## Data Sources
        - OpenML: TBD
        - HuggingFace: TBD
        """
        research_file = tmp_path / "research.md"
        research_file.write_text(research_content)
        
        with patch("ingest.RESEARCH_FILE", research_file):
            with pytest.raises(ValueError, match="missing required static data source IDs"):
                parse_research_md()

class TestFetchOpenML:
    @patch('ingest.load_dataset')
    def test_successful_fetch(self, mock_load_dataset, tmp_path):
        """Test successful OpenML fetch."""
        mock_dataset = MagicMock()
        mock_df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        mock_dataset.to_pandas.return_value = mock_df
        mock_load_dataset.return_value = mock_dataset
        
        result = fetch_openml_data("43667")
        
        assert len(result) == 2
        mock_load_dataset.assert_called_once_with('openml', "43667", split='train')

    @patch('ingest.load_dataset')
    def test_failed_fetch(self, mock_load_dataset):
        """Test error when OpenML fetch fails."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with pytest.raises(RuntimeError, match="OpenML fetch failed"):
            fetch_openml_data("43667")

class TestFetchHuggingFace:
    @patch('ingest.load_dataset')
    def test_successful_fetch(self, mock_load_dataset):
        """Test successful HuggingFace fetch."""
        mock_dataset = MagicMock()
        mock_df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        mock_dataset.to_pandas.return_value = mock_df
        mock_load_dataset.return_value = mock_dataset
        
        result = fetch_huggingface_data("lst-wear-dataset")
        
        assert len(result) == 2
        mock_load_dataset.assert_called_once_with("lst-wear-dataset", split='train')

    @patch('ingest.load_dataset')
    def test_failed_fetch(self, mock_load_dataset):
        """Test error when HuggingFace fetch fails."""
        mock_load_dataset.side_effect = Exception("Dataset not found")
        
        with pytest.raises(RuntimeError, match="HuggingFace fetch failed"):
            fetch_huggingface_data("lst-wear-dataset")

class TestIngestAllData:
    @patch("ingest.parse_research_md")
    @patch("ingest.fetch_openml_data")
    @patch("ingest.fetch_huggingface_data")
    @patch("ingest.fetch_literature_data")
    def test_full_ingest_flow(self, mock_lit, mock_hf, mock_openml, mock_parse, tmp_path):
        """Test full ingestion flow with mocked sources."""
        # Setup mocks
        mock_parse.return_value = {
            'openml_id': '43667',
            'huggingface_dataset_id': 'lst-wear',
            'literature_urls': ['https://example.com/data.csv']
        }
        
        df1 = pd.DataFrame({'a': [1]})
        df2 = pd.DataFrame({'b': [2]})
        df3 = pd.DataFrame({'c': [3]})
        
        mock_openml.return_value = df1
        mock_hf.return_value = df2
        mock_lit.return_value = [df3]
        
        # Run
        result = ingest_all_data()
        
        # Verify
        assert len(result) == 3  # 1+1+1
        mock_parse.assert_called_once()
        mock_openml.assert_called_once_with('43667')
        mock_hf.assert_called_once_with('lst-wear')
        mock_lit.assert_called_once_with(['https://example.com/data.csv'])