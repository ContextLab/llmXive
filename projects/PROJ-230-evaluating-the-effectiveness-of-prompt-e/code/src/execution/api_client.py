"""
API Client for HuggingFace Inference API.
Implements exponential backoff, timeout enforcement, and error handling.
"""
import os
import time
import logging
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path

from src.utils.timeout_utils import enforce_api_timeout, TimeoutError as ProjectTimeoutError

# Configure logger
logger = logging.getLogger(__name__)

class InferenceError(Exception):
    """Base exception for inference API errors."""
    pass

class MalformedResponseError(InferenceError):
    """Raised when the API response structure is invalid."""
    pass

class RateLimitError(InferenceError):
    """Raised when the API returns a 429 rate limit response."""
    pass

class ServerError(InferenceError):
    """Raised for 5xx server errors."""
    pass

# Configuration
API_BASE_URL = "https://api-inference.huggingface.co/models/codellama/CodeLlama-7b-hf"
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0
TIMEOUT_SECONDS = 120

def call_inference_api(
    prompt: str,
    api_key: Optional[str] = None,
    max_new_tokens: int = 512,
    temperature: float = 0.2,
    seed: Optional[int] = None
) -> str:
    """
    Call the HuggingFace Inference API with exponential backoff and timeout.

    Args:
        prompt: The input prompt text.
        api_key: HuggingFace API token. Defaults to HF_TOKEN env var.
        max_new_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        seed: Random seed for deterministic generation.

    Returns:
        The generated text output.

    Raises:
        InferenceError: If the API call fails after retries.
        MalformedResponseError: If the response cannot be parsed.
        ProjectTimeoutError: If the request exceeds the timeout.
    """
    token = api_key or os.getenv("HF_TOKEN")
    if not token:
        raise InferenceError("HF_TOKEN environment variable not set and no API key provided.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "return_full_text": False,
            "do_sample": temperature > 0,
        }
    }
    if seed is not None:
        payload["parameters"]["seed"] = seed

    url = API_BASE_URL

    last_exception = None
    backoff = INITIAL_BACKOFF

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Wrap the request with timeout enforcement
            def make_request():
                response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
                return response

            # Use the project's timeout utility
            response = enforce_api_timeout(make_request, timeout_seconds=TIMEOUT_SECONDS)

            if response.status_code == 200:
                data = response.json()
                if not isinstance(data, list) or len(data) == 0:
                    raise MalformedResponseError(f"Unexpected response structure: {data}")
                
                # Handle the typical HF response format: [{'generated_text': '...'}]
                if 'generated_text' in data[0]:
                    return data[0]['generated_text'].strip()
                else:
                    raise MalformedResponseError(f"Missing 'generated_text' in response: {data}")

            elif response.status_code == 429:
                # Rate limited
                retry_after = response.headers.get('Retry-After', backoff)
                try:
                    wait_time = float(retry_after)
                except (ValueError, TypeError):
                    wait_time = backoff
                
                logger.warning(f"Rate limited. Waiting {wait_time}s before retry {attempt}/{MAX_RETRIES}.")
                time.sleep(wait_time)
                last_exception = RateLimitError(f"Rate limit exceeded. Retry-After: {retry_after}")
                continue

            elif 500 <= response.status_code < 600:
                # Server error, retry
                logger.warning(f"Server error {response.status_code}. Retrying in {backoff}s (attempt {attempt}/{MAX_RETRIES}).")
                time.sleep(backoff)
                last_exception = ServerError(f"Server error: {response.status_code} - {response.text}")
                backoff = min(backoff * 2, MAX_BACKOFF)
                continue

            else:
                # Client error (4xx) that is not rate limit - likely permanent
                raise InferenceError(f"Client error {response.status_code}: {response.text}")

        except ProjectTimeoutError as e:
            logger.error(f"Request timed out after {TIMEOUT_SECONDS}s on attempt {attempt}.")
            last_exception = e
            if attempt == MAX_RETRIES:
                raise
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)

        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error on attempt {attempt}: {e}. Retrying...")
            last_exception = e
            if attempt == MAX_RETRIES:
                raise InferenceError(f"Network error after {MAX_RETRIES} retries: {e}")
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)

        except (ValueError, KeyError, TypeError) as e:
            # Parsing errors are likely fatal unless the payload is wrong
            raise MalformedResponseError(f"Failed to parse response: {e}")

    # If we exit the loop without returning, raise the last exception
    raise InferenceError(f"Failed after {MAX_RETRIES} retries. Last error: {last_exception}")

def main():
    """
    CLI entry point for testing the API client.
    Usage: python -m src.execution.api_client --prompt "def add(a, b):"
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Test HuggingFace Inference API client")
    parser.add_argument("--prompt", type=str, default="def add(a, b):\n    return a + b", help="Input prompt")
    parser.add_argument("--api-key", type=str, default=None, help="HF API Token")
    parser.add_argument("--max-tokens", type=int, default=128, help="Max new tokens")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    
    try:
        result = call_inference_api(
            prompt=args.prompt,
            api_key=args.api_key,
            max_new_tokens=args.max_tokens,
            seed=args.seed
        )
        print(f"Generated:\n{result}")
    except InferenceError as e:
        logger.error(f"API Call failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()