import pytest
from src.lib.validator import validate_dataset_size, ValidationError
from unittest.mock import MagicMock
from typing import List, Dict, Any


class TestValidator:
    """Tests for dataset size validation logic."""

    def test_validate_dataset_size_passes_above_threshold(self):
        """Test that validation passes when dataset size >= 30."""
        # Create a mock iterator with 30 items
        mock_data = [{"id": i} for i in range(30)]
        mock_iterator = iter(mock_data)
        
        # Should not raise
        count = validate_dataset_size(mock_iterator)
        assert count == 30

    def test_validate_dataset_size_passes_above_threshold_large(self):
        """Test that validation passes for large datasets."""
        mock_data = [{"id": i} for i in range(1000)]
        mock_iterator = iter(mock_data)
        
        count = validate_dataset_size(mock_iterator)
        assert count == 1000

    def test_validate_dataset_size_fails_below_threshold(self):
        """Test that validation fails when dataset size < 30."""
        mock_data = [{"id": i} for i in range(29)]
        mock_iterator = iter(mock_data)
        
        with pytest.raises(ValidationError) as exc_info:
            validate_dataset_size(mock_iterator)
        
        assert "Insufficient Sample Size" in str(exc_info.value)
        assert "29" in str(exc_info.value)
        assert "30" in str(exc_info.value)

    def test_validate_dataset_size_exact_threshold(self):
        """Test that validation passes exactly at threshold (N=30)."""
        mock_data = [{"id": i} for i in range(30)]
        mock_iterator = iter(mock_data)
        
        count = validate_dataset_size(mock_iterator)
        assert count == 30

    def test_validate_dataset_size_empty_dataset(self):
        """Test that validation fails for empty dataset."""
        mock_iterator = iter([])
        
        with pytest.raises(ValidationError) as exc_info:
            validate_dataset_size(mock_iterator)
        
        assert "Insufficient Sample Size" in str(exc_info.value)
        assert "0" in str(exc_info.value)

    def test_validate_dataset_size_consumes_iterator(self):
        """Test that the validator consumes the entire iterator."""
        consumed_count = 0
        
        def counting_iterator():
            nonlocal consumed_count
            for i in range(25):
                consumed_count += 1
                yield {"id": i}
        
        mock_iterator = counting_iterator()
        
        with pytest.raises(ValidationError):
            validate_dataset_size(mock_iterator)
        
        # Verify all items were consumed
        assert consumed_count == 25
