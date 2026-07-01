"""
Unit tests for verify_models.py
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.research.verify_models import get_model_size_mb, verify_models, MODEL_SIZE_THRESHOLD_GB

class TestGetModelSizeMb:
    @patch('src.research.verify_models.HfApi')
    def test_returns_size_mb(self, mock_hf_api):
        # Mock the API response
        mock_instance = MagicMock()
        mock_hf_api.return_value = mock_instance
        
        mock_info = MagicMock()
        mock_sibling = MagicMock()
        mock_sibling.size = 104857600  # 100 MB in bytes
        mock_info.siblings = [mock_sibling]
        mock_instance.model_info.return_value = mock_info
        
        size = get_model_size_mb("fake/model")
        
        assert size == 100.0  # 100 MB
        mock_instance.model_info.assert_called_once_with("fake/model")

    @patch('src.research.verify_models.HfApi')
    def test_returns_none_on_error(self, mock_hf_api):
        mock_instance = MagicMock()
        mock_hf_api.return_value = mock_instance
        mock_instance.model_info.side_effect = Exception("Connection error")
        
        size = get_model_size_mb("fake/model")
        
        assert size is None

class TestVerifyModels:
    def test_verify_models_structure(self):
        # This test checks the structure of the output, not the actual network call
        # We mock the get_model_size_mb function to avoid network calls
        with patch('src.research.verify_models.get_model_size_mb') as mock_size:
            mock_size.return_value = 500.0  # 500 MB
            
            results = verify_models()
            
            assert isinstance(results, list)
            assert len(results) > 0
            
            for res in results:
                assert "model_name" in res
                assert "hf_id" in res
                assert "size_mb" in res
                assert "cpu_tractable" in res
                assert "status" in res
                
                # Check logic
                if res["size_mb"] is not None:
                    expected_tractable = res["size_mb"] < (MODEL_SIZE_THRESHOLD_GB * 1024)
                    assert res["cpu_tractable"] == expected_tractable

class TestModelThreshold:
    def test_threshold_is_1gb(self):
        # 1 GB in MB is 1024
        assert MODEL_SIZE_THRESHOLD_GB == 1.0