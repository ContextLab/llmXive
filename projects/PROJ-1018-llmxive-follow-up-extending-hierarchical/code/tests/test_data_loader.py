import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
import itertools
from datasets import Dataset
import json

from src.data_loader import (
    load_pg19_streaming,
    estimate_token_count,
    get_document_iterator,
    filter_long_documents,
    save_filtered_dataset,
    DataFetchError,
    run_filter_pipeline
)

class TestTokenCounting:
    def test_estimate_token_count_with_tokenizer(self):
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        text = "Hello world this is a test."
        count = estimate_token_count(text, tokenizer)
        assert count > 0
        assert isinstance(count, int)

    def test_estimate_token_count_without_tokenizer(self):
        text = "A" * 1000
        count = estimate_token_count(text, None)
        assert count == 250  # 1000 / 4

class TestFiltering:
    def test_filter_long_documents_logic(self):
        docs = [
            {"document_id": "1", "text": "a" * 10000, "token_count": 10000},
            {"document_id": "2", "text": "a" * 40000, "token_count": 40000},
            {"document_id": "3", "text": "a" * 32000, "token_count": 32000},
        ]
        filtered = list(filter_long_documents(iter(docs), min_tokens=32000))
        assert len(filtered) == 2
        assert filtered[0]["document_id"] == "2"
        assert filtered[1]["document_id"] == "3"

    def test_filter_logging_format(self, capsys):
        docs = [
            {"document_id": "skipped_1", "text": "short", "token_count": 100}
        ]
        list(filter_long_documents(iter(docs), min_tokens=32000))
        captured = capsys.readouterr()
        assert "WARNING: Skipping document skipped_1: length 100 < 32000" in captured.out

class TestSampling:
    def test_sample_dataset(self):
        docs = [{"id": i} for i in range(100)]
        sampled = list(itertools.islice(docs, 5))
        assert len(sampled) == 5

class TestIntegration:
    def test_save_filtered_dataset(self):
        docs = [
            {"document_id": "1", "text": "test", "token_count": 50000}
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name
        
        count = save_filtered_dataset(iter(docs), path)
        assert count == 1
        
        with open(path, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["document_id"] == "1"
            assert "text" in data[0]
            assert "token_count" in data[0]
        
        os.remove(path)

    @patch('src.data_loader.load_dataset')
    def test_load_pg19_streaming_failure(self, mock_load):
        mock_load.side_effect = Exception("Network error")
        with pytest.raises(DataFetchError):
            load_pg19_streaming()

    def test_run_filter_pipeline_structure(self):
        # Mock the heavy lifting to ensure structure is correct without network
        with patch('src.data_loader.load_pg19_streaming') as mock_load, \
             patch('src.data_loader.get_document_iterator') as mock_iter, \
             patch('src.data_loader.filter_long_documents') as mock_filter, \
             patch('src.data_loader.save_filtered_dataset') as mock_save:
             
            mock_load.return_value = iter([])
            mock_iter.return_value = iter([])
            mock_filter.return_value = iter([])
            mock_save.return_value = 0
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output = os.path.join(tmpdir, "test.json")
                result = run_filter_pipeline(
                    tokenizer_name="fake/test",
                    output_path=output,
                    min_tokens=32000
                )
                assert result == 0
                mock_save.assert_called_once()
                # Verify output path passed correctly
                call_args = mock_save.call_args[0]
                assert call_args[1] == output