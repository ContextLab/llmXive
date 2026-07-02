"""
CPU-tractable LLM client wrapper.

Supports:
1. HuggingFace Inference API (HTTP)
2. Local GGUF inference via llama-cpp-python (CPU only)

No CUDA/GPU usage is enabled or required.
"""

import os
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

import requests
from requests.exceptions import RequestException

# Optional import for GGUF support; handled gracefully if missing
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

from utils.logger import get_logger, LLMClientError

logger = get_logger(__name__)


class LLMClient:
    """
    Unified client for HuggingFace Inference API and local GGUF models.
    Designed for CPU-only execution.
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        hf_api_key: Optional[str] = None,
        gguf_path: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        timeout: int = 60,
        use_cache: bool = False,
    ):
        """
        Initialize the client.

        Args:
            model_id: HuggingFace model ID (e.g., 'mistralai/Mistral-7B-Instruct-v0.1')
            hf_api_key: HuggingFace API token. If None, reads from HF_API_KEY env var.
            gguf_path: Path to a local .gguf file. If provided, GGUF mode is used.
            max_tokens: Maximum new tokens to generate.
            temperature: Sampling temperature (0.0 for deterministic).
            timeout: Request timeout in seconds.
            use_cache: If True, attempts to cache responses (simple in-memory cache).
        """
        self.model_id = model_id
        self.hf_api_key = hf_api_key or os.getenv("HF_API_KEY")
        self.gguf_path = gguf_path
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.use_cache = use_cache

        # Simple in-memory cache: key -> response
        self._cache: Dict[str, str] = {} if use_cache else None

        # Determine mode
        self.mode = "gguf" if self.gguf_path else "hf_api"

        if self.mode == "gguf":
            if not LLAMA_CPP_AVAILABLE:
                raise ImportError(
                    "llama-cpp-python is required for GGUF mode but is not installed. "
                    "Install it via: pip install llama-cpp-python"
                )
            if not Path(self.gguf_path).exists():
                raise FileNotFoundError(f"GGUF model file not found at: {self.gguf_path}")

            logger.info(f"Initializing GGUF client from: {self.gguf_path}")
            # CPU-only configuration
            self._llm = Llama(
                model_path=self.gguf_path,
                n_ctx=2048,
                n_threads=4,  # Tune as needed for CPU
                n_batch=512,
                verbose=False,
            )
        elif self.mode == "hf_api":
            if not self.hf_api_key:
                raise ValueError(
                    "HuggingFace API key is required for HF API mode. "
                    "Provide it via 'hf_api_key' argument or set HF_API_KEY env var."
                )
            if not self.model_id:
                raise ValueError("model_id is required for HuggingFace API mode.")
            logger.info(f"Initializing HuggingFace API client for model: {self.model_id}")
        else:
            raise ValueError("Either gguf_path or model_id+hf_api_key must be provided.")

    def _get_cache_key(self, prompt: str, **kwargs) -> str:
        """Generate a cache key from prompt and relevant kwargs."""
        import hashlib
        data = f"{prompt}:{self.max_tokens}:{self.temperature}:{kwargs}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _query_hf_api(self, prompt: str) -> str:
        """Query HuggingFace Inference API."""
        url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        headers = {
            "Authorization": f"Bearer {self.hf_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "do_sample": self.temperature > 0,
                "return_full_text": False,
            },
        }

        start = time.time()
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            elapsed = time.time() - start
            logger.debug(f"HF API request took {elapsed:.2f}s, status: {response.status_code}")

            response.raise_for_status()
            result = response.json()

            # HF Inference API can return a list or a single dict depending on config
            if isinstance(result, list) and len(result) > 0:
                generated = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                generated = result.get("generated_text", "")
            else:
                generated = ""

            return generated.strip()

        except RequestException as e:
            logger.error(f"HF API request failed: {e}")
            raise LLMClientError(f"Failed to query HuggingFace API: {e}") from e

    def _query_gguf(self, prompt: str) -> str:
        """Query local GGUF model via llama-cpp-python."""
        start = time.time()
        try:
            output = self._llm(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=[],  # No custom stops; caller should manage context
                echo=False,
            )
            elapsed = time.time() - start
            logger.debug(f"GGUF inference took {elapsed:.2f}s")

            generated = output.get("choices", [{}])[0].get("text", "")
            return generated.strip()

        except Exception as e:
            logger.error(f"GGUF inference failed: {e}")
            raise LLMClientError(f"Failed to query GGUF model: {e}") from e

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text for a given prompt.

        Args:
            prompt: The input prompt string.
            **kwargs: Additional parameters (currently ignored; uses instance defaults).

        Returns:
            Generated text string.

        Raises:
            LLMClientError: If generation fails.
        """
        if self.use_cache:
            cache_key = self._get_cache_key(prompt, **kwargs)
            if cache_key in self._cache:
                logger.debug("Cache hit for prompt")
                return self._cache[cache_key]

        try:
            if self.mode == "hf_api":
                result = self._query_hf_api(prompt)
            else:
                result = self._query_gguf(prompt)

            if self.use_cache:
                self._cache[cache_key] = result

            return result

        except LLMClientError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during generation: {e}")
            raise LLMClientError(f"Unexpected error during generation: {e}") from e

    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Generate text for a list of prompts sequentially.

        Args:
            prompts: List of prompt strings.
            **kwargs: Additional parameters.

        Returns:
            List of generated text strings.
        """
        results = []
        for i, prompt in enumerate(prompts):
            logger.info(f"Processing batch item {i+1}/{len(prompts)}")
            try:
                result = self.generate(prompt, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate for prompt {i}: {e}")
                results.append("")  # Or raise, depending on desired behavior
        return results


def create_client(
    mode: str = "hf_api",
    model_id: Optional[str] = None,
    hf_api_key: Optional[str] = None,
    gguf_path: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    timeout: int = 60,
    use_cache: bool = False,
) -> LLMClient:
    """
    Factory function to create an LLMClient instance.

    Args:
        mode: 'hf_api' or 'gguf'
        model_id: HuggingFace model ID (required for hf_api mode)
        hf_api_key: HuggingFace API key (required for hf_api mode)
        gguf_path: Path to GGUF file (required for gguf mode)
        max_tokens: Max new tokens
        temperature: Sampling temperature
        timeout: Request timeout
        use_cache: Enable simple in-memory caching

    Returns:
        LLMClient instance
    """
    return LLMClient(
        model_id=model_id,
        hf_api_key=hf_api_key,
        gguf_path=gguf_path,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
        use_cache=use_cache,
    )