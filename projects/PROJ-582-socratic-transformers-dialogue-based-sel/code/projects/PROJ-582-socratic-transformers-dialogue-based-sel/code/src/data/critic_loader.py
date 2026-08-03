import os
import sys
import gc
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

from src.utils.config import get_config, SocraticConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CriticModel:
    """
    Wrapper for a frozen pre-trained model used as an external critic.
    
    This model is loaded in inference mode (no gradients) and is intended
    to generate critiques for the Socratic dialogue generation process.
    It is distinct from the trainable base model used for the main task.
    """
    
    def __init__(
        self,
        model_path: str,
        tokenizer_path: Optional[str] = None,
        quantization_config: Optional[BitsAndBytesConfig] = None
    ):
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path or model_path
        self.quantization_config = quantization_config
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        
    def load(self) -> Tuple[Any, Any]:
        """
        Load the frozen critic model and tokenizer.
        
        Returns:
            Tuple[model, tokenizer]: The loaded model and tokenizer.
        
        Raises:
            RuntimeError: If the model fails to load.
        """
        if self.is_loaded:
            logger.warning("Critic model already loaded. Returning existing instance.")
            return self.model, self.tokenizer
        
        logger.info(f"Loading frozen critic model from: {self.model_path}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.tokenizer_path,
                trust_remote_code=True
            )
            
            # Ensure pad token is set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
            
            logger.info(f"Tokenizer loaded: {self.tokenizer.__class__.__name__}")
            
            # Prepare quantization config if not provided
            if self.quantization_config is None:
                # Default to 4-bit quantization for CPU/RAM efficiency
                self.quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16
                )
            
            # Load model in inference mode (frozen)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                quantization_config=self.quantization_config,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            # Explicitly freeze all parameters
            for param in self.model.parameters():
                param.requires_grad = False
            
            self.model.eval()
            self.is_loaded = True
            
            logger.info(f"Critic model loaded successfully: {self.model.__class__.__name__}")
            logger.info(f"Model parameters frozen: {sum(p.numel() for p in self.model.parameters())}")
            
        except Exception as e:
            logger.error(f"Failed to load critic model: {str(e)}")
            raise RuntimeError(f"Failed to load critic model from {self.model_path}: {str(e)}")
        
        return self.model, self.tokenizer
    
    def generate_critique(
        self,
        question: str,
        initial_answer: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """
        Generate a critique for the given question and initial answer.
        
        Args:
            question: The original question.
            initial_answer: The initial answer to critique.
            max_new_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            top_p: Top-p sampling threshold.
        
        Returns:
            str: The generated critique text.
        
        Raises:
            RuntimeError: If the model is not loaded.
        """
        if not self.is_loaded:
            raise RuntimeError("Critic model not loaded. Call load() first.")
        
        # Construct the critique prompt
        # This prompt follows the Socratic method: identifying contradictions
        # and unsupported assumptions without originating new knowledge
        prompt = f"""You are a critical evaluator in a Socratic dialogue. 
Your task is to identify logical errors, calculation mistakes, or unsupported assumptions in the following answer.

Question: {question}
Initial Answer: {initial_answer}

Critique:
"""
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Extract the generated critique
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        critique = full_response.split("Critique:\n")[-1].strip()
        
        return critique
    
    def cleanup(self):
        """Clean up model resources."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.is_loaded = False
        logger.info("Critic model resources cleaned up.")


def load_frozen_critic(
    model_name: Optional[str] = None,
    use_quantization: bool = True
) -> CriticModel:
    """
    Load a frozen critic model for generating critiques.
    
    Args:
        model_name: Name of the model to load. Defaults to a small, 
                   efficient model suitable for CPU inference.
        use_quantization: Whether to use 4-bit quantization.
    
    Returns:
        CriticModel: The loaded and ready-to-use critic model.
    
    Raises:
        RuntimeError: If the model fails to load.
    """
    config = get_config()
    
    # Default to a small, efficient model if not specified
    if model_name is None:
        # Using a small model that can run on CPU with quantization
        # Llama-3-8B is mentioned in the task, but for CPU efficiency
        # we might want to start with a smaller variant or use quantization
        model_name = config.critic_model_path or "meta-llama/Meta-Llama-3-8B"
    
    logger.info(f"Initializing frozen critic model: {model_name}")
    
    # Prepare quantization config if requested
    quant_config = None
    if use_quantization:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
    
    critic = CriticModel(
        model_path=model_name,
        quantization_config=quant_config
    )
    
    # Load the model
    critic.load()
    
    logger.info("Frozen critic model ready for critique generation.")
    return critic


def main():
    """
    Main function to demonstrate loading the frozen critic model.
    This can be run as a script to verify the model loads correctly.
    """
    logger.info("Starting frozen critic model loader demonstration...")
    
    try:
        # Load the critic model
        critic = load_frozen_critic(
            model_name=None,  # Use default from config or fallback
            use_quantization=True
        )
        
        # Test with a simple example
        test_question = "What is 2 + 2?"
        test_answer = "The answer is 5."
        
        logger.info(f"Testing critique generation for: {test_question}")
        logger.info(f"Initial answer: {test_answer}")
        
        critique = critic.generate_critique(
            question=test_question,
            initial_answer=test_answer,
            max_new_tokens=100
        )
        
        logger.info(f"Generated critique: {critique}")
        
        # Cleanup
        critic.cleanup()
        logger.info("Demonstration completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()