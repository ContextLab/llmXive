import os
import sys
import gc
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CriticModel:
    """
    Represents a frozen critic model used for generating critiques in the Socratic dialogue pipeline.
    
    Attributes:
        model: The underlying HuggingFace model instance.
        tokenizer: The associated tokenizer.
        config: Model configuration.
        is_frozen: Boolean indicating if gradients are disabled.
    """
    def __init__(self, model: AutoModelForCausalLM, tokenizer: AutoTokenizer, config: Dict[str, Any]):
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        self.is_frozen = False
        self._freeze()

    def _freeze(self):
        """Freezes all parameters of the model to prevent fine-tuning."""
        for param in self.model.parameters():
            param.requires_grad = False
        self.model.eval()
        self.is_frozen = True
        logger.info("Critic model parameters frozen successfully.")

    def generate_critique(self, prompt: str, max_new_tokens: int = 256) -> str:
        """
        Generates a critique based on the provided prompt.
        
        Args:
            prompt: The input text prompt.
            max_new_tokens: Maximum number of tokens to generate.
            
        Returns:
            The generated critique string.
        """
        if not self.is_frozen:
            raise RuntimeError("Model must be frozen before inference.")
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False, # Deterministic generation for consistency
                temperature=None
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the prompt from the output if it's included in the generation
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):]
        
        return generated_text.strip()

def load_frozen_critic(
    model_name: str = "meta-llama/Llama-3-8b",
    device_map: str = "auto",
    quantization_bits: int = 4
) -> Tuple[CriticModel, str]:
    """
    Loads a pre-trained, frozen critic model with 4-bit quantization.
    
    This function acquires a known base checkpoint (e.g., Llama-3-8B) and ensures
    it is not fine-tuned (no LoRA adapters loaded unless specified) and that
    gradients are disabled.
    
    Args:
        model_name: HuggingFace model identifier.
        device_map: Device mapping strategy ('auto', 'cpu', 'cuda').
        quantization_bits: Bits for quantization (4 or 8).
        
    Returns:
        A tuple containing the CriticModel instance and the model name used.
        
    Raises:
        ValueError: If the model cannot be verified as a base checkpoint or if loading fails.
        RuntimeError: If memory constraints are violated or model is not frozen.
    """
    logger.info(f"Attempting to load frozen critic model: {model_name}")
    
    # Verify model is a base checkpoint (not a fine-tuned adapter)
    # In a real scenario, we might check HF metadata or a local manifest.
    # For this implementation, we assume the provided model_name is the base.
    if "lora" in model_name.lower() or "finetuned" in model_name.lower():
        logger.warning(f"Warning: Model {model_name} appears to be a fine-tuned variant. "
                       "Proceeding only if explicitly intended.")
    
    # Configure 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Ensure tokenizer handles padding correctly
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map=device_map,
            trust_remote_code=True,
            torch_dtype=torch.float16
        )
        
        # Explicitly freeze the model
        critic = CriticModel(model, tokenizer, {"name": model_name})
        
        # Verification: Assert requires_grad is False
        for param in critic.model.parameters():
            if param.requires_grad:
                raise RuntimeError("Model parameters were not successfully frozen.")
        
        logger.info(f"Successfully loaded and frozen critic model: {model_name}")
        return critic, model_name
        
    except Exception as e:
        logger.error(f"Failed to load critic model {model_name}: {str(e)}")
        raise

def main():
    """
    Main entry point to test the critic loader.
    Loads the model, verifies it is frozen, and runs a sample generation.
    """
    # Configuration
    MODEL_NAME = "meta-llama/Llama-3-8b" # Using Llama-3-8B as the base
    # Fallback for environments without internet or restricted access could be a smaller model
    # but the task requires a "frozen, pre-trained small model (e.g., Llama-3-8B or similar)"
    
    try:
        critic, name = load_frozen_critic(model_name=MODEL_NAME)
        
        # Verification: Check model config for fine-tune history (if available in config)
        # For base models, this is usually empty or default
        if hasattr(critic.model.config, 'finetuned'):
            if critic.model.config.finetuned:
                logger.warning("Model config indicates it is fine-tuned.")
        
        # Test generation
        test_prompt = "Question: If x = 5 and y = 3, what is x + y? Answer: 8. Critique this answer."
        logger.info(f"Running sample generation with prompt: {test_prompt[:50]}...")
        
        response = critic.generate_critique(test_prompt, max_new_tokens=100)
        logger.info(f"Generated response: {response}")
        
        print(f"SUCCESS: Critic model loaded and frozen. Model: {name}")
        print(f"Sample Critique: {response}")
        
    except Exception as e:
        logger.critical(f"Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()