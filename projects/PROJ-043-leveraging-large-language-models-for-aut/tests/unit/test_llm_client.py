import pytest
import time
import logging
from unittest.mock import patch, MagicMock, Mock
from requests.exceptions import Timeout, RequestException
from pathlib import Path
import sys
import os

# Adjust path to include project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.llm.refactoring import refactor_single_function
from code.config import Config
from code.utils.logging import LLMRefactoringError, get_logger

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = get_logger("test_llm_client")

class TestRetryLogic:
    """Unit tests for API retry logic and timeout handling."""

    def test_retry_logic_exponential_backoff(self):
        """
        Assert that retries occur with increasing delays (exponential backoff)
        and timeout is enforced per the spec.
        """
        # Mock the requests.post to simulate repeated failures
        with patch('code.llm.refactoring.requests.post') as mock_post:
            # Simulate 3 timeouts followed by a success
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"generated_text": "refactored_code"}

            # Configure side_effect to raise Timeout 3 times, then return success
            mock_post.side_effect = [
                Timeout("Request timed out"),
                Timeout("Request timed out"),
                Timeout("Request timed out"),
                mock_response_success
            ]

            # Mock time.sleep to avoid actual waiting during test
            with patch('code.llm.refactoring.time.sleep') as mock_sleep:
                # Mock time.time to track elapsed time if needed, though we check sleep calls
                original_time = time.time
                time_values = [0.0, 1.0, 4.0, 9.0] # Simulated time progression
                with patch('code.llm.refactoring.time.time', side_effect=time_values):
                    
                    config = Config(
                        HF_API_KEY="test_key",
                        RANDOM_SEED=42,
                        MAX_ATTEMPTS=5,
                        MIN_VALID_FUNCTIONS=100,
                        TARGET_VALID_FUNCTIONS=200,
                        BATCH_SIZE=10,
                        BASELINE_TOLERANCE=0.01
                    )

                    # Call the function with a small timeout to ensure it triggers quickly
                    # Note: refactor_single_function expects a function sample dict
                    sample_code = "def dummy(): pass"
                    function_hash = "abc123"
                    
                    # We need to patch the specific API call logic inside refactor_single_function
                    # Since we are testing the retry logic, we assume the function calls requests.post
                    
                    try:
                        result = refactor_single_function(
                            code=sample_code,
                            function_hash=function_hash,
                            config=config
                        )
                    except LLMRefactoringError:
                        # If it fails after max retries, that's also a valid path if we hit limits
                        # But here we set it to succeed on 4th attempt
                        pass

                    # Verify that sleep was called with increasing delays (1, 2, 4 seconds typically)
                    # The exact backoff strategy (1, 2, 4 or 2, 4, 8) depends on implementation
                    # We assert that sleep was called at least 3 times
                    assert mock_sleep.call_count == 3, f"Expected 3 sleep calls for 3 retries, got {mock_sleep.call_count}"
                    
                    # Verify the delays are increasing (Exponential Backoff)
                    # We check the arguments passed to sleep
                    sleep_delays = [call[0][0] for call in mock_sleep.call_args_list]
                    assert all(sleep_delays[i] <= sleep_delays[i+1] for i in range(len(sleep_delays)-1)), \
                        "Delays should be non-decreasing for exponential backoff"
                    
                    # Verify that requests.post was called 4 times (3 failures + 1 success)
                    assert mock_post.call_count == 4, f"Expected 4 API calls (3 retries + 1 success), got {mock_post.call_count}"

    def test_timeout_enforcement(self):
        """
        Assert that a timeout exception is raised and handled correctly
        when the API does not respond within the specified time.
        """
        with patch('code.llm.refactoring.requests.post') as mock_post:
            # Simulate a persistent timeout
            mock_post.side_effect = Timeout("Connection timed out")

            config = Config(
                HF_API_KEY="test_key",
                RANDOM_SEED=42,
                MAX_ATTEMPTS=2, # Limit retries for this test
                MIN_VALID_FUNCTIONS=100,
                TARGET_VALID_FUNCTIONS=200,
                BATCH_SIZE=10,
                BASELINE_TOLERANCE=0.01
            )

            sample_code = "def dummy(): pass"
            function_hash = "def123"

            # We expect the function to eventually raise an error after exhausting retries
            with patch('code.llm.refactoring.time.sleep'):
                with pytest.raises(LLMRefactoringError) as exc_info:
                    refactor_single_function(
                        code=sample_code,
                        function_hash=function_hash,
                        config=config
                    )
                
                assert "Max retries exceeded" in str(exc_info.value) or "Timeout" in str(exc_info.value)
                assert mock_post.call_count == 2 # Initial + 1 retry (MAX_ATTEMPTS=2)

    def test_request_exception_handling(self):
        """
        Assert that generic RequestExceptions are handled with exponential backoff.
        """
        with patch('code.llm.refactoring.requests.post') as mock_post:
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"generated_text": "code"}

            # Mix of RequestExceptions
            mock_post.side_effect = [
                RequestException("Network error"),
                RequestException("Server error"),
                mock_response_success
            ]

            with patch('code.llm.refactoring.time.sleep') as mock_sleep:
                config = Config(
                    HF_API_KEY="test_key",
                    RANDOM_SEED=42,
                    MAX_ATTEMPTS=5,
                    MIN_VALID_FUNCTIONS=100,
                    TARGET_VALID_FUNCTIONS=200,
                    BATCH_SIZE=10,
                    BASELINE_TOLERANCE=0.01
                )

                try:
                    refactor_single_function(
                        code="def x(): pass",
                        function_hash="hash_xyz",
                        config=config
                    )
                except LLMRefactoringError:
                    pass # Should succeed eventually

                assert mock_sleep.call_count == 2
                assert mock_post.call_count == 3

    def test_success_without_retry(self):
        """
        Assert that if the first attempt succeeds, no retries or sleeps occur.
        """
        with patch('code.llm.refactoring.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"generated_text": "success"}
            mock_post.return_value = mock_response

            with patch('code.llm.refactoring.time.sleep') as mock_sleep:
                config = Config(
                    HF_API_KEY="test_key",
                    RANDOM_SEED=42,
                    MAX_ATTEMPTS=5,
                    MIN_VALID_FUNCTIONS=100,
                    TARGET_VALID_FUNCTIONS=200,
                    BATCH_SIZE=10,
                    BASELINE_TOLERANCE=0.01
                )

                refactor_single_function(
                    code="def y(): pass",
                    function_hash="hash_abc",
                    config=config
                )

                assert mock_sleep.call_count == 0
                assert mock_post.call_count == 1