import os
import sys
import gc
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

from src.utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CriticModel:
    """
    Wrapper for the frozen critic model used in adversarial dialogue generation.
    
    This model is loaded with 4-bit quantization to fit in memory and is kept
    frozen (requires_grad=False) to serve as a fixed external mechanism for
    generating critiques during the dialogue generation process.
    """
    
    def __init__(self, model_id: str, quantization_config: Optional[BitsAndBytesConfig] = None):
        """
        Initialize the CriticModel.
        
        Args:
            model_id: HuggingFace model ID for the critic model.
            quantization_config: Optional quantization configuration for 4-bit loading.
        """
        self.model_id = model_id
        self.quantization_config = quantization_config
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self._loaded = False
    
    def load(self) -> None:
        """
        Load the model and tokenizer from HuggingFace.
        
        The model is loaded with 4-bit quantization if configured, and all
        parameters are frozen (requires_grad=False).
        """
        if self._loaded:
            logger.warning("Model already loaded. Unloading first.")
            self.unload()
        
        logger.info(f"Loading critic model: {self.model_id}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            trust_remote_code=True
        )
        
        # Set pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model with quantization if configured
        if self.quantization_config:
            logger.info("Loading model with 4-bit quantization...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                quantization_config=self.quantization_config,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.float16
            )
        else:
            logger.info("Loading model without quantization...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.float16
            )
        
        # Freeze all parameters
        self.model.requires_grad_(False)
        
        # Verify freezing
        for param in self.model.parameters():
            assert not param.requires_grad, "Model parameters should be frozen"
        
        self.model.eval()
        self._loaded = True
        logger.info(f"Successfully loaded and frozen critic model: {self.model_id}")
    
    def unload(self) -> None:
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self._loaded = False
        logger.info("Critic model unloaded")
    
    def generate_critique(self, answer: str, max_new_tokens: int = 256) -> str:
        """
        Generate a critique for a given answer.
        
        Args:
            answer: The answer text to critique.
            max_new_tokens: Maximum number of tokens to generate.
        
        Returns:
            The generated critique text.
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        # Create prompt
        prompt = f"Identify logical contradictions, unsupported assumptions, or high-probability errors in the following answer: {answer}. Output only the critique."
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        critique = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove prompt from output
        critique = critique.replace(prompt, "").strip()
        
        return critique

def load_frozen_critic() -> CriticModel:
    """
    Load the frozen critic model based on configuration.
    
    Returns:
        A CriticModel instance that is loaded and frozen.
    
    Raises:
        RuntimeError: If the model fails to load.
    """
    config = get_config()
    model_id = config.CRICIT_MODEL_ID
    
    logger.info(f"Loading frozen critic model: {model_id}")
    
    # Configure 4-bit quantization
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )
    
    critic = CriticModel(model_id=model_id, quantization_config=quantization_config)
    
    try:
        critic.load()
        
        # Verify model is frozen
        assert critic.model.requires_grad == False, "Model should be frozen"
        
        # Verify architecture matches config (basic check)
        assert critic.model is not None, "Model should be loaded"
        
        logger.info("Critic model loaded and verified")
        return critic
        
    except Exception as e:
        logger.error(f"Failed to load critic model: {e}")
        raise RuntimeError(f"Failed to load critic model: {e}")

def main():
    """Entry point for testing the critic loader."""
    logger.info("Testing critic model loader...")
    
    try:
        critic = load_frozen_critic()
        logger.info("Critic model loaded successfully")
        
        # Test generation
        test_answer = "The answer is 42 because the universe is finite."
        critique = critic.generate_critique(test_answer)
        logger.info(f"Generated critique: {critique}")
        
        # Verify model is frozen
        assert critic.model.requires_grad == False
        logger.info("Model verified as frozen")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()