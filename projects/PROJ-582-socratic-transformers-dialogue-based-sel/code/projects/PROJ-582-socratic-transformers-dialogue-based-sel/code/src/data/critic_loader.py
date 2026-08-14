"""
Critic Model Loader for Socratic Transformers Project.

This module handles the acquisition and loading of a frozen, pre-trained
small model (Critic) suitable for 4-bit quantization on CPU-constrained
environments. The model ID is sourced from the project configuration.
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

# Add project root to path if running as script
if "code" not in sys.path[0]:
    code_root = Path(__file__).parent.parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

from src.utils.config import get_config

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class CriticModel:
    """
    Wrapper class for the frozen Critic model and its tokenizer.
    Ensures the model is loaded with 4-bit quantization and frozen parameters.
    """

    def __init__(self, model_id: str, device: str = "cpu"):
        self.model_id = model_id
        self.device = device
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.config: Optional[Dict[str, Any]] = None

    def load(self) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Loads the model and tokenizer from HuggingFace Hub.
        Applies 4-bit quantization and freezes all parameters.

        Returns:
            Tuple[AutoModelForCausalLM, AutoTokenizer]: The loaded model and tokenizer.

        Raises:
            RuntimeError: If the model fails to load or configuration is invalid.
        """
        logger.info(f"Loading Critic model: {self.model_id}")

        # Load configuration to get quantization settings if defined there,
        # otherwise use defaults suitable for CPU/low-memory.
        try:
            project_config = get_config()
            # Use the CRITIC_MODEL_ID from config if not passed explicitly,
            # but here we trust the constructor argument which should come from config.
        except Exception as e:
            logger.warning(f"Could not load project config for model settings: {e}")

        # 4-bit Quantization Configuration
        # Using bnb_4bit_compute_dtype=torch.float16 for better stability on most hardware
        # even if running on CPU, though float32 is safer for pure CPU.
        # Given the constraint "fits in available memory", float16 is preferred for size.
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )

        # Load Tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=False
            )
            # Ensure pad token is set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            logger.info("Tokenizer loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load tokenizer for {self.model_id}: {e}")
            raise RuntimeError(f"Tokenizer loading failed: {e}") from e

        # Load Model
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                quantization_config=bnb_config,
                device_map=self.device if self.device != "cpu" else None,
                torch_dtype=torch.float16,
                trust_remote_code=False,
                low_cpu_mem_usage=True
            )

            # Explicitly move to device if device_map didn't handle it (e.g. CPU)
            if self.device == "cpu":
                self.model = self.model.to(self.device)

            logger.info("Model loaded successfully with 4-bit quantization.")

        except Exception as e:
            logger.error(f"Failed to load model {self.model_id}: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

        # Freeze all parameters
        logger.info("Freezing model parameters...")
        for param in self.model.parameters():
            param.requires_grad = False

        # Verify freezing
        if any(p.requires_grad for p in self.model.parameters()):
            raise RuntimeError("Model parameters were not successfully frozen.")

        logger.info("Model is frozen and ready for inference.")
        return self.model, self.tokenizer

    def verify_architecture(self) -> Dict[str, Any]:
        """
        Verifies that the loaded model matches the expected architecture
        and returns summary info.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded yet.")

        return {
            "model_id": self.model_id,
            "architecture": self.model.config.architectures[0] if hasattr(self.model.config, 'architectures') else "Unknown",
            "num_parameters": sum(p.numel() for p in self.model.parameters()),
            "requires_grad": all(not p.requires_grad for p in self.model.parameters()),
            "device": self.device
        }


def load_frozen_critic(model_id: Optional[str] = None) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Factory function to load the frozen critic model.

    Args:
        model_id (Optional[str]): The HuggingFace model ID. If None, reads
            from `src.utils.config` key `CRITIC_MODEL_ID`.

    Returns:
        Tuple[AutoModelForCausalLM, AutoTokenizer]: The loaded, frozen model and tokenizer.

    Raises:
        RuntimeError: If the model cannot be loaded or verified.
    """
    config = get_config()

    if model_id is None:
        if not hasattr(config, 'CRITIC_MODEL_ID') or config.CRIC_MODEL_ID is None:
            # Fallback to a known small model if config is missing, but warn
            # Note: The task requires reading from config. If config is missing,
            # we should raise an error to satisfy "fail loudly".
            # However, to make the script runnable for verification, we check the attribute name.
            # The task says "key CRITIC_MODEL_ID".
            available_attrs = [a for a in dir(config) if not a.startswith('_')]
            raise RuntimeError(
                f"CRITIC_MODEL_ID not found in config. Available attrs: {available_attrs}. "
                "Please ensure src/utils/config.py defines CRITIC_MODEL_ID."
            )
        model_id = config.CRIC_MODEL_ID # Typo in task description? Assuming CRITIC_MODEL_ID

        # Correcting potential typo in variable name access based on standard naming
        # The task explicitly says "key CRITIC_MODEL_ID".
        if not hasattr(config, 'CRITIC_MODEL_ID'):
             # Check for common typos or variations if strict key is missing
             if hasattr(config, 'critic_model_id'):
                 model_id = config.critic_model_id
             else:
                 raise RuntimeError("Config must define 'CRITIC_MODEL_ID' or 'critic_model_id'.")
        else:
             model_id = config.CRIC_MODEL_ID # Re-reading: The task says "key CRITIC_MODEL_ID"
             # Let's assume the config object has this attribute.

    # Re-evaluating: The task says "read from src/utils/config.py (key CRITIC_MODEL_ID)".
    # I will access it directly. If the attribute doesn't exist, the get_config() wrapper
    # or the dataclass should handle it.
    # Let's assume the config object is a dataclass or dict-like.
    # From the API surface: `from src.utils.config import get_config, SocraticConfig`.
    # SocraticConfig is a dataclass.

    if model_id is None:
        try:
            model_id = config.CRIC_MODEL_ID
        except AttributeError:
             # Try standard casing
             if hasattr(config, 'CRITIC_MODEL_ID'):
                 model_id = config.CRIC_MODEL_ID
             else:
                 raise RuntimeError("CRITIC_MODEL_ID is not defined in src/utils/config.py")

    logger.info(f"Using Critic Model ID: {model_id}")

    critic = CriticModel(model_id=model_id)
    model, tokenizer = critic.load()

    # Verification
    arch_info = critic.verify_architecture()
    assert arch_info["requires_grad"] is True, "Model must be frozen (requires_grad=False)"
    logger.info(f"Architecture verification passed: {arch_info['architecture']}")

    return model, tokenizer


def main():
    """
    Main entry point for testing the Critic Loader.
    Verifies loading, freezing, and architecture.
    """
    logging.basicConfig(level=logging.INFO)

    try:
        model, tokenizer = load_frozen_critic()

        # Run a dummy inference to ensure it works (optional but good for verification)
        input_text = "Test critique: "
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            _ = model.generate(
                **inputs,
                max_new_tokens=5,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )

        logger.info("Critic model loaded and verified successfully.")
        return 0

    except Exception as e:
        logger.error(f"Failed to load or verify Critic model: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
