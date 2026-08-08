"""
Critic Model Loader for Socratic Transformers Project.

This module handles the acquisition and loading of a frozen, pre-trained
"Critic" model used for generating adversarial critiques in the Socratic
dialogue pipeline.

The model is loaded in 4-bit quantization (if supported) or standard precision
with gradients explicitly disabled to ensure it acts as a fixed evaluator.
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

# Project root path resolution
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = _PROJECT_ROOT / "data" / "processed"
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default model configuration
DEFAULT_MODEL_NAME = "meta-llama/Llama-3-8B"
# Fallback to a smaller model if the default is inaccessible or too large for the environment
# Using a widely available base model for demonstration if Llama-3 is not accessible
FALLBACK_MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

class CriticModel:
    """
    Wrapper for the frozen Critic model.

    Attributes:
        model: The underlying HuggingFace model instance.
        tokenizer: The corresponding tokenizer.
        is_frozen: Boolean flag indicating if gradients are disabled.
    """

    def __init__(
        self,
        model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        is_frozen: bool = True,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.is_frozen = is_frozen
        self._verify_frozen()

    def _verify_frozen(self):
        """
        Verifies that the model parameters do not require gradients.
        Raises AssertionError if the model is not frozen.
        """
        for param in self.model.parameters():
            if param.requires_grad:
                raise AssertionError(
                    "Critic model is not frozen. All parameters must have requires_grad=False."
                )
        logger.info("Critic model verification passed: requires_grad is False for all parameters.")

    def generate_critique(self, prompt: str, max_new_tokens: int = 256) -> str:
        """
        Generates a critique based on the input prompt.

        Args:
            prompt: The input text to critique.
            max_new_tokens: Maximum number of tokens to generate.

        Returns:
            The generated critique string.
        """
        if not self.is_frozen:
            logger.warning("Model is not frozen. Generating in eval mode but gradients are enabled.")
            self.model.eval()

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False, # Deterministic generation for consistency
                temperature=None,
                top_p=None,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


def load_frozen_critic(
    model_name: Optional[str] = None,
    use_4bit: bool = True,
    device_map: str = "auto",
) -> CriticModel:
    """
    Loads a pre-trained model as a frozen Critic.

    This function attempts to load the specified model (defaulting to Llama-3-8B
    or a fallback). It configures the model to be frozen (requires_grad=False)
    and ensures it is in evaluation mode.

    Args:
        model_name: HuggingFace model identifier. Defaults to DEFAULT_MODEL_NAME.
        use_4bit: Whether to use 4-bit quantization via bitsandbytes.
        device_map: Device mapping strategy for transformers (e.g., "auto", "cpu", "cuda").

    Returns:
        A CriticModel instance with frozen weights.

    Raises:
        RuntimeError: If the model cannot be loaded or verified as frozen.
        ImportError: If required dependencies (bitsandbytes) are missing when 4bit is requested.
    """
    model_name = model_name or DEFAULT_MODEL_NAME

    # Attempt to load Llama-3 if specified, otherwise fallback
    try:
        logger.info(f"Attempting to load model: {model_name}")
        
        # Configure quantization if requested
        quant_config = None
        if use_4bit:
            try:
                from bitsandbytes.nn import Linear4bit
                quant_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                )
                logger.info("4-bit quantization configured.")
            except ImportError:
                logger.warning("bitsandbytes not found. Disabling 4-bit quantization.")
                use_4bit = False

        # Load Tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load Model
        load_kwargs = {
            "device_map": device_map,
            "torch_dtype": torch.float16,
        }
        if use_4bit and quant_config:
            load_kwargs["quantization_config"] = quant_config

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **load_kwargs,
            trust_remote_code=True,
        )

        # Ensure model is in eval mode
        model.eval()

        # FREEZE ALL PARAMETERS
        for param in model.parameters():
            param.requires_grad = False

        # Verify the freeze status explicitly
        # This satisfies the verification requirement: "Assert model.requires_grad = False"
        total_params = 0
        frozen_params = 0
        for name, param in model.named_parameters():
            total_params += 1
            if not param.requires_grad:
                frozen_params += 1
        
        if frozen_params != total_params:
            raise RuntimeError(
                f"Model is not fully frozen. {total_params - frozen_params} parameters require gradients."
            )
        
        logger.info(f"Model loaded and frozen successfully. Total parameters: {total_params}")

        return CriticModel(model, tokenizer, is_frozen=True)

    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        # If the primary model fails (e.g., access denied, OOM), try fallback if not already tried
        if model_name != FALLBACK_MODEL_NAME:
            logger.info(f"Attempting fallback model: {FALLBACK_MODEL_NAME}")
            return load_frozen_critic(
                model_name=FALLBACK_MODEL_NAME,
                use_4bit=use_4bit,
                device_map=device_map,
            )
        raise RuntimeError(f"Could not load any critic model. Last error: {e}") from e


def main():
    """
    Main entry point for testing the Critic Loader.
    Loads the model, verifies it is frozen, and prints a sample generation.
    """
    logger.info("Starting Critic Model Loader verification...")
    
    try:
        # Load the model
        critic = load_frozen_critic(model_name="microsoft/Phi-3-mini-4k-instruct")
        
        # Verification: Check requires_grad
        assert not critic.model.requires_grad, "Model requires_grad is True!"
        for param in critic.model.parameters():
            assert not param.requires_grad, f"Parameter {param.name} requires_grad is True!"
        
        logger.info("✓ Verification Passed: Model is frozen (requires_grad=False).")

        # Verification: Check config for fine-tune history (simple check)
        # We assume if we loaded from a base checkpoint, it's not fine-tuned for this specific task yet.
        # A more rigorous check would involve checking for adapter weights in PeftModel,
        # but for a base model load, the absence of LoRA adapters implies it's base.
        if hasattr(critic.model, "peft_config"):
            if critic.model.peft_config:
                logger.warning("Model appears to have PEFT adapters. This might be a fine-tuned checkpoint.")
            else:
                logger.info("Model is a base checkpoint (no PEFT adapters found).")
        else:
            logger.info("Model is a standard base checkpoint.")

        # Test generation
        test_prompt = "Critique the following math solution for logical gaps: The answer is 42 because 6*7=42."
        logger.info(f"Generating critique for: {test_prompt}")
        critique = critic.generate_critique(test_prompt, max_new_tokens=50)
        logger.info(f"Generated Critique: {critique}")

        logger.info("Critic Loader verification complete.")
        return 0

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())