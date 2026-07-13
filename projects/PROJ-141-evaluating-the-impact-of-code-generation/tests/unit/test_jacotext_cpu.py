"""
Unit tests for JaCoText CPU verification logic.
"""
import unittest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Adjust path to import the module
sys_path = Path(__file__).resolve().parent.parent.parent
if str(sys_path) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(sys_path))

from models.jacotext_cpu import get_model_size_mb, verify_cpu_tractability

class TestJaCoTextVerification(unittest.TestCase):

    @patch('models.jacotext_cpu.HfApi')
    def test_get_model_size_mb_success(self, mock_hf_api):
        """Test successful size retrieval"""
        mock_info = MagicMock()
        mock_info.siblings = [MagicMock(size=1000000), MagicMock(size=2000000)]
        mock_hf_api.return_value.model_info.return_value = mock_info

        size = get_model_size_mb("test/model")
        
        self.assertAlmostEqual(size, 2.86, places=2)

    @patch('models.jacotext_cpu.HfApi')
    def test_get_model_size_mb_error(self, mock_hf_api):
        """Test error handling in size retrieval"""
        mock_hf_api.return_value.model_info.side_effect = Exception("Network error")
        
        size = get_model_size_mb("test/model")
        self.assertIsNone(size)

    def test_verify_cpu_tractability_mocked(self):
        """Test the verification flow with mocked transformers"""
        # We cannot easily mock the full model loading without heavy mocking.
        # Instead, we verify the logic path for size > 1GB
        with patch('models.jacotext_cpu.get_model_size_mb', return_value=2000.0):
            result = verify_cpu_tractability("fake/model")
            self.assertEqual(result["status"], "failed_size_limit")
            self.assertIn("exceeds 1GB", result["error"])

    def test_verify_cpu_tractability_success_mocked(self):
        """Test success path with mocked model loading"""
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_model.parameters.return_value = [MagicMock(numel=100)] # Fake params
        
        with patch('models.jacotext_cpu.AutoTokenizer.from_pretrained', return_value=mock_tokenizer):
            with patch('models.jacotext_cpu.AutoModelForCausalLM.from_pretrained', return_value=mock_model):
                with patch('models.jacotext_cpu.get_model_size_mb', return_value=500.0):
                    result = verify_cpu_tractability("fake/model")
                    self.assertEqual(result["status"], "success")
                    self.assertIsNotNone(result["inference_time_sec"])

if __name__ == '__main__':
    unittest.main()
