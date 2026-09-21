import pytest
from unittest.mock import patch, MagicMock
import itertools
from code.src.data_loader import (
    DataFetchError,
    load_pg19_streaming,
    filter_long_documents,
    get_document_iterator
)
from code.src.config import Config

class TestTokenCounting:
    def test_filter_long_documents_includes_long(self):
        """Test that documents with enough tokens are included."""
        docs = [{"text": "A" * 200000}] # ~50k tokens
        filtered = list(filter_long_documents(iter(docs), min_tokens=32000))
        assert len(filtered) == 1
        assert "_estimated_tokens" in filtered[0]

    def test_filter_long_documents_excludes_short(self):
        """Test that documents with too few tokens are excluded."""
        docs = [{"text": "Short"}]
        filtered = list(filter_long_documents(iter(docs), min_tokens=32000))
        assert len(filtered) == 0

class TestFiltering:
    def test_sampling_logic(self):
        """Test that sampling limits the number of items returned."""
        config = Config(seed=42)
        # Mock the load function to return a known list
        mock_data = [{"text": str(i)} for i in range(100)]
        
        with patch('code.src.data_loader.load_pg19_streaming', return_value=iter(mock_data)):
            with patch('code.src.data_loader.filter_long_documents', side_effect=lambda x, y: x):
                iterator = get_document_iterator(config, sample_size=5)
                result = list(iterator)
                
                assert len(result) == 5
                assert isinstance(result, list)

class TestIntegration:
    @patch('code.src.data_loader.load_dataset')
    def test_load_pg19_streaming_raises_on_failure(self, mock_load):
        """Test that DataFetchError is raised if the real source fails."""
        mock_load.side_effect = Exception("Connection timeout")
        config = Config(seed=42)
        
        with pytest.raises(DataFetchError):
            load_pg19_streaming(config)