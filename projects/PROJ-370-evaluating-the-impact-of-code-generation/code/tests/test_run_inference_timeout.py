import pytest
import json
import time
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from code.src.inference.run_inference import process_single_pr, parse_llm_output
from code.src.inference.schema import InferenceStatus
from code.src.utils.timeout_wrapper import TimeoutContext

class TestRunInferenceTimeout:
    """Tests for T023: Timeout enforcement in run_inference.py"""

    def test_parse_llm_output_valid_json(self):
        """Test parsing valid JSON output"""
        raw = '{"detections": [{"severity": "critical", "description": "test"}]}'
        result = parse_llm_output(raw, "test-pr-1")
        assert len(result["detections"]) == 1
        assert result["detections"][0]["severity"] == "critical"

    def test_parse_llm_output_markdown_block(self):
        """Test parsing JSON inside markdown code blocks"""
        raw = '```json\n{"detections": []}\n```'
        result = parse_llm_output(raw, "test-pr-2")
        assert "detections" in result

    def test_process_single_pr_timeout_simulation(self):
        """
        Simulate a timeout scenario.
        We mock the model.generate to take too long, triggering the timeout.
        """
        # Mock model and tokenizer
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.decode.return_value = "fake output"
        
        # Mock the tokenizer to return empty inputs for speed
        mock_tokenizer.return_value = {"input_ids": [[1, 2, 3]]}
        
        # Mock torch.no_grad
        with patch('code.src.inference.run_inference.torch') as mock_torch:
            mock_torch.no_grad.return_value.__enter__ = Mock()
            mock_torch.no_grad.return_value.__exit__ = Mock()
            
            # Mock the generate method to simulate a long-running process
            # We patch the TimeoutContext to immediately raise TimeoutError
            # to simulate the timeout logic firing
            with patch('code.src.inference.run_inference.TimeoutContext') as mock_ctx:
                mock_ctx_instance = MagicMock()
                mock_ctx_instance.__enter__ = Mock(side_effect=TimeoutError("Simulated timeout"))
                mock_ctx_instance.__exit__ = Mock(return_value=False)
                mock_ctx.return_value = mock_ctx_instance

                response = process_single_pr(
                    pr_data={"pr_id": "timeout-pr"},
                    model=mock_model,
                    tokenizer=mock_tokenizer,
                    timeout_seconds=1
                )

                assert response.status == InferenceStatus.TIMEOUT
                assert response.error_message is not None
                assert "timeout" in response.error_message.lower() or "simulated" in response.error_message.lower()

    def test_process_single_pr_success(self):
        """Test successful processing without timeout"""
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.decode.return_value = '{"detections": []}'
        mock_tokenizer.return_value = {"input_ids": [[1, 2, 3]]}
        
        with patch('code.src.inference.run_inference.torch') as mock_torch:
            mock_torch.no_grad.return_value.__enter__ = Mock()
            mock_torch.no_grad.return_value.__exit__ = Mock()
            
            # Mock the generate method to return a quick response
            mock_model.generate.return_value = [[1, 2, 3]]

            with patch('code.src.inference.run_inference.TimeoutContext') as mock_ctx:
                mock_ctx_instance = MagicMock()
                mock_ctx_instance.__enter__ = Mock(return_value=None)
                mock_ctx_instance.__exit__ = Mock(return_value=False)
                mock_ctx.return_value = mock_ctx_instance

                response = process_single_pr(
                    pr_data={"pr_id": "success-pr"},
                    model=mock_model,
                    tokenizer=mock_tokenizer,
                    timeout_seconds=300
                )

                assert response.status == InferenceStatus.SUCCESS
                assert response.latency_seconds >= 0
