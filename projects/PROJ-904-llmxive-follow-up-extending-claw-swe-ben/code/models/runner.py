import os
import sys
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from config import get_model_path, get_hf_token, get_env_var

# Ensure logging is configured if not already
if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_new_tokens: int = 512
    temperature: float = 0.0  # Greedy decoding by default for reproducibility
    do_sample: bool = False
    top_p: float = 0.9
    repetition_penalty: float = 1.1
    stop_sequences: Optional[List[str]] = None

class ModelRunner:
    """
    Handles loading and inference for LLM models.
    Supports parameter-scaled models (1B, 7B, 8B) with quantization.
    """

    def __init__(self, model_name: str, quantization_level: str = "q4_k_m", device_map: str = "auto"):
        """
        Initialize the ModelRunner.

        Args:
            model_name: HuggingFace model identifier (e.g., 'meta-llama/Llama-3-8B')
            quantization_level: Quantization strategy ('q4_k_m', 'q8_0', 'none')
            device_map: Device mapping strategy ('auto', 'cpu', 'cuda')
        """
        self.model_name = model_name
        self.quantization_level = quantization_level
        self.device_map = device_map
        self.model = None
        self.tokenizer = None
        self._loaded = False

        logger.info(f"Initializing ModelRunner for {model_name} with {quantization_level} quantization")

    def _get_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """Configure quantization based on the selected level."""
        if self.quantization_level == "none":
            return None

        if self.quantization_level == "q4_k_m":
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
        elif self.quantization_level == "q8_0":
            return BitsAndBytesConfig(
                load_in_8bit=True,
            )
        else:
            raise ValueError(f"Unsupported quantization level: {self.quantization_level}")

    def load(self) -> None:
        """Load the model and tokenizer into memory."""
        if self._loaded:
            logger.warning("Model already loaded.")
            return

        logger.info(f"Loading tokenizer for {self.model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            token=get_hf_token(),
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        logger.info(f"Loading model {self.model_name} with quantization {self.quantization_level}...")
        quantization_config = self._get_quantization_config()

        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                token=get_hf_token(),
                device_map=self.device_map,
                torch_dtype=torch.float16,
                quantization_config=quantization_config,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            self._loaded = True
            logger.info("Model loaded successfully.")
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.critical(
                    f"MEMORY_PRESSURE: Failed to load model {self.model_name} due to OOM. "
                    f"Consider using a smaller model or more aggressive quantization."
                )
                raise RuntimeError(
                    f"Memory pressure exceeded capacity for {self.model_name}. "
                    "Try reducing batch size, using a smaller model, or increasing quantization."
                ) from e
            raise

    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> str:
        """
        Generate a completion for the given prompt.

        Args:
            prompt: The input text prompt.
            config: Generation configuration. Defaults to GenerationConfig().

        Returns:
            The generated text completion.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        if config is None:
            config = GenerationConfig()

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        start_time = time.time()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=config.max_new_tokens,
                temperature=config.temperature,
                do_sample=config.do_sample,
                top_p=config.top_p,
                repetition_penalty=config.repetition_penalty,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        elapsed = time.time() - start_time
        logger.debug(f"Generation took {elapsed:.2f}s for {config.max_new_tokens} max tokens")

        # Decode the output, removing the prompt
        generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
        completion = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        # Handle stop sequences if provided
        if config.stop_sequences:
            for stop_seq in config.stop_sequences:
                if stop_seq in completion:
                    completion = completion.split(stop_seq)[0]
                    break

        return completion.strip()

    def run_instance(self, prompt: str, config: Optional[GenerationConfig] = None) -> Dict[str, Any]:
        """
        Run a single instance through the model and return structured results.

        Args:
            prompt: The input prompt.
            config: Generation configuration.

        Returns:
            Dictionary containing 'completion', 'timestamp', and 'status'.
        """
        try:
            start_time = time.time()
            completion = self.generate(prompt, config)
            end_time = time.time()

            return {
                "completion": completion,
                "timestamp": end_time,
                "status": "success",
                "duration_seconds": end_time - start_time
            }
        except Exception as e:
            logger.error(f"Error running instance: {e}")
            return {
                "completion": "",
                "timestamp": time.time(),
                "status": "error",
                "error_message": str(e)
            }

def main():
    """
    CLI entry point for testing the ModelRunner.
    Usage: python -m models.runner --model <model_name> --prompt "<text>"
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test ModelRunner")
    parser.add_argument("--model", type=str, default="meta-llama/Llama-3-8B",
                        help="HuggingFace model identifier")
    parser.add_argument("--quantization", type=str, default="q4_k_m",
                        help="Quantization level (q4_k_m, q8_0, none)")
    parser.add_argument("--prompt", type=str,
                        default="Write a Python function to calculate the Fibonacci sequence.",
                        help="Input prompt")
    parser.add_argument("--max-tokens", type=int, default=256,
                        help="Maximum new tokens to generate")

    args = parser.parse_args()

    runner = ModelRunner(args.model, quantization_level=args.quantization)
    runner.load()

    config = GenerationConfig(max_new_tokens=args.max_tokens)
    result = runner.run_instance(args.prompt, config)

    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Completion:\n{result['completion']}")
        print(f"Duration: {result['duration_seconds']:.2f}s")
    else:
        print(f"Error: {result['error_message']}")

if __name__ == "__main__":
    main()