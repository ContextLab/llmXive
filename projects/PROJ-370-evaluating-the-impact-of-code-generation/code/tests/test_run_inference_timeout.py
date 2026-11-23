import pytest
import json
import time
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import threading

from code.src.inference.run_inference import process_single_pr, parse_llm_output, run_batch_inference
from code.src.inference.schema import InferenceStatus

class TestRunInferenceTimeout:
    @pytest.fixture
    def mock_pr_data(self):
        return {
            "pr_id": "test-123",
            "file_path": "test.py",
            "diff": "def hello():\n    print('world')"
        }

    @pytest.fixture
    def mock_model(self):
        model = MagicMock()
        model.device = "cpu"
        return model

    @pytest.fixture
    def mock_tokenizer(self):
        tokenizer = MagicMock()
        tokenizer.eos_token_id = 0
        tokenizer.return_value = {"input_ids": [[1, 2, 3]]}
        return tokenizer

    @patch("code.src.inference.run_inference.get_bug_detection_prompt")
    @patch("code.src.inference.run_inference.create_inference_request")
    def test_process_single_pr_timeout(self, mock_create_req, mock_get_prompt, mock_pr_data, mock_model, mock_tokenizer):
        """Test that process_single_pr returns TIMEOUT status when inference takes too long."""
        mock_get_prompt.return_value = "Prompt"
        mock_create_req.return_value = {"prompt": "Prompt"}
        
        # Mock tokenizer.generate to block indefinitely
        mock_tokenizer.generate = MagicMock(side_effect=lambda **kwargs: time.sleep(100))
        
        # We need to mock the threading behavior to simulate timeout without actually waiting
        # Instead, we patch the thread join to return immediately but keep thread alive
        with patch("threading.Thread") as MockThread:
            mock_thread_instance = MagicMock()
            mock_thread_instance.is_alive.return_value = True # Simulate still running
            mock_thread_instance.start = MagicMock()
            mock_thread_instance.join = MagicMock() # Default join waits, but we mock the instance
            MockThread.return_value = mock_thread_instance

            response = process_single_pr(mock_pr_data, mock_model, mock_tokenizer, timeout_seconds=1, memory_limit_gb=7.0)
            
            assert response.status == InferenceStatus.TIMEOUT
            assert "timeout" in response.error_message.lower()

    @patch("code.src.inference.run_inference.get_bug_detection_prompt")
    @patch("code.src.inference.run_inference.create_inference_request")
    def test_process_single_pr_success(self, mock_create_req, mock_get_prompt, mock_pr_data, mock_model, mock_tokenizer):
        """Test successful processing within timeout."""
        mock_get_prompt.return_value = "Prompt"
        mock_create_req.return_value = {"prompt": "Prompt"}
        
        # Mock a fast completion
        mock_tokenizer.decode = MagicMock(return_value='{"detections": [{"severity": "major", "line_start": 1, "line_end": 1}]}')
        mock_tokenizer.generate = MagicMock(return_value=[[1, 2, 3]])
        
        with patch("threading.Thread") as MockThread:
            mock_thread_instance = MagicMock()
            mock_thread_instance.is_alive.return_value = False
            mock_thread_instance.start = MagicMock()
            mock_thread_instance.join = MagicMock()
            MockThread.return_value = mock_thread_instance
            
            response = process_single_pr(mock_pr_data, mock_model, mock_tokenizer, timeout_seconds=5, memory_limit_gb=7.0)
            
            assert response.status == InferenceStatus.SUCCESS
            assert len(response.detections) == 1

    def test_parse_llm_output_json(self):
        """Test parsing valid JSON output."""
        output = '{"detections": [{"severity": "major", "line_start": 1, "line_end": 2}]}'
        result = parse_llm_output(output)
        assert result is not None
        assert "detections" in result

    def test_parse_llm_output_markdown(self):
        """Test parsing JSON inside markdown blocks."""
        output = "```json\n{\"detections\": []}\n```"
        result = parse_llm_output(output)
        assert result is not None
        assert result == {"detections": []}

    def test_parse_llm_output_invalid(self):
        """Test parsing invalid JSON returns None."""
        output = "This is not JSON"
        result = parse_llm_output(output)
        assert result is None