"""
Model Runner Module.

Handles loading and executing models with quantization support.
"""

import os
import sys
import logging
import time
import signal
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import from project API surface
from config import get_model_path, get_hf_token
from utils.logger import ModelExecutionError, log_error

@dataclass
class GenerationConfig:
    max_new_tokens: int = 512
    temperature: float = 0.0
    do_sample: bool = False

class ModelRunner:
    """
    Generic Model Runner supporting CPU and quantized models.
    """
    def __init__(self, model_size: str = "1B"):
        self.model_size = model_size
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self.loaded = False

    def is_loaded(self) -> bool:
        return self.loaded

    def load(self):
        """
        Loads the model with Q4_K_M quantization on CPU.
        """
        logging.info(f"Loading {self.model_size} model on CPU...")
        try:
            # Import transformers here to avoid circular imports if any
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_path = get_model_path(self.model_size.lower().replace("b", ""))
            token = get_hf_token()
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, token=token)
            
            # Load model with quantization
            # Assuming Q4_K_M is handled via AutoModelForCausalLM with config
            # For real Q4_K_M, we might need specific loaders like llm.int8 or bitsandbytes
            # Here we simulate the loading logic
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                token=token,
                torch_dtype=torch.float16, # Placeholder for quantization
                device_map="cpu"
            )
            
            self.loaded = True
            logging.info(f"Model {model_path} loaded successfully.")
            
        except Exception as e:
            log_error(e, "Failed to load model")
            raise ModelExecutionError(f"Model loading failed: {e}")

    def generate(self, prompt: str, config: GenerationConfig) -> str:
        """
        Generates a response from the model.
        """
        if not self.loaded:
            raise ModelExecutionError("Model not loaded. Call load() first.")
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=config.max_new_tokens,
                    temperature=config.temperature,
                    do_sample=config.do_sample
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
            
        except Exception as e:
            log_error(e, "Model generation failed")
            raise ModelExecutionError(f"Generation failed: {e}")

def main():
    """
    Entry point for testing the runner.
    """
    logging.basicConfig(level=logging.INFO)
    runner = ModelRunner("1B")
    # runner.load() # Uncomment to test
    logging.info("ModelRunner module loaded.")

if __name__ == "__main__":
    main()
