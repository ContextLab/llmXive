"""
LLM Client Wrapper for CPU-tractable inference.

Supports:
1. HuggingFace Inference API (HTTP)
2. Local GGUF inference via llama-cpp-python (CPU only)

This module implements the interface required by T017 (orchestrator) to query
LLMs without requiring CUDA/GPU resources.
"""

import os
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import requests
from config import get_env_var, Paths
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
HF_API_URL = "https://api-inference.huggingface.co/models/"
DEFAULT_MODEL = "meta-llama/Llama-2-7b-chat-hf"  # Fallback if not specified
MAX_RETRIES = 3
RETRY_DELAY = 5.0  # seconds

# GGUF defaults
GGUF_DEFAULT_PATH = "data/raw/models/gguf/llama-2-7b.Q4_K_M.gguf"
GGUF_MAX_TOKENS = 2048
GGUF_N_CTX = 4096


class LLMClientError(Exception):
    """Custom exception for LLM client errors."""
    pass


class LLMClient:
    """
    Unified client for LLM inference supporting HuggingFace API and local GGUF.

    Attributes:
        mode (str): Either 'hf_api' or 'local_gguf'
        model_id (str): Model identifier (HF repo or local path)
        api_key (str, optional): HuggingFace API key if using HF mode
    """

    def __init__(
        self,
        mode: str = "hf_api",
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY,
    ):
        """
        Initialize the LLM client.

        Args:
            mode: 'hf_api' or 'local_gguf'
            model_id: HuggingFace model ID or local GGUF path
            api_key: HuggingFace API token (required for HF mode)
            max_retries: Number of retry attempts for transient failures
            retry_delay: Delay between retries in seconds
        """
        self.mode = mode
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        if mode == "hf_api":
            self.model_id = model_id or get_env_var("HF_MODEL_ID", DEFAULT_MODEL)
            self.api_key = api_key or get_env_var("HF_API_KEY")
            if not self.api_key:
                raise LLMClientError(
                    "HuggingFace API key is required for 'hf_api' mode. "
                    "Set HF_API_KEY environment variable."
                )
            self._init_hf_client()
        elif mode == "local_gguf":
            self.model_path = model_id or get_env_var("GGUF_MODEL_PATH", GGUF_DEFAULT_PATH)
            self._init_gguf_client()
        else:
            raise LLMClientError(f"Unsupported mode: {mode}. Use 'hf_api' or 'local_gguf'.")

        logger.info(f"Initialized LLMClient in {mode} mode with model: {self.model_id if mode == 'hf_api' else self.model_path}")

    def _init_hf_client(self):
        """Initialize HuggingFace Inference API client."""
        # No heavy initialization needed, just validate key
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            # Quick sanity check
            resp = requests.get(
                f"{HF_API_URL}{self.model_id}/status",
                headers=headers,
                timeout=10
            )
            if resp.status_code == 401:
                raise LLMClientError("Invalid HuggingFace API key.")
            if resp.status_code == 404:
                logger.warning(f"Model {self.model_id} not found on HF Hub. It may be private or require login.")
            logger.debug(f"HF API connectivity check passed for {self.model_id}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not verify HF API connection: {e}. Will attempt on first query.")

    def _init_gguf_client(self):
        """Initialize local GGUF client using llama-cpp-python."""
        try:
            from llama_cpp import Llama
        except ImportError:
            raise LLMClientError(
                "llama-cpp-python is required for 'local_gguf' mode. "
                "Install it via: pip install llama-cpp-python"
            )

        if not Path(self.model_path).exists():
            raise LLMClientError(
                f"GGUF model file not found at: {self.model_path}. "
                "Please download a model (e.g., via huggingface-cli) and set GGUF_MODEL_PATH."
            )

        logger.info(f"Loading GGUF model from {self.model_path} (CPU only)...")
        start_time = time.time()
        
        self._llm = Llama(
            model_path=self.model_path,
            n_ctx=GGUF_N_CTX,
            n_threads=os.cpu_count() or 4,
            use_mmap=True,
            use_mlock=False,
            verbose=False  # Suppress llama.cpp verbose logs
        )
        
        load_time = time.time() - start_time
        logger.info(f"GGUF model loaded in {load_time:.2f}s")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
        stream: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt string.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature (0.0 = deterministic).
            top_p: Nucleus sampling parameter.
            stop: List of stop sequences.
            stream: If True, returns a generator (not implemented for HF API in this simple wrapper).

        Returns:
            Generated text string.

        Raises:
            LLMClientError: If generation fails after retries.
        """
        if stream:
            logger.warning("Streaming not fully implemented for HF API in this wrapper; returning full response.")

        if self.mode == "hf_api":
            return self._generate_hf(prompt, max_tokens, temperature, top_p, stop)
        else:
            return self._generate_gguf(prompt, max_tokens, temperature, top_p, stop)

    def _generate_hf(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop: Optional[List[str]]
    ) -> str:
        """Execute HuggingFace Inference API generation with retries."""
        url = f"{HF_API_URL}{self.model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Payload for text-generation models
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "return_full_text": False,  # Don't repeat the prompt
                "stop": stop or []
            }
        }

        for attempt in range(self.max_retries):
            try:
                # HF Inference API is synchronous
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 503:
                    # Model loading
                    wait_time = response.headers.get("retry-after", str(self.retry_delay))
                    logger.warning(f"Model loading (503). Retrying in {wait_time}s...")
                    time.sleep(float(wait_time) if wait_time.isdigit() else self.retry_delay)
                    continue
                
                if response.status_code != 200:
                    raise LLMClientError(f"HF API error: {response.status_code} - {response.text}")

                result = response.json()
                # HF API returns list of dicts with 'generated_text'
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").strip()
                elif isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"].strip()
                else:
                    logger.warning(f"Unexpected HF API response structure: {result}")
                    return ""

            except requests.exceptions.Timeout:
                logger.warning(f"Request timed out (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt == self.max_retries - 1:
                    raise LLMClientError(f"HF API request failed after {self.max_retries} attempts: {e}")
                time.sleep(self.retry_delay)
        
        raise LLMClientError("Max retries exceeded for HF API")

    def _generate_gguf(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop: Optional[List[str]]
    ) -> str:
        """Execute local GGUF generation."""
        try:
            # llama-cpp-python generate method
            output = self._llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or [],
                echo=False,
                verbose=False
            )
            
            if isinstance(output, dict) and "choices" in output:
                return output["choices"][0]["text"].strip()
            elif isinstance(output, str):
                return output.strip()
            else:
                raise LLMClientError(f"Unexpected GGUF output type: {type(output)}")
                
        except Exception as e:
            logger.error(f"GGUF generation failed: {e}")
            raise LLMClientError(f"Local generation failed: {e}")


def get_client(mode: str = "hf_api", **kwargs) -> LLMClient:
    """
    Factory function to get an LLMClient instance.
    
    Args:
        mode: 'hf_api' or 'local_gguf'
        **kwargs: Arguments passed to LLMClient.__init__
        
    Returns:
        Configured LLMClient instance.
    """
    return LLMClient(mode=mode, **kwargs)
