import os
import time
import logging
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path
from src.utils.timeout_utils import run_with_api_timeout, TimeoutError as ProjectTimeoutError
from src.utils.logging import get_logger

# Configure logging for this module
logger = get_logger(__name__)

# API Configuration
# Using HuggingFace Inference API endpoint for CodeLlama-7B
# The specific model ID is passed in the payload, endpoint is the base HF Inference URL
HF_INFERENCE_ENDPOINT = "https://api-inference.huggingface.co/models/codellama/CodeLlama-7b-Instruct-hf"
DEFAULT_MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 60.0
API_TIMEOUT_SECONDS = 120

class InferenceError(Exception):
    """Base exception for inference API failures."""
    pass

class MalformedResponseError(InferenceError):
    """Raised when the API response structure is invalid or missing expected fields."""
    pass

class RateLimitError(InferenceError):
    """Raised when the API returns a 429 Too Many Requests status."""
    pass

class ModelLoadingError(InferenceError):
    """Raised when the model is currently loading (503)."""
    pass


def _get_headers() -> Dict[str, str]:
    """Construct headers for the API request."""
    api_token = os.getenv("HF_API_TOKEN")
    if not api_token:
        logger.warning("HF_API_TOKEN not found in environment. Request will fail if auth is required.")
    
    headers = {
        "Content-Type": "application/json",
    }
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    return headers


def _exponential_backoff(attempt: int) -> float:
    """Calculate backoff duration with jitter."""
    backoff = min(INITIAL_BACKOFF_SECONDS * (2 ** attempt), MAX_BACKOFF_SECONDS)
    # Add small jitter to prevent thundering herd
    jitter = backoff * 0.1
    return backoff + (jitter * (0.5 - (hash(str(time.time())) % 1000) / 1000.0))


def call_inference_api(
    prompt: str,
    model_id: str = "codellama/CodeLlama-7b-Instruct-hf",
    max_new_tokens: int = 512,
    temperature: float = 0.2,
    do_sample: bool = True,
    stop_sequences: Optional[List[str]] = None,
    max_retries: int = DEFAULT_MAX_RETRIES
) -> str:
    """
    Call the HuggingFace Inference API with exponential backoff and timeout enforcement.
    
    Args:
        prompt: The input prompt text.
        model_id: The HuggingFace model ID to query.
        max_new_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature.
        do_sample: Whether to use sampling.
        stop_sequences: List of strings to stop generation.
        max_retries: Maximum number of retry attempts.
        
    Returns:
        The generated text output.
        
    Raises:
        InferenceError: If all retries fail or the API returns a fatal error.
        MalformedResponseError: If the response cannot be parsed.
        ProjectTimeoutError: If the request exceeds the timeout limit.
    """
    headers = _get_headers()
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "do_sample": do_sample,
            "stop": stop_sequences or [],
            "return_full_text": False
        }
    }
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Wrap the request in the timeout handler
            def _make_request():
                response = requests.post(
                    HF_INFERENCE_ENDPOINT,
                    headers=headers,
                    json=payload,
                    timeout=API_TIMEOUT_SECONDS
                )
                return response
            
            response = run_with_api_timeout(_make_request, timeout_seconds=API_TIMEOUT_SECONDS)
            
            # Handle HTTP status codes
            if response.status_code == 200:
                try:
                    data = response.json()
                    # HF Inference API returns a list of dicts with 'generated_text'
                    if isinstance(data, list) and len(data) > 0:
                        if "generated_text" in data[0]:
                            return data[0]["generated_text"]
                        else:
                            raise MalformedResponseError(
                                f"Response missing 'generated_text': {data}"
                            )
                    else:
                        raise MalformedResponseError(
                            f"Unexpected response format: {data}"
                        )
                except requests.exceptions.JSONDecodeError:
                    raise MalformedResponseError(
                        f"Invalid JSON response: {response.text}"
                    )
            
            elif response.status_code == 503:
                # Model is loading
                retry_after = int(response.headers.get("Retry-After", 5))
                error_msg = f"Model loading (503). Retrying after {retry_after}s."
                logger.warning(error_msg)
                time.sleep(retry_after)
                last_error = ModelLoadingError(error_msg)
                continue
            
            elif response.status_code == 429:
                # Rate limited
                retry_after = int(response.headers.get("Retry-After", 10))
                error_msg = f"Rate limited (429). Retrying after {retry_after}s."
                logger.warning(error_msg)
                time.sleep(retry_after)
                last_error = RateLimitError(error_msg)
                continue
            
            elif response.status_code >= 500:
                # Server error, retry with backoff
                backoff_time = _exponential_backoff(attempt)
                logger.warning(f"Server error {response.status_code}. Retrying in {backoff_time:.1f}s...")
                time.sleep(backoff_time)
                last_error = InferenceError(f"Server error {response.status_code}: {response.text}")
                continue
            
            else:
                # Client error (4xx) that is not rate limit - likely fatal
                error_detail = response.text[:200]
                raise InferenceError(
                    f"API request failed with status {response.status_code}: {error_detail}"
                )
        
        except ProjectTimeoutError as e:
            logger.error(f"Request timed out after {API_TIMEOUT_SECONDS}s: {e}")
            last_error = e
            if attempt == max_retries - 1:
                raise
            # Retry on timeout
            backoff_time = _exponential_backoff(attempt)
            logger.warning(f"Retrying after timeout in {backoff_time:.1f}s...")
            time.sleep(backoff_time)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            last_error = InferenceError(f"Network error: {e}")
            if attempt == max_retries - 1:
                raise
            backoff_time = _exponential_backoff(attempt)
            time.sleep(backoff_time)
    
    # If we exit the loop, all retries failed
    raise last_error or InferenceError("Max retries exceeded")


def main():
    """
    Main entry point for testing the API client.
    This is intended to be run as a script to verify connectivity.
    """
    test_prompt = "<s>[INST] Convert the following Python function to JavaScript:\n\ndef add(a, b):\n    return a + b\n\n[/INST]"
    
    logger.info("Testing API client connectivity...")
    try:
        result = call_inference_api(
            prompt=test_prompt,
            max_new_tokens=50,
            temperature=0.1
        )
        logger.info(f"Success! Generated {len(result)} characters.")
        logger.info(f"Output preview: {result[:100]}...")
    except Exception as e:
        logger.error(f"API test failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
