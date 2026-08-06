"""
LLM Client with caching support for performance optimization.
Implements a simple in-memory and disk-based cache to avoid redundant API calls.
"""
import os
import time
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import requests
from config import get_env_var, Paths
from utils.logger import get_logger

logger = get_logger(__name__)

class LLMClientError(Exception):
    """Custom exception for LLM client errors."""
    pass

class LLMClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/Meta-Llama-3-8B-Instruct"):
        self.api_key = api_key or get_env_var("HF_API_KEY")
        if not self.api_key:
            raise LLMClientError("HF_API_KEY environment variable is required.")
        
        self.model = model
        self.base_url = "https://api-inference.huggingface.co/models/"
        
        # Caching setup
        self.cache_dir = Paths.STATE_DIR / "llm_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache: Dict[str, Dict] = {}
        self._load_cache()

    def _load_cache(self):
        """Load existing cache from disk if available."""
        cache_file = self.cache_dir / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded LLM cache with {len(self.cache)} entries.")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache: {e}. Starting fresh.")
                self.cache = {}

    def _save_cache(self):
        """Save cache to disk."""
        cache_file = self.cache_dir / "cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save cache: {e}")

    def _get_cache_key(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate a deterministic cache key for a prompt."""
        # Normalize prompt slightly to avoid whitespace issues
        normalized = prompt.strip()
        key_str = f"{normalized}|{temperature}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _query_api(self, prompt: str, temperature: float = 0.0, max_tokens: int = 1024) -> str:
        """Perform the actual API request."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": temperature > 0.0,
                "return_full_text": False
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}{self.model}/generate",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            else:
                raise LLMClientError(f"Unexpected API response format: {result}")
                
        except requests.exceptions.Timeout:
            raise LLMClientError("API request timed out.")
        except requests.exceptions.RequestException as e:
            raise LLMClientError(f"API request failed: {str(e)}")

    def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 1024) -> str:
        """
        Generate text with caching support.
        Returns cached result if available, otherwise queries API and caches.
        """
        cache_key = self._get_cache_key(prompt, temperature)
        
        if cache_key in self.cache:
            cached_entry = self.cache[cache_key]
            # Optional: Add TTL check here if needed
            logger.debug(f"Cache hit for prompt (key: {cache_key[:8]}...)")
            return cached_entry["response"]

        logger.debug(f"Cache miss for prompt (key: {cache_key[:8]}...), querying API...")
        response = self._query_api(prompt, temperature, max_tokens)
        
        # Update cache
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        # Periodic save to avoid data loss on crash
        if len(self.cache) % 10 == 0:
            self._save_cache()

        return response

def get_client() -> LLMClient:
    """Factory function to get a configured LLM client."""
    return LLMClient()
