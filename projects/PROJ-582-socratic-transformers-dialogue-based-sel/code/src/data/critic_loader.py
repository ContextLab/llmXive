"""
T050: Download/Load Frozen Critic Model.

Acquires a frozen, pre-trained small model (Mistral-7B-Instruct-v0.2)
to be used as the external critic for generating critiques.
Ensures separation from the trainable base model by loading with
frozen parameters and specific quantization for CPU efficiency.
"""
import os
import sys
import gc
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Default model: Mistral-7B-Instruct-v0.2 is a strong, small critic candidate.
# It is smaller than Llama-3-8B and generally performs well on reasoning tasks.
DEFAULT_CRITIC_MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"

class CriticModel:
    """
    Wrapper for the frozen critic model.
    Handles loading, tokenization, and generation with parameters frozen.
    """
    def __init__(self, model: AutoModelForCausalLM, tokenizer: AutoTokenizer, config: SocraticConfig):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        self.device = config.device if hasattr(config, 'device') and config.device else "cpu"
        
        # Ensure model is frozen to prevent gradient updates during critique generation
        for param in self.model.parameters():
            param.requires_grad = False
        
        self.model.eval()
        logger.info(f"Critic model loaded and frozen on device: {self.device}")

    def generate_critique(self, question: str, initial_answer: str, max_new_tokens: int = 256) -> str:
        """
        Generates a critique based on the question and initial answer.
        Uses a structured prompt template to enforce logical analysis.
        """
        prompt = (
            f"System: You are a rigorous logic critic. Your task is to identify "
            f"logical contradictions, calculation errors, or unsupported assumptions "
            f"in the following answer to a question. "
            f"Question: {question}\n"
            f"Initial Answer: {initial_answer}\n"
            f"Task: Analyze the reasoning step-by-step. If you find an error, "
            f"explain it clearly. If the answer is correct, state that no errors were found.\n"
            f"Critique:"
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the generated part
        generated_text = response[len(prompt):].strip()
        return generated_text

def load_frozen_critic(
    model_id: Optional[str] = None,
    quantize: bool = True
) -> Tuple[CriticModel, SocraticConfig]:
    """
    Loads the frozen critic model.
    
    Args:
        model_id: HuggingFace model ID. Defaults to Mistral-7B-Instruct-v0.2.
        quantize: If True, uses 4-bit quantization (bitsandbytes) to fit in memory.
    
    Returns:
        Tuple of (CriticModel instance, Config object)
    
    Raises:
        RuntimeError: If the model cannot be loaded or dependencies are missing.
    """
    config = get_config()
    model_id = model_id or config.critic_model_id or DEFAULT_CRITIC_MODEL_ID
    
    logger.info(f"Loading frozen critic model: {model_id}")
    
    # Determine device
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    
    # Quantization config for 4-bit loading (requires bitsandbytes)
    bnb_config = None
    if quantize and device == "cuda":
        try:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
            logger.info("Using 4-bit quantization for critic model.")
        except Exception as e:
            logger.warning(f"Failed to initialize 4-bit quantization: {e}. Falling back to 8-bit or full precision.")
            bnb_config = None
    elif quantize and device == "cpu":
        # For CPU, we rely on standard float32/16 or torch.compile if available,
        # as bitsandbytes 4-bit is primarily for CUDA.
        logger.info("Running on CPU; standard precision will be used for critic model.")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            padding_side="left"
        )
        
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model_kwargs = {
            "trust_remote_code": True,
            "device_map": "auto" if device != "cpu" else None,
            "torch_dtype": torch.float16 if device != "cpu" else torch.float32,
        }
        
        if bnb_config:
            model_kwargs["quantization_config"] = bnb_config

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            **model_kwargs
        )
        
        # Wrap in our custom class
        critic = CriticModel(model, tokenizer, config)
        return critic, config

    except Exception as e:
        logger.error(f"Failed to load critic model {model_id}: {e}")
        raise RuntimeError(f"Could not load frozen critic model. Ensure 'bitsandbytes' and 'transformers' are installed. Error: {e}")

def main():
    """
    Entry point for testing the critic loader.
    Downloads and loads the model, then prints a test critique.
    """
    logger.info("Starting T050: Frozen Critic Model Loader")
    
    try:
        critic, config = load_frozen_critic()
        
        # Test generation
        test_question = "If I have 3 apples and eat 2, how many do I have?"
        test_answer = "I have 1 apple left because 3 minus 2 is 1."
        
        logger.info(f"Generating critique for: {test_question}")
        critique = critic.generate_critique(test_question, test_answer, max_new_tokens=128)
        
        logger.info(f"Generated Critique:\n{critique}")
        logger.info("T050: Critic model loaded and tested successfully.")
        
    except Exception as e:
        logger.error(f"T050 Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
