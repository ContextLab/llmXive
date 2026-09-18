"""
ModelRunner class for loading and executing LLMs.
Supports 1B and 7B models with Q4_K_M quantization on CPU.
"""
import os
import sys
import logging
import time
import signal
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GenerationConfig:
    """Configuration for model generation."""
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    do_sample: bool = True

class ModelRunner:
    """
    Runner for LLM models.
    Handles loading, inference, and memory management.
    """
    def __init__(self, model_path: str, quantization: str = "Q4_K_M", model_size: str = "1b"):
        self.model_path = model_path
        self.quantization = quantization
        self.model_size = model_size
        self.model = None
        self.tokenizer = None
        logger.info(f"Initializing ModelRunner for {model_path} ({quantization})")

    def load_model(self) -> None:
        """
        Load the model and tokenizer.
        Uses quantization to fit in CPU memory.
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            import torch

            logger.info(f"Loading model: {self.model_path}")

            # Configure quantization
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)

            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                quantization_config=bnb_config,
                device_map="auto" if torch.cuda.is_available() else "cpu",
                torch_dtype=torch.float16
            )

            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    def generate(self, prompt: str, context: str, config: Optional[GenerationConfig] = None) -> Tuple[str, float]:
        """
        Generate a response given prompt and context.
        Returns (output, duration).
        """
        if self.model is None or self.tokenizer is None:
            self.load_model()

        config = config or GenerationConfig()

        # Combine context and prompt
        full_input = f"{context}\n\nIssue: {prompt}\n\nSolution:"

        start = time.time()

        try:
            inputs = self.tokenizer(full_input, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = inputs.to("cuda")

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=config.max_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    do_sample=config.do_sample
                )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            duration = time.time() - start

            # Check if solution was generated (simple heuristic)
            success = "def " in response or "class " in response or "return" in response

            return response, duration, success
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise RuntimeError(f"Generation failed: {e}") from e

def main():
    """Main entry point for testing the runner."""
    # Dummy test
    runner = ModelRunner("dummy_path")
    print("ModelRunner initialized")

if __name__ == "__main__":
    main()
