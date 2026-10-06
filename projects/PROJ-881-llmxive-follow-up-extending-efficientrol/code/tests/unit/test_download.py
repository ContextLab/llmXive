"""
Unit tests for the download module.

Tests verify:
- Streaming logic with islice
- No synthetic fallback behavior
- Error handling for failed downloads
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.download import (
    download_gsm8k_subset,
    download_minigrid_subset,
    download_all_datasets,
    DEFAULT_MAX_SAMPLES
)

class TestDownloadModule:
    """Test suite for download module."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def mock_huggingface_dataset(self):
        """Create a mock HuggingFace dataset iterator."""
        def create_mock_examples(count=10):
            examples = []
            for i in range(count):
                examples.append({
                    "id": f"test_{i}",
                    "question": f"Test question {i}",
                    "answer": f"Test answer {i}"
                })
            return iter(examples)
        return create_mock_examples
    
    def test_download_gsm8k_capping(self, temp_dir, mock_huggingface_dataset):
        """Test that GSM8K download respects max_samples cap."""
        # Create mock dataset iterator
        mock_examples = list(mock_huggingface_dataset(1000))
        mock_iter = iter(mock_examples)
        
        with patch('src.data.download.load_dataset') as mock_load:
            # Mock the load_dataset to return our iterator
            mock_load.return_value = mock_iter
            
            output_path = temp_dir / "gsm8k_test.jsonl"
            max_samples = 50
            
            result_path = download_gsm8k_subset(output_path, max_samples)
            
            # Verify the file was created
            assert result_path.exists()
            
            # Verify only max_samples were written
            with open(result_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == max_samples, f"Expected {max_samples} lines, got {len(lines)}"
            
            # Verify the content matches expected examples
            for i, line in enumerate(lines):
                data = json.loads(line)
                assert data['id'] == f"test_{i}"
    
    def test_download_minigrid_capping(self, temp_dir, mock_huggingface_dataset):
        """Test that MiniGrid download respects max_samples cap."""
        # Create mock dataset iterator
        mock_examples = list(mock_huggingface_dataset(1000))
        mock_iter = iter(mock_examples)
        
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.return_value = mock_iter
            
            output_path = temp_dir / "minigrid_test.jsonl"
            max_samples = 75
            
            result_path = download_minigrid_subset(output_path, max_samples)
            
            # Verify the file was created
            assert result_path.exists()
            
            # Verify only max_samples were written
            with open(result_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == max_samples
    
    def test_download_fails_loudly_no_synthetic_fallback(self, temp_dir):
        """Test that download raises error on failure without synthetic fallback."""
        with patch('src.data.download.load_dataset') as mock_load:
            # Simulate a connection error
            mock_load.side_effect = ConnectionError("Network unavailable")
            
            output_path = temp_dir / "gsm8k_fail.jsonl"
            
            with pytest.raises(ConnectionError) as exc_info:
                download_gsm8k_subset(output_path, 50)
            
            # Verify the error message indicates real data fetch failure
            assert "real data fetch failure" in str(exc_info.value).lower()
            
            # Verify no file was created (no synthetic fallback)
            assert not output_path.exists()
    
    def test_default_max_samples(self):
        """Test that DEFAULT_MAX_SAMPLES is set to 500."""
        assert DEFAULT_MAX_SAMPLES == 500, "Default max samples should be 500 per FR-001"
    
    def test_download_all_datasets(self, temp_dir, mock_huggingface_dataset):
        """Test downloading both datasets."""
        mock_examples = list(mock_huggingface_dataset(100))
        mock_iter = iter(mock_examples)
        
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.return_value = mock_iter
            
            gsm8k_path = temp_dir / "gsm8k_all.jsonl"
            minigrid_path = temp_dir / "minigrid_all.jsonl"
            
            results = download_all_datasets(
                gsm8k_path=gsm8k_path,
                minigrid_path=minigrid_path,
                max_samples=25
            )
            
            # Verify both files were created
            assert 'gsm8k' in results
            assert 'minigrid' in results
            assert results['gsm8k'].exists()
            assert results['minigrid'].exists()
            
            # Verify both have correct sample counts
            with open(results['gsm8k'], 'r') as f:
                assert len(f.readlines()) == 25
            
            with open(results['minigrid'], 'r') as f:
                assert len(f.readlines()) == 25
    
    def test_streaming_logic_with_islice(self, temp_dir, mock_huggingface_dataset):
        """Test that streaming uses islice correctly."""
        # Create a larger mock dataset
        mock_examples = list(mock_huggingface_dataset(10000))
        mock_iter = iter(mock_examples)
        
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.return_value = mock_iter
            
            output_path = temp_dir / "streaming_test.jsonl"
            max_samples = 100
            
            result_path = download_gsm8k_subset(output_path, max_samples)
            
            # Verify the file exists
            assert result_path.exists()
            
            # Verify we got exactly max_samples
            with open(result_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == max_samples
            
            # Verify the first and last samples are correct
            first_data = json.loads(lines[0])
            last_data = json.loads(lines[-1])
            
            assert first_data['id'] == 'test_0'
            assert last_data['id'] == f'test_{max_samples - 1}'
    
    def test_empty_dataset_handling(self, temp_dir):
        """Test handling of empty dataset."""
        mock_iter = iter([])  # Empty iterator
        
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.return_value = mock_iter
            
            output_path = temp_dir / "empty_test.jsonl"
            
            result_path = download_gsm8k_subset(output_path, 50)
            
            # Verify file was created but is empty
            assert result_path.exists()
            assert result_path.stat().st_size == 0
    
    def test_partial_dataset_handling(self, temp_dir, mock_huggingface_dataset):
        """Test handling when dataset has fewer examples than requested."""
        mock_examples = list(mock_huggingface_dataset(10))
        mock_iter = iter(mock_examples)
        
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.return_value = mock_iter
            
            output_path = temp_dir / "partial_test.jsonl"
            max_samples = 100  # Request more than available
            
            result_path = download_gsm8k_subset(output_path, max_samples)
            
            # Verify file was created with available examples
            assert result_path.exists()
            
            with open(result_path, 'r') as f:
                lines = f.readlines()
            
            # Should have all 10 examples, not 100
            assert len(lines) == 10
    
    def test_jsonl_format(self, temp_dir, mock_huggingface_dataset):
        """Test that output is valid JSONL format."""
        mock_examples = list(mock_huggingface_dataset(5))
        mock_iter = iter(mock_examples)
        
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.return_value = mock_iter
            
            output_path = temp_dir / "format_test.jsonl"
            
            download_gsm8k_subset(output_path, 5)
            
            # Verify each line is valid JSON
            with open(output_path, 'r') as f:
                for line in f:
                    # Should not raise JSONDecodeError
                    json.loads(line)
    
    def test_directory_creation(self, temp_dir, mock_huggingface_dataset):
        """Test that output directory is created if it doesn't exist."""
        mock_examples = list(mock_huggingface_dataset(5))
        mock_iter = iter(mock_examples)
        
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.return_value = mock_iter
            
            # Use a nested path that doesn't exist
            output_path = temp_dir / "nested" / "deep" / "gsm8k.jsonl"
            
            result_path = download_gsm8k_subset(output_path, 5)
            
            # Verify the directory was created
            assert output_path.parent.exists()
            assert result_path.exists()
    
    def test_custom_max_samples_parameter(self, temp_dir, mock_huggingface_dataset):
        """Test that custom max_samples parameter is respected."""
        mock_examples = list(mock_huggingface_dataset(500))
        mock_iter = iter(mock_examples)
        
        with patch('src.data.download.load_dataset') as mock_load:
            mock_load.return_value = mock_iter
            
            output_path = temp_dir / "custom_test.jsonl"
            
            # Test various custom values
            for custom_count in [10, 50, 100, 250]:
                result_path = download_gsm8k_subset(output_path, custom_count)
                
                with open(result_path, 'r') as f:
                    lines = f.readlines()
                
                assert len(lines) == custom_count, f"Expected {custom_count}, got {len(lines)}"
    
    def test_error_on_import_failure(self, temp_dir):
        """Test that ImportError is raised if datasets package is missing."""
        with patch.dict(sys.modules, {'datasets': None}):
            with patch('src.data.download.load_dataset') as mock_load:
                # Simulate ImportError
                mock_load.side_effect = ImportError("datasets not found")
                
                output_path = temp_dir / "import_error.jsonl"
                
                with pytest.raises(ImportError):
                    download_gsm8k_subset(output_path, 50)