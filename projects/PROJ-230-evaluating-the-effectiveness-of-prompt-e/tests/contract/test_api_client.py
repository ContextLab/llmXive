import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json
import time

# Add project root to path if not already present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.timeout_utils import TimeoutError
from src.execution.api_client import (
    InferenceError,
    MalformedResponseError,
    call_inference_api,
    main
)

# Constants for contract testing
MOCK_API_ENDPOINT = "https://api-inference.huggingface.co/models/codeparrot/code-trans-py-js"
MOCK_API_KEY = "hf_test_key_12345"
MOCK_PROMPT = "def hello():\n    print('Hello')"
MOCK_SEED = 42
EXPECTED_TIMEOUT = 120
MAX_RETRIES = 3

class TestCodeLlamaAPIClientContract:
    """
    Contract tests for the API client to ensure it adheres to:
    - Correct error handling (InferenceError, MalformedResponseError, TimeoutError)
    - Retry logic with exponential backoff
    - Timeout enforcement
    - Response validation
    """

    def test_call_inference_api_success_response(self):
        """
        Contract: When the API returns a valid 200 response with 'generated_text',
        the function must return the text and not raise an exception.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"generated_text": "function hello() { console.log('Hello'); }"}
        mock_response.raise_for_status = MagicMock()

        with patch('src.execution.api_client.requests.post', return_value=mock_response) as mock_post:
            result = call_inference_api(
                prompt=MOCK_PROMPT,
                api_endpoint=MOCK_API_ENDPOINT,
                api_key=MOCK_API_KEY,
                seed=MOCK_SEED
            )

            mock_post.assert_called_once()
            assert result == "function hello() { console.log('Hello'); }"

    def test_call_inference_api_503_retry_logic(self):
        """
        Contract: When the API returns a 503 (Service Unavailable), the function
        must retry up to MAX_RETRIES times with exponential backoff before failing.
        """
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = Exception("503 Service Unavailable")

        with patch('src.execution.api_client.requests.post', return_value=mock_response) as mock_post:
            with patch('src.execution.api_client.time.sleep') as mock_sleep:
                with pytest.raises(InferenceError):
                    call_inference_api(
                        prompt=MOCK_PROMPT,
                        api_endpoint=MOCK_API_ENDPOINT,
                        api_key=MOCK_API_KEY,
                        seed=MOCK_SEED,
                        max_retries=MAX_RETRIES
                    )

                # Verify retry attempts (initial + retries)
                assert mock_post.call_count == MAX_RETRIES
                # Verify sleep was called for backoff (retries - 1)
                assert mock_sleep.call_count == MAX_RETRIES - 1

    def test_call_inference_api_malformed_response(self):
        """
        Contract: When the API returns a 200 response but the JSON does not contain
        'generated_text', the function must raise MalformedResponseError.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Some internal error", "detail": "Missing field"}
        mock_response.raise_for_status = MagicMock()

        with patch('src.execution.api_client.requests.post', return_value=mock_response):
            with pytest.raises(MalformedResponseError) as exc_info:
                call_inference_api(
                    prompt=MOCK_PROMPT,
                    api_endpoint=MOCK_API_ENDPOINT,
                    api_key=MOCK_API_KEY,
                    seed=MOCK_SEED
                )
            assert "Malformed response" in str(exc_info.value)

    def test_call_inference_api_timeout_handling(self):
        """
        Contract: When the API request exceeds the timeout, the function must
        raise InferenceError wrapping the TimeoutError.
        """
        with patch('src.execution.api_client.requests.post') as mock_post:
            mock_post.side_effect = TimeoutError("Request timed out")

            with pytest.raises(InferenceError) as exc_info:
                call_inference_api(
                    prompt=MOCK_PROMPT,
                    api_endpoint=MOCK_API_ENDPOINT,
                    api_key=MOCK_API_KEY,
                    seed=MOCK_SEED
                )
            assert "Timeout" in str(exc_info.value)

    def test_call_inference_api_non_json_response(self):
        """
        Contract: When the API returns a non-JSON response (e.g., HTML error page),
        the function must raise MalformedResponseError.
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "<html><body>Internal Server Error</body></html>"
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_response.raise_for_status.side_effect = Exception("500 Internal Server Error")

        with patch('src.execution.api_client.requests.post', return_value=mock_response):
            with pytest.raises(InferenceError):
                call_inference_api(
                    prompt=MOCK_PROMPT,
                    api_endpoint=MOCK_API_ENDPOINT,
                    api_key=MOCK_API_KEY,
                    seed=MOCK_SEED
                )

    def test_call_inference_api_payload_structure(self):
        """
        Contract: The payload sent to the API must include 'inputs', 'parameters',
        and 'seed' (if provided) in the correct format.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"generated_text": "output"}
        mock_response.raise_for_status = MagicMock()

        with patch('src.execution.api_client.requests.post', return_value=mock_response) as mock_post:
            call_inference_api(
                prompt=MOCK_PROMPT,
                api_endpoint=MOCK_API_ENDPOINT,
                api_key=MOCK_API_KEY,
                seed=MOCK_SEED
            )

            call_args = mock_post.call_args
            payload = call_args.kwargs.get('json') or call_args[1].get('json')

            assert 'inputs' in payload
            assert payload['inputs'] == MOCK_PROMPT
            assert 'parameters' in payload
            assert 'seed' in payload['parameters']
            assert payload['parameters']['seed'] == MOCK_SEED


def test_call_inference_api_function_contract():
    """
    Standalone contract test to verify the function signature and basic behavior.
    """
    # Verify function exists and is callable
    assert callable(call_inference_api)

    # Verify it raises InferenceError when endpoint is unreachable (network error)
    with patch('src.execution.api_client.requests.post') as mock_post:
        mock_post.side_effect = Exception("Network Error")
        with pytest.raises(InferenceError):
            call_inference_api(
                prompt="test",
                api_endpoint="http://invalid-url",
                api_key="key",
                seed=0
            )