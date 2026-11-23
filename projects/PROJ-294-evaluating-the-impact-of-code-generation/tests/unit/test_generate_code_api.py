import os
import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import json
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, 'code')
from generate_code import generate_code_via_hf_api, mark_sample_missing, generate_code_batch

class TestHuggingFaceAPISensitivity(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mock_prompt = "def add(a, b):\n    return a + b"
        self.mock_model_id = "codellama/CodeLlama-7b-hf"
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('generate_code.requests.post')
    def test_generate_code_via_hf_api_success(self, mock_post):
        """Test successful API call returns generated text."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": "return a + b"}]
        mock_post.return_value = mock_response
        
        result = generate_code_via_hf_api(
            self.mock_prompt,
            self.mock_model_id,
            api_token="fake_token"
        )
        
        self.assertEqual(result, "return a + b")
        mock_post.assert_called_once()
    
    @patch('generate_code.requests.post')
    def test_generate_code_via_hf_api_model_loading(self, mock_post):
        """Test retry logic when model is loading (503)."""
        mock_response_503 = MagicMock()
        mock_response_503.status_code = 503
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = [{"generated_text": "success"}]
        
        mock_post.side_effect = [mock_response_503, mock_response_200]
        
        result = generate_code_via_hf_api(
            self.mock_prompt,
            self.mock_model_id,
            api_token="fake_token",
            max_retries=3
        )
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_post.call_count, 2)
    
    @patch('generate_code.requests.post')
    def test_generate_code_via_hf_api_failure(self, mock_post):
        """Test API call raises error after max retries."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        with self.assertRaises(RuntimeError):
            generate_code_via_hf_api(
                self.mock_prompt,
                self.mock_model_id,
                api_token="fake_token",
                max_retries=2
            )
    
    def test_mark_sample_missing(self):
        """Test missing record structure."""
        record = mark_sample_missing("task_001", "API timeout")
        self.assertEqual(record["task_id"], "task_001")
        self.assertEqual(record["status"], "missing")
        self.assertEqual(record["error_reason"], "API timeout")
        self.assertIsNone(record["generated_code"])
    
    @patch('generate_code.generate_code_via_hf_api')
    def test_generate_code_batch_with_api(self, mock_api_call):
        """Test batch generation using API."""
        mock_api_call.return_value = "generated code"
        
        tasks = [
            {"task_id": "task_001", "prompt": "prompt1"},
            {"task_id": "task_002", "prompt": "prompt2"}
        ]
        
        output_path = os.path.join(self.test_dir, "test_output.json")
        results = generate_code_batch(
            tasks,
            output_path=output_path,
            use_api_for_sensitivity=True,
            api_model_id=self.mock_model_id,
            hf_token="fake_token"
        )
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["source_model"], self.mock_model_id)
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(len(saved_data), 2)

if __name__ == "__main__":
    unittest.main()