import os
import sys
import logging
import signal
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import logging utilities from the project
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class VLMTimeoutError(Exception):
    """Custom exception for VLM generation timeouts."""
    pass

class VLMWrapper:
    """
    Wrapper for Phi-3-mini-4k-instruct-GGUF using llama-cpp-python.
    Implements robust timeout handling and memory error handling.
    """
    
    def __init__(self, model_path: str, n_ctx: int = 4096, n_threads: int = 4):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.model = None
        self._loaded = False
        logger.info(f"Initializing VLMWrapper with model: {model_path}")

    def load_model(self):
        """Load the GGUF model."""
        if self._loaded:
            return
        
        try:
            from llama_cpp import Llama
            logger.info(f"Loading model from {self.model_path}...")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=0,  # CPU-only constraint
                verbose=False
            )
            self._loaded = True
            logger.info("Model loaded successfully.")
        except ImportError:
            logger.error("llama-cpp-python not installed. Cannot load VLM.")
            raise
        except Exception as e:
            logger.error(f"Failed to load VLM model: {e}")
            raise

    def _generate_with_timeout(self, prompt: str, max_tokens: int = 256, timeout_seconds: int = 300) -> str:
        """
        Generate text with a timeout mechanism using signal alarm.
        Only works on Unix-like systems where signal.SIGALRM is available.
        """
        if sys.platform == 'win32':
            # Fallback for Windows: signal not available, rely on internal loop or external watchdog
            # For this implementation, we assume Unix or that the underlying library handles it.
            # We will wrap the call in a try/except for OOM and rely on the caller for timeout if on Windows.
            logger.warning("Signal-based timeout not available on Windows. Using standard generation.")
            return self._generate_inner(prompt, max_tokens)
        
        def timeout_handler(signum, frame):
            raise VLMTimeoutError(f"VLM generation timed out after {timeout_seconds} seconds")

        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        try:
            signal.alarm(timeout_seconds)
            result = self._generate_inner(prompt, max_tokens)
            return result
        except VLMTimeoutError:
            raise
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def _generate_inner(self, prompt: str, max_tokens: int) -> str:
        """Inner generation logic without timeout wrapper."""
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                stop=["</s>", "Instruction:"],
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except MemoryError:
            raise MemoryError("VLM generation ran out of memory.")
        except Exception as e:
            # Catch specific llama-cpp errors if possible, otherwise generic
            logger.error(f"Generation error: {e}")
            raise

    def generate_description(self, instance_id: str, prompt: str, timeout_seconds: int = 300) -> Optional[str]:
        """
        Generate a description for a given prompt.
        Handles timeouts and memory errors gracefully.
        
        Args:
            instance_id: Unique identifier for the current instance (for logging).
            prompt: The text prompt for the VLM.
            timeout_seconds: Timeout in seconds for the generation.
        
        Returns:
            Generated text string, or None if skipped due to error.
        """
        try:
            description = self._generate_with_timeout(prompt, timeout_seconds=timeout_seconds)
            return description
        except VLMTimeoutError as e:
            logger.warning(f"[Instance {instance_id}] TIMEOUT: {e}. Skipping instance.")
            self._log_skipped_instance(instance_id, reason="TIMEOUT", error=str(e))
            return None
        except MemoryError as e:
            logger.warning(f"[Instance {instance_id}] MEMORY_ERROR: {e}. Skipping instance.")
            self._log_skipped_instance(instance_id, reason="MEMORY_ERROR", error=str(e))
            return None
        except Exception as e:
            # Catch any other unexpected errors to prevent pipeline crash
            logger.error(f"[Instance {instance_id}] UNEXPECTED_ERROR: {e}. Skipping instance.")
            self._log_skipped_instance(instance_id, reason="UNEXPECTED_ERROR", error=str(e))
            return None

    def _log_skipped_instance(self, instance_id: str, reason: str, error: str):
        """
        Log the skipped instance to outputs/skipped_instances.log.
        Creates the file and directory if they don't exist.
        """
        log_dir = Path("outputs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "skipped_instances.log"
        
        log_entry = {
            "instance_id": instance_id,
            "reason": reason,
            "error": str(error),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except IOError as io_err:
            logger.error(f"Failed to write to skipped_instances.log: {io_err}")

def create_vlm_wrapper(model_path: str) -> VLMWrapper:
    """Factory function to create a VLMWrapper instance."""
    return VLMWrapper(model_path)