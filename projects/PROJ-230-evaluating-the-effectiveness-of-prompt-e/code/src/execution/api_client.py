"""
API Client for HuggingFace Inference API (CodeLlama-7B).
Implements exponential backoff, timeout enforcement, and error handling.
"""
import os
import time
import logging
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path

from src.utils.timeout_utils import run_with_api_timeout, TimeoutError as ProjectTimeoutError
from src.utils.logging import get_logger

# Configuration
API_URL = os.getenv(
    "HF_INFERENCE_URL",
    "https://api-inference.huggingface.co/models/codellama/CodeLlama-7b-Instruct-hf"
)
API_TOKEN = os.getenv("HF_API_TOKEN")
MAX_RETRIES = int(os.getenv("HF_MAX_RETRIES", "5"))
BASE_DELAY = float(os.getenv("HF_BASE_DELAY", "2.0"))
MAX_DELAY = float(os.getenv("HF_MAX_DELAY", "60.0"))
TIMEOUT_SECONDS = 120

logger = get_logger(__name__)


class InferenceError(Exception):
    """Custom exception for inference failures."""
    pass


class MalformedResponseError(InferenceError):
    """Raised when the API response structure is unexpected."""
    pass


def _calculate_backoff(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    # Add small jitter to prevent thundering herd
    jitter = delay * 0.1 * (time.time() % 1)
    return delay + jitter


def _handle_error_response(response: requests.Response, attempt: int) -> None:
    """Parse and log error from HTTP response."""
    try:
        error_data = response.json()
        error_msg = error_data.get("error", "Unknown error")
        detail = error_data.get("details", "")
    except ValueError:
        error_msg = response.text or "Unknown error"
        detail = ""

    logger.warning(
        f"API Error on attempt {attempt + 1}: {response.status_code} - {error_msg}. Details: {detail}"
    )

    if response.status_code == 429:
        raise InferenceError(f"Rate limited. Retry after {error_data.get('estimated_time', 60)}s")
    elif response.status_code >= 500:
        raise InferenceError(f"Server error ({response.status_code}): {error_msg}")
    else:
        raise InferenceError(f"Client error ({response.status_code}): {error_msg}")


def call_inference_api(
    prompt: str,
    model: str = "codellama/CodeLlama-7b-Instruct-hf",
    max_new_tokens: int = 512,
    temperature: float = 0.2,
    seed: Optional[int] = None,
    retry_attempts: int = MAX_RETRIES
) -> str:
    """
    Call the HuggingFace Inference API with exponential backoff and timeout.

    Args:
        prompt: The text prompt to send to the model.
        model: Model identifier on HuggingFace.
        max_new_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        seed: Random seed for determinism.
        retry_attempts: Number of retry attempts on failure.

    Returns:
        The generated text string.

    Raises:
        InferenceError: If all retries fail or a non-recoverable error occurs.
        MalformedResponseError: If the response JSON structure is invalid.
        TimeoutError: If the request exceeds the timeout limit.
    """
    if not API_TOKEN:
        raise InferenceError("HF_API_TOKEN environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "return_full_text": False,
            "do_sample": temperature > 0.0
        }
    }

    if seed is not None:
        payload["parameters"]["seed"] = seed

    last_error: Optional[Exception] = None

    for attempt in range(retry_attempts):
        try:
            logger.debug(f"Sending request to {API_URL} (attempt {attempt + 1}/{retry_attempts})")

            def _make_request():
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
                resp.raise_for_status()
                return resp

            # Enforce timeout using the project utility
            response = run_with_api_timeout(_make_request, timeout_seconds=TIMEOUT_SECONDS)

            try:
                result_json = response.json()
            except ValueError as e:
                raise MalformedResponseError(f"Failed to parse JSON response: {e}")

            # Handle HuggingFace specific response formats
            if isinstance(result_json, list) and len(result_json) > 0:
                generated_text = result_json[0].get("generated_text", "")
            elif isinstance(result_json, dict) and "generated_text" in result_json:
                generated_text = result_json["generated_text"]
            elif isinstance(result_json, dict) and "error" in result_json:
                # Model might be loading
                error_msg = result_json.get("error", "Model loading error")
                logger.warning(f"Model loading or error: {error_msg}. Retrying...")
                time.sleep(_calculate_backoff(attempt))
                continue
            else:
                raise MalformedResponseError(f"Unexpected response structure: {result_json}")

            if not generated_text:
                logger.warning("Received empty generated_text from API.")
                return ""

            logger.info(f"Successfully generated {len(generated_text)} chars.")
            return generated_text

        except ProjectTimeoutError as e:
            last_error = e
            logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
            if attempt == retry_attempts - 1:
                raise InferenceError(f"API request timed out after {retry_attempts} attempts.")
            time.sleep(_calculate_backoff(attempt))

        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt == retry_attempts - 1:
                raise InferenceError(f"Network error after {retry_attempts} attempts: {e}")
            time.sleep(_calculate_backoff(attempt))

        except (InferenceError, MalformedResponseError) as e:
            # Non-retryable errors or handled logic
            if isinstance(e, MalformedResponseError):
                # Malformed responses are usually not fixed by retrying unless transient
                logger.error(f"Malformed response: {e}")
                raise
            # For InferenceError (e.g., 429, 500), we might retry if it was wrapped
            if "Rate limited" in str(e) or "Server error" in str(e):
                if attempt == retry_attempts - 1:
                    raise
                time.sleep(_calculate_backoff(attempt))
            else:
                raise

        except Exception as e:
            last_error = e
            logger.exception(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt == retry_attempts - 1:
                raise InferenceError(f"Unexpected error after retries: {e}")
            time.sleep(_calculate_backoff(attempt))

    raise InferenceError(f"Failed to get response after {retry_attempts} attempts. Last error: {last_error}")


def main():
    """Test script for the API client."""
    test_prompt = "Translate this Python function to JavaScript:\n\ndef add(a, b):\n    return a + b"
    try:
        logger.info("Testing API client with a sample prompt...")
        result = call_inference_api(
            prompt=test_prompt,
            max_new_tokens=100,
            temperature=0.1,
            seed=42
        )
        logger.info(f"Result:\n{result}")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
