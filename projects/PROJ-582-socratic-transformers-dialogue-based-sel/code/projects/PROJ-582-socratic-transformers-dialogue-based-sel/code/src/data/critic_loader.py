"""
Frozen Critic Model Loader for Socratic Transformers Project.

This module implements the loading of a frozen, pre-trained small model
with 4-bit quantization, configured via the project's central config.
It serves as the adversarial critique mechanism for identifying logical
contradictions (FR-002).
"""
import gc
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# Add project root to path for imports if running as script
if "code" in os.getcwd():
    sys.path.insert(0, os.getcwd())
else:
    # Handle relative import context
    current_dir = Path(__file__).resolve()
    project_root = current_dir.parents[2]
    sys.path.insert(0, str(project_root))

from src.utils.config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Constructs the 4-bit quantization configuration for memory efficiency.

    Returns:
        BitsAndBytesConfig: Configuration object for 4-bit loading.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        llm_int8_enable_fp32_cpu_offload=True, # Enable CPU offload for safety on constrained RAM
    )


class CriticModel:
    """
    Wrapper for the frozen critic model to manage lifecycle and inference.
    """
    def __init__(self, model: AutoModelForCausalLM, tokenizer: AutoTokenizer, model_id: str):
        self.model = model
        self.tokenizer = tokenizer
        self.model_id = model_id
        self._frozen = False

    def freeze(self):
        """Freeze all model parameters (requires_grad=False)."""
        if not self._frozen:
            for param in self.model.parameters():
                param.requires_grad = False
            self.model.eval()
            self._frozen = True
            logger.info(f"Model {self.model_id} frozen successfully.")

    def generate_critique(self, prompt: str, max_new_tokens: int = 256) -> str:
        """
        Generates a critique based on the provided prompt.

        Args:
            prompt (str): The input prompt containing the answer to critique.
            max_new_tokens (int): Maximum tokens to generate.

        Returns:
            str: The generated critique text.
        """
        if not self._frozen:
            self.freeze()

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False, # Deterministic for consistency
                temperature=0.7,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode and strip prompt
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        critique = generated_text[len(prompt):].strip()
        return critique


def load_frozen_critic(config: Optional[Dict[str, Any]] = None) -> CriticModel:
    """
    Loads the frozen critic model from HuggingFace using the configured ID.

    This function:
    1. Reads the CRITIC_MODEL_ID from the project config.
    2. Loads the model with 4-bit quantization to fit in memory.
    3. Freezes all parameters (requires_grad=False).
    4. Returns the wrapped CriticModel instance.

    Args:
        config (Optional[Dict]): Optional config dict. If None, loads global config.

    Returns:
        CriticModel: The loaded and frozen critic model.

    Raises:
        ValueError: If CRITIC_MODEL_ID is not set in config.
        RuntimeError: If model loading fails.
    """
    try:
        current_config = config or get_config()
        model_id = current_config.get("CRITIC_MODEL_ID")

        if not model_id:
            raise ValueError("CRITIC_MODEL_ID is not set in configuration. "
                             "Please set it in environment or config file.")

        logger.info(f"Loading frozen critic model: {model_id}")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            padding_side="left"
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load quantization config
        quant_config = get_4bit_quantization_config()

        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quant_config,
            device_map="auto", # Automatically handles CPU/GPU offloading
            trust_remote_code=True,
            torch_dtype=torch.float16
        )

        # Freeze the model immediately
        for param in model.parameters():
            param.requires_grad = False
        model.eval()

        logger.info(f"Model {model_id} loaded and frozen. Architecture: {model.config.architectures}")

        return CriticModel(model, tokenizer, model_id)

    except Exception as e:
        logger.error(f"Failed to load critic model: {e}")
        raise RuntimeError(f"Critical error loading critic model: {e}") from e


def main():
    """
    Entry point for testing the critic loader directly.
    Verifies loading, freezing, and basic architecture check.
    """
    try:
        logger.info("Starting Critic Loader verification...")
        critic = load_frozen_critic()

        # Verification steps
        assert critic._frozen, "Model should be frozen upon loading."
        assert all(not p.requires_grad for p in critic.model.parameters()), \
            "All parameters must have requires_grad=False."

        logger.info("Verification passed: Model is frozen and ready for inference.")
        logger.info(f"Model Architecture: {critic.model.config.architectures}")

        # Optional: Test a tiny generation if memory permits
        test_prompt = "Identify logical contradictions in: 2+2=5."
        logger.info(f"Running test inference with prompt: '{test_prompt}'")
        critique = critic.generate_critique(test_prompt, max_new_tokens=50)
        logger.info(f"Generated Critique: {critique}")

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)

    finally:
        # Clean up
        if 'critic' in locals():
            del critic
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()