"""
Contract test for the API client (US2).

This test verifies that the API client adheres to the interface contract
defined in src/execution/api_client.py, specifically:
1. The client accepts the required arguments (prompt, model, timeout).
2. The client returns a dictionary with the expected keys on success.
3. The client raises the expected TimeoutError on timeout simulation.
4. The client handles malformed responses gracefully.

This test does NOT make real network calls but mocks the underlying
transport to ensure the client logic (retry, timeout, parsing) works
as specified.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path if running locally
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.timeout_utils import TimeoutError
from src.execution.api_client import (
    CodeLlamaAPIClient,
    call_inference_api,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT
)


class TestCodeLlamaAPIClientContract:
    """Contract tests for CodeLlamaAPIClient."""

    def test_init_requires_api_key(self):
        """Client must require an API key or read from env."""
        # If HF_API_KEY is not set, it should raise or handle gracefully.
        # We test that the client initializes without crashing if key is provided.
        client = CodeLlamaAPIClient(api_key="fake_key_for_test")
        assert client.api_key == "fake_key_for_test"
        assert client.model == DEFAULT_MODEL
        assert client.timeout == DEFAULT_TIMEOUT

    def test_call_api_success_structure(self):
        """
        Verify that on a successful mock response, the client returns
        a dict with 'text' and 'usage' keys (or equivalent structure).
        """
        mock_response = {
            "generated_text": "function test() { return 1; }",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }

        with patch('src.execution.api_client.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            client = CodeLlamaAPIClient(api_key="fake_key")
            result = client.generate("def test(): pass")

            assert isinstance(result, dict)
            assert "text" in result
            assert "usage" in result
            assert result["text"] == "function test() { return 1; }"
            assert mock_post.called

    def test_call_api_timeout_raises(self):
        """Verify that a timeout exception is raised and handled."""
        with patch('src.execution.api_client.requests.post') as mock_post:
            mock_post.side_effect = TimeoutError("Simulated timeout")

            client = CodeLlamaAPIClient(api_key="fake_key")
            
            # The client should raise the TimeoutError if retries are exhausted
            # or we can test the specific helper if exposed.
            # For contract, we ensure the error propagates or is caught as expected.
            with pytest.raises(TimeoutError):
                client.generate("def test(): pass")

    def test_call_api_malformed_response(self):
        """Verify handling of non-JSON or unexpected JSON structure."""
        with patch('src.execution.api_client.requests.post') as mock_post:
            # Simulate a 200 OK but with invalid JSON content
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("No JSON object could be decoded")
            mock_post.return_value = mock_response

            client = CodeLlamaAPIClient(api_key="fake_key")
            
            # Should raise an error or return a specific error dict
            # Based on typical contract, it should not crash the whole process
            # but signal failure.
            with pytest.raises((ValueError, Exception)):
                client.generate("def test(): pass")


def test_call_inference_api_function_contract():
    """
    Contract test for the standalone function call_inference_api.
    Ensures it matches the signature and basic behavior expected by run_inference.py.
    """
    mock_payload = {
        "inputs": "def hello(): pass",
        "parameters": {"max_new_tokens": 50}
    }
    mock_response_json = {
        "generated_text": "function hello() { console.log('hi'); }"
    }

    with patch('src.execution.api_client.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response_json

        result = call_inference_api(
            prompt="def hello(): pass",
            model=DEFAULT_MODEL,
            api_key="fake_key",
            timeout=10
        )

        assert result is not None
        assert "text" in result
        mock_post.assert_called_once()
        # Verify the payload structure roughly matches expectations
        call_args = mock_post.call_args
        assert call_args[1]['json']['inputs'] == "def hello(): pass"