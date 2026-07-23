import os
import time
import logging
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path

from src.utils.timeout_utils import enforce_api_timeout, TimeoutError
from src.utils.logging import get_logger

# Configure logging for this module
logger = get_logger(__name__)

class InferenceError(Exception):
    """Custom exception for API inference failures."""
    pass

class MalformedResponseError(Exception):
    """Custom exception for malformed API responses."""
    pass

# Configuration constants
API_ENDPOINT = os.getenv("INFERENCE_API_ENDPOINT", "https://api-inference.huggingface.co/models/codellama/CodeLlama-7b-Instruct-hf")
API_TOKEN = os.getenv("HF_API_TOKEN")
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 60.0     # seconds
TIMEOUT_SECONDS = 120

def _calculate_backoff(attempt: int) -> float:
    """Calculate exponential backoff with jitter."""
    backoff = min(INITIAL_BACKOFF * (2 ** attempt), MAX_BACKOFF)
    # Add small jitter to prevent thundering herd
    jitter = backoff * 0.1 * (os.urandom(1)[0] / 255.0)
    return backoff + jitter

def call_inference_api(
    prompt: str,
    model_id: str = "codellama/CodeLlama-7b-Instruct-hf",
    max_new_tokens: int = 512,
    temperature: float = 0.2,
    do_sample: bool = True,
    retry_attempts: int = MAX_RETRIES
) -> str:
    """
    Call the HuggingFace Inference API with exponential backoff and timeout enforcement.

    Args:
        prompt: The input prompt text.
        model_id: HuggingFace model identifier.
        max_new_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature.
        do_sample: Whether to use sampling.
        retry_attempts: Maximum number of retry attempts.

    Returns:
        Generated text content.

    Raises:
        InferenceError: If all retries fail or API returns a fatal error.
        MalformedResponseError: If the response structure is invalid.
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
            "do_sample": do_sample,
            "return_full_text": False,
            "stop": ["</s>", "# End of translation"]
        }
    }

    last_exception = None

    for attempt in range(retry_attempts):
        try:
            logger.debug(f"API request attempt {attempt + 1}/{retry_attempts} for model {model_id}")

            # Enforce timeout using the utility
            response = enforce_api_timeout(
                requests.post,
                (API_ENDPOINT,),
                {
                    "headers": headers,
                    "json": payload,
                    "timeout": TIMEOUT_SECONDS
                },
                timeout_duration=TIMEOUT_SECONDS
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    if not isinstance(data, list) or len(data) == 0:
                        raise MalformedResponseError("Response is not a non-empty list.")
                    if "generated_text" not in data[0]:
                        raise MalformedResponseError(f"Missing 'generated_text' in response: {data}")
                    return data[0]["generated_text"].strip()
                except ValueError as e:
                    raise MalformedResponseError(f"Failed to parse JSON response: {e}")

            elif response.status_code == 503:
                # Model loading or service unavailable - retry with backoff
                wait_time = _calculate_backoff(attempt)
                logger.warning(f"Model loading (503). Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
                continue

            elif response.status_code == 429:
                # Rate limited - retry with backoff
                wait_time = _calculate_backoff(attempt)
                logger.warning(f"Rate limited (429). Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
                continue

            else:
                # Fatal error
                error_detail = response.text
                raise InferenceError(f"API request failed with status {response.status_code}: {error_detail}")

        except TimeoutError as e:
            logger.warning(f"Request timed out on attempt {attempt + 1}: {e}")
            if attempt == retry_attempts - 1:
                raise
            time.sleep(_calculate_backoff(attempt))
            continue

        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error on attempt {attempt + 1}: {e}")
            last_exception = e
            if attempt == retry_attempts - 1:
                raise InferenceError(f"Network failure after {retry_attempts} attempts: {e}")
            time.sleep(_calculate_backoff(attempt))
            continue

        except Exception as e:
            # Unexpected error - log and re-raise immediately if it's not a retryable network issue
            logger.error(f"Unexpected error: {e}")
            if attempt == retry_attempts - 1:
                raise InferenceError(f"Unexpected error after {retry_attempts} attempts: {e}")
            time.sleep(_calculate_backoff(attempt))
            continue

    raise InferenceError(f"Failed to get response after {retry_attempts} attempts.")

def main():
    """
    Main entry point for testing the API client.
    Runs a simple test call to verify connectivity and configuration.
    """
    test_prompt = "Translate the following Python code to JavaScript:\n\nprint('Hello World')"
    logger.info("Testing API client with a sample prompt...")
    try:
        result = call_inference_api(test_prompt)
        logger.info(f"Success! Generated output:\n{result}")
    except Exception as e:
        logger.error(f"API test failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()