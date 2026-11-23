import os
import sys
import logging
import signal
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Attempt to import llama-cpp-python. 
# If not installed, this will raise ImportError, which is the correct "fail loud" behavior 
# for a missing dependency, rather than faking functionality.
try:
    from llama_cpp import Llama
except ImportError:
    raise ImportError(
        "llama-cpp-python is required. Install with: pip install llama-cpp-python"
    )

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default timeout in seconds for VLM generation
DEFAULT_TIMEOUT_SECONDS = 120

class VLMTimeoutError(Exception):
    """Raised when VLM generation exceeds the configured timeout."""
    pass

class VLMWrapper:
    """
    Wrapper for the Phi-3-mini-4k-instruct-GGUF model using llama-cpp-python.
    Implements robust timeout handling and memory error handling for batch processing.
    """
    
    def __init__(
        self, 
        model_path: str, 
        n_ctx: int = 4096, 
        n_threads: int = 4, 
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        log_file: Optional[str] = None
    ):
        """
        Initialize the VLM wrapper.
        
        Args:
            model_path: Path to the GGUF model file.
            n_ctx: Context window size.
            n_threads: Number of CPU threads to use.
            timeout_seconds: Maximum time allowed for a single generation call.
            log_file: Path to the log file for skipped instances (e.g., outputs/skipped_instances.log).
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.timeout_seconds = timeout_seconds
        self.log_file = log_file
        self.model: Optional[Llama] = None
        
        # Ensure log directory exists if log_file is specified
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing VLMWrapper with model: {model_path}, timeout: {timeout_seconds}s")

    def _log_skipped_instance(self, instance_id: str, reason: str):
        """
        Logs a skipped instance to the designated log file.
        
        Args:
            instance_id: The ID of the instance that was skipped.
            reason: The reason for skipping (e.g., timeout, memory error).
        """
        if not self.log_file:
            logger.warning(f"Instance {instance_id} skipped ({reason}), but no log file configured.")
            return

        try:
            log_entry = {
                "instance_id": instance_id,
                "reason": reason,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
            logger.warning(f"Skipped instance {instance_id}: {reason}. Logged to {self.log_file}")
        except Exception as e:
            logger.error(f"Failed to write skip log for {instance_id}: {e}")

    def load_model(self) -> None:
        """Load the model from disk."""
        if self.model is not None:
            return

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        logger.info(f"Loading model from {self.model_path}...")
        try:
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                verbose=False  # Reduce llama_cpp verbosity
            )
            logger.info("Model loaded successfully.")
        except MemoryError as e:
            logger.error(f"MemoryError while loading model: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate_description(
        self, 
        prompt: str, 
        instance_id: str, 
        max_tokens: int = 256
    ) -> str:
        """
        Generate a description for a given prompt with robust timeout handling.
        
        If the generation exceeds `timeout_seconds` or runs out of memory, 
        the instance is logged as skipped and a VLMTimeoutError (or MemoryError) is raised.
        
        Args:
            prompt: The text prompt for the VLM.
            instance_id: The ID of the current instance (for logging).
            max_tokens: Maximum tokens to generate.
        
        Returns:
            The generated description string.
        
        Raises:
            VLMTimeoutError: If generation exceeds the timeout.
            MemoryError: If the process runs out of memory during generation.
            Exception: Other unexpected errors.
        """
        if self.model is None:
            self.load_model()

        logger.debug(f"Generating description for instance {instance_id}")

        # Use signal-based timeout for Unix-like systems
        if os.name != 'nt':  # Not Windows
            def timeout_handler(signum, frame):
                raise VLMTimeoutError(f"Generation timed out after {self.timeout_seconds}s for instance {instance_id}")

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout_seconds)
        
        start_time = time.time()
        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                stop=["</s>", "Instruction:"], # Common stop tokens
                echo=False
            )
            elapsed = time.time() - start_time
            logger.debug(f"Generation took {elapsed:.2f}s for instance {instance_id}")
            
            # Cancel alarm if we finished early
            if os.name != 'nt':
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            return output['choices'][0]['text'].strip()

        except VLMTimeoutError:
            # Cancel alarm on exception too
            if os.name != 'nt':
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            self._log_skipped_instance(instance_id, "Timeout")
            raise

        except MemoryError:
            if os.name != 'nt':
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            self._log_skipped_instance(instance_id, "MemoryError")
            raise

        except Exception as e:
            if os.name != 'nt':
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            logger.error(f"Unexpected error during generation for {instance_id}: {e}")
            # Log other errors as well to ensure we don't silently lose data
            self._log_skipped_instance(instance_id, f"Error: {str(e)}")
            raise

        finally:
            # Ensure alarm is cleared if we somehow exited without it
            if os.name != 'nt':
                try:
                    signal.alarm(0)
                except:
                    pass

    def generate_batch(
        self, 
        prompts: List[str], 
        instance_ids: List[str], 
        max_tokens: int = 256
    ) -> List[Optional[str]]:
        """
        Generate descriptions for a batch of prompts.
        
        This method iterates through the batch. If an individual instance fails 
        (timeout, memory error), it logs the failure and continues to the next 
        instance, returning None for the failed entry in the results list.
        
        Args:
            prompts: List of prompts.
            instance_ids: List of corresponding instance IDs.
            max_tokens: Max tokens per generation.
        
        Returns:
            List of generated descriptions. Failed entries are None.
        """
        if len(prompts) != len(instance_ids):
            raise ValueError("Prompts and instance_ids must have the same length")

        results = []
        for prompt, inst_id in zip(prompts, instance_ids):
            try:
                desc = self.generate_description(prompt, inst_id, max_tokens)
                results.append(desc)
            except (VLMTimeoutError, MemoryError) as e:
                # Log handled in generate_description, just append None
                results.append(None)
            except Exception as e:
                logger.error(f"Unhandled exception for {inst_id}: {e}")
                results.append(None)
        
        return results

def create_vlm_wrapper(
    model_path: str, 
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    log_file: str = "outputs/skipped_instances.log"
) -> VLMWrapper:
    """
    Factory function to create a VLMWrapper instance.
    
    Args:
        model_path: Path to the GGUF model.
        timeout_seconds: Timeout for generation.
        log_file: Path to the skip log file.
        
    Returns:
        Configured VLMWrapper instance.
    """
    return VLMWrapper(
        model_path=model_path,
        timeout_seconds=timeout_seconds,
        log_file=log_file
    )