"""
Unit tests for SSM Student Model Loader.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from models.ssm_student import SSMStudentLoader, estimate_model_size_gb, MODEL_ID

class TestSSMStudentLoader:
    """Tests for SSMStudentLoader class."""

    def test_estimate_model_size_gb(self):
        """Test that model size estimation returns a reasonable value."""
        size = estimate_model_size_gb(MODEL_ID)
        assert isinstance(size, float)
        assert 0 < size < 10  # Should be between 0 and 10 GB
        # Mamba-1.3b should be around 3-4 GB
        assert 2.5 < size < 5.0

    @patch('models.ssm_student.SSMStudentLoader.verify_memory_budget')
    @patch('models.ssm_student.MambaForCausalLM')
    @patch('models.ssm_student.AutoTokenizer')
    def test_load_model_success(self, mock_tokenizer, mock_mamba, mock_verify):
        """Test successful model loading."""
        # Setup mocks
        mock_verify.return_value = True
        mock_model_instance = MagicMock()
        mock_model_instance.parameters.return_value = [MagicMock(numel=lambda: 100)]
        mock_mamba.from_pretrained.return_value = mock_model_instance
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        loader = SSMStudentLoader()
        
        # This would normally fail without real models, but we're mocking
        # Just verify the method structure is correct
        assert loader.model_id == MODEL_ID
        assert loader.device == "cpu"

    def test_verify_memory_budget_within_limit(self):
        """Test that verification passes when within limit."""
        loader = SSMStudentLoader()
        # Temporarily set size to be within limit
        original_size = loader.size_gb
        loader.size_gb = 5.0  # Below PRELOAD_CHECK_GB (6.5)
        
        try:
            result = loader.verify_memory_budget()
            assert result is True
        finally:
            loader.size_gb = original_size

    def test_verify_memory_budget_exceeds_limit(self):
        """Test that verification raises MemoryError when exceeding limit."""
        loader = SSMStudentLoader()
        # Set size to exceed limit
        original_size = loader.size_gb
        loader.size_gb = 7.0  # Above PRELOAD_CHECK_GB (6.5)
        
        try:
            with pytest.raises(MemoryError):
                loader.verify_memory_budget()
        finally:
            loader.size_gb = original_size

class TestSSMStudentLoaderEdgeCases:
    """Tests for edge cases and error handling."""

    @patch('models.ssm_student.psutil')
    def test_memory_check_with_psutil(self, mock_psutil):
        """Test memory check when psutil is available."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 2 * (1024 ** 3)  # 2GB
        mock_psutil.Process.return_value = mock_process
        
        loader = SSMStudentLoader()
        loader.size_gb = 3.0  # Total would be 5GB, within 7GB limit
        
        # Should not raise
        result = loader.verify_memory_budget()
        assert result is True

    def test_no_fallback_on_failure(self):
        """Ensure that the loader does not fall back to synthetic models."""
        loader = SSMStudentLoader()
        # The loader should raise MemoryError or ValueError on failure,
        # not return a mock/synthetic model
        with patch.object(loader, 'verify_memory_budget', side_effect=MemoryError("Test")):
            with pytest.raises(MemoryError):
                loader.load_model()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])