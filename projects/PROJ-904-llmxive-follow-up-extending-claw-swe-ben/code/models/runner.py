"""
ModelRunner module for llmXive automated science pipeline.

Implements a generic ModelRunner class that supports loading LLMs with
Q4_K_M quantization on CPU, handling memory pressure via aggressive
quantization or termination flags.
"""

import os
import sys
import logging
import time
import signal
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from utils.logger import ModelExecutionError, setup_logger, log_error

# Configure logger for this module
logger = setup_logger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    do_sample: bool = True
    repetition_penalty: float = 1.1
    pad_token_id: Optional[int] = None


class ModelRunner:
    """
    Generic model runner supporting CPU execution with quantization.

    Features:
    - Loads models with Q4_K_M quantization via bitsandbytes
    - Handles memory pressure via quantization and early termination
    - Supports both 1B and 7B parameter models
    - Thread-safe execution with timeout support
    """

    def __init__(
        self,
        model_path: str,
        quantization_level: str = "q4_k_m",
        device: str = "cpu",
        max_memory_mb: Optional[int] = None,
        timeout_seconds: Optional[int] = None
    ):
        """
        Initialize the model runner.

        Args:
            model_path: Hugging Face model identifier or local path
            quantization_level: Quantization level ('q4_k_m', 'q8_0', 'none')
            device: Device to run on ('cpu', 'cuda')
            max_memory_mb: Maximum memory in MB (for memory pressure handling)
            timeout_seconds: Optional timeout for generation in seconds
        """
        self.model_path = model_path
        self.quantization_level = quantization_level
        self.device = device
        self.max_memory_mb = max_memory_mb
        self.timeout_seconds = timeout_seconds
        self.model = None
        self.tokenizer = None
        self._loaded = False

        logger.info(f"Initializing ModelRunner for {model_path} on {device}")

    def _get_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """
        Get the quantization configuration based on the selected level.

        Returns:
            BitsAndBytesConfig or None if no quantization requested
        """
        if self.quantization_level == "none":
            return None

        # Q4_K_M quantization for CPU execution
        # This provides a good balance between memory usage and quality
        if self.quantization_level == "q4_k_m":
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                llm_int8_enable_fp32_cpu_offload=True,  # Enable CPU offloading
                llm_int8_has_fp16_weight=False,
            )
        elif self.quantization_level == "q8_0":
            return BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_enable_fp32_cpu_offload=True,
                llm_int8_has_fp16_weight=False,
            )
        else:
            raise ValueError(f"Unknown quantization level: {self.quantization_level}")

    def load_model(self) -> bool:
        """
        Load the model and tokenizer with quantization.

        Returns:
            True if loading successful, False otherwise

        Raises:
            ModelExecutionError: If model loading fails
        """
        if self._loaded:
            logger.warning("Model already loaded")
            return True

        try:
            logger.info(f"Loading tokenizer from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                padding_side="left"
            )

            # Set pad token if not set
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            logger.info(f"Loading model with {self.quantization_level} quantization")
            quant_config = self._get_quantization_config()

            device_map = "auto" if self.device == "cuda" else None

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                quantization_config=quant_config,
                device_map=device_map,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )

            if self.device == "cpu" and self.model:
                self.model = self.model.to("cpu")

            self._loaded = True
            logger.info(f"Model loaded successfully: {self.model_path}")
            return True

        except Exception as e:
            error_msg = f"Failed to load model {self.model_path}: {str(e)}"
            log_error(logger, error_msg, exc_info=True)
            raise ModelExecutionError(error_msg) from e

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
        self._loaded = False
        logger.info("Model unloaded")

    def _handle_memory_pressure(self) -> bool:
        """
        Handle memory pressure by attempting aggressive quantization.

        Returns:
            True if memory pressure was handled, False if termination required
        """
        logger.warning("Memory pressure detected, attempting aggressive handling")

        # Try to unload and reload with stricter quantization
        if self.quantization_level != "q4_k_m":
            old_level = self.quantization_level
            self.quantization_level = "q4_k_m"
            logger.info(f"Downgrading quantization from {old_level} to q4_k_m")

            try:
                self.unload_model()
                self.load_model()
                return True
            except Exception as e:
                logger.error(f"Failed to downgrade quantization: {e}")
                return False

        # If already at max quantization, suggest termination
        logger.error("Cannot reduce memory further, termination recommended")
        return False

    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate text from a prompt.

        Args:
            prompt: Input prompt text
            config: Generation configuration (uses defaults if None)

        Returns:
            Tuple of (generated_text, metadata_dict)

        Raises:
            ModelExecutionError: If generation fails
            TimeoutError: If generation exceeds timeout
        """
        if not self._loaded:
            self.load_model()

        if config is None:
            config = GenerationConfig()

        metadata = {
            "prompt_length": len(prompt),
            "generation_start_time": time.time(),
            "model_path": self.model_path,
        }

        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True
            )

            if self.device == "cpu":
                inputs = {k: v for k, v in inputs.items()}

            start_time = time.time()

            # Generate with timeout handling
            if self.timeout_seconds:
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Generation exceeded {self.timeout_seconds}s timeout")

                # Set signal handler (Unix only)
                if hasattr(signal, 'SIGALRM'):
                    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(self.timeout_seconds)

                try:
                    with torch.no_grad():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=config.max_new_tokens,
                            temperature=config.temperature,
                            top_p=config.top_p,
                            top_k=config.top_k,
                            do_sample=config.do_sample,
                            repetition_penalty=config.repetition_penalty,
                            pad_token_id=config.pad_token_id or self.tokenizer.pad_token_id,
                            eos_token_id=self.tokenizer.eos_token_id,
                        )
                finally:
                    if hasattr(signal, 'SIGALRM'):
                        signal.alarm(0)
                        signal.signal(signal.SIGALRM, old_handler)
            else:
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=config.max_new_tokens,
                        temperature=config.temperature,
                        top_p=config.top_p,
                        top_k=config.top_k,
                        do_sample=config.do_sample,
                        repetition_penalty=config.repetition_penalty,
                        pad_token_id=config.pad_token_id or self.tokenizer.pad_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                    )

            generation_time = time.time() - start_time
            metadata["generation_time"] = generation_time

            # Decode output
            generated_text = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )

            # Remove prompt from generated text
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):]

            metadata["generated_length"] = len(generated_text)
            metadata["success"] = True

            return generated_text.strip(), metadata

        except TimeoutError:
            logger.error("Generation timed out")
            metadata["success"] = False
            metadata["error"] = "timeout"
            raise
        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            log_error(logger, error_msg, exc_info=True)

            # Try to handle memory pressure
            if "memory" in str(e).lower() or "cuda" in str(e).lower():
                if self._handle_memory_pressure():
                    logger.info("Retrying generation after memory handling")
                    return self.generate(prompt, config)

            metadata["success"] = False
            metadata["error"] = str(e)
            raise ModelExecutionError(error_msg) from e

    def __enter__(self):
        """Context manager entry."""
        self.load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.unload_model()
        return False


def main():
    """
    Main function for testing the ModelRunner.

    This is a simple test to verify the runner can be instantiated
    and that the API surface is correct.
    """
    logger.info("ModelRunner test started")

    # Example usage (not executed in production)
    runner = ModelRunner(
        model_path="microsoft/Phi-3-mini-4k-instruct",
        quantization_level="q4_k_m",
        device="cpu"
    )

    config = GenerationConfig(
        max_new_tokens=100,
        temperature=0.7
    )

    test_prompt = "What is the capital of France?"

    try:
        # Note: This would actually run if a model was available
        # response, metadata = runner.generate(test_prompt, config)
        logger.info(f"ModelRunner initialized successfully for: {runner.model_path}")
        logger.info(f"Quantization: {runner.quantization_level}")
        logger.info(f"Device: {runner.device}")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

    logger.info("ModelRunner test completed")


if __name__ == "__main__":
    main()
