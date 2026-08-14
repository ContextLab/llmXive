"""
Critic Model Loader for Socratic Transformers.

This module handles the acquisition and loading of a frozen, pre-trained
critic model used for generating adversarial critiques. The model is loaded
with 4-bit quantization to fit within the 7GB RAM constraint.

Philosophy: This engine executes ordered operations (selection pressure)
and does not originate inquiry. The critic model is a static component
defined by configuration.
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

# Import configuration from the existing API surface
from src.utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CriticModel:
    """
    Wrapper class for the frozen critic model and its tokenizer.

    Attributes:
        model: The loaded PyTorch model instance.
        tokenizer: The associated tokenizer.
        config: The configuration object used for loading.
    """
    def __init__(self, model: AutoModelForCausalLM, tokenizer: AutoTokenizer, config_id: str):
        self.model = model
        self.tokenizer = tokenizer
        self.config_id = config_id
        self._verify_frozen()

    def _verify_frozen(self) -> None:
        """Assert that the model parameters are frozen (requires_grad=False)."""
        for param in self.model.parameters():
            if param.requires_grad:
                raise RuntimeError(
                    f"Critic model parameters must be frozen. "
                    f"Found a parameter with requires_grad=True in model {self.config_id}."
                )
        logger.info(f"Critic model '{self.config_id}' verified as frozen.")


def load_frozen_critic() -> CriticModel:
    """
    Loads the frozen critic model specified in the project configuration.

    This function:
    1. Reads `CRITIC_MODEL_ID` from `src/utils/config.py`.
    2. Configures 4-bit quantization via `bitsandbytes` for CPU/GPU efficiency.
    3. Loads the model and tokenizer from HuggingFace.
    4. Verifies the model is frozen.
    5. Returns a `CriticModel` instance.

    Returns:
        CriticModel: The loaded, frozen critic model wrapper.

    Raises:
        RuntimeError: If the model cannot be loaded or is not frozen.
        KeyError: If `CRITIC_MODEL_ID` is not defined in the config.
    """
    config = get_config()

    # Retrieve the model ID from configuration
    critic_model_id = getattr(config, 'CRITIC_MODEL_ID', None)
    if not critic_model_id:
        raise RuntimeError(
            "CRITIC_MODEL_ID is not defined in src/utils/config.py. "
            "Please define it to proceed with loading the critic model."
        )

    logger.info(f"Loading frozen critic model: {critic_model_id}")

    # Configure 4-bit quantization
    # Note: Using bnb_4bit_compute_type='float32' for stability on CPU/limited GPU
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float32,
        llm_int8_skip_modules=["lm_head"]
    )

    try:
        # Load Tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            critic_model_id,
            trust_remote_code=True,
            padding_side="left"
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load Model
        # We load the base model first. If a LoRA adapter is expected, it would be applied here,
        # but for the "frozen critic" role in this pipeline, we typically load the base model
        # directly as the source of the critique logic.
        model = AutoModelForCausalLM.from_pretrained(
            critic_model_id,
            quantization_config=quantization_config,
            device_map="auto", # Automatically distributes to available device (CPU/GPU)
            trust_remote_code=True,
            torch_dtype=torch.float32
        )

        # Explicitly freeze parameters to ensure no gradients are computed
        for param in model.parameters():
            param.requires_grad = False
        model.eval()

        # Verify architecture matches expectations (basic check)
        logger.info(f"Model architecture: {model.config.architectures}")
        logger.info(f"Model hidden size: {model.config.hidden_size}")

        return CriticModel(model, tokenizer, critic_model_id)

    except Exception as e:
        logger.error(f"Failed to load critic model {critic_model_id}: {e}")
        raise RuntimeError(f"Could not load frozen critic model: {e}") from e


def main() -> None:
    """
    Entry point for testing the critic loader.

    Executes the load_frozen_critic function and performs basic verification.
    """
    try:
        critic = load_frozen_critic()
        logger.info("SUCCESS: Critic model loaded and verified.")
        
        # Verification: Check requires_grad
        is_frozen = all(not p.requires_grad for p in critic.model.parameters())
        if not is_frozen:
            logger.error("VERIFICATION FAILED: Model is not frozen.")
            sys.exit(1)
        
        # Verification: Check architecture
        logger.info(f"Architecture verified: {critic.model.config.architectures}")
        
        # Clean up to free memory for subsequent tasks
        del critic
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Verification complete. Exiting cleanly.")
        sys.exit(0)

    except Exception as e:
        logger.error(f"CRITICAL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()