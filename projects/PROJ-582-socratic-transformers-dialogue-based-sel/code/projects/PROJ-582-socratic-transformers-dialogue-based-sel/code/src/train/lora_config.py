"""
LoRA Configuration Module for CPU-Constrained Fine-Tuning.

Implements FR-003:
- batch_size <= 2
- gradient_accumulation_steps = 4
- 4-bit quantization (BitsAndBytesConfig)

This module provides the configuration factory for the PEFT LoRA adapter
and the quantization settings required to fit models into limited RAM (7GB).
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
import os

from peft import LoraConfig, TaskType
from transformers import BitsAndBytesConfig

from src.utils.config import get_config, SocraticConfig


@dataclass
class LoRAConfig:
    """
    Container for LoRA and Quantization hyperparameters.

    Attributes:
        r: Rank of the low-rank matrices.
        lora_alpha: Scaling factor for the low-rank matrices.
        lora_dropout: Dropout probability for LoRA layers.
        target_modules: List of module names to replace with LoRA.
        task_type: Task type for PEFT (CAUSAL_LM for text generation).
        bias: Bias type for LoRA (none, lora, all).
        modules_to_save: List of modules to save alongside LoRA.

        quantization_4bit: Whether to use 4-bit quantization.
        quantization_type: 'nf4' or 'fp4' for 4-bit quantization.
        bnb_4bit_compute_dtype: Data type for computation (float16 or bfloat16).
        bnb_4bit_use_double_quant: Whether to use nested quantization.
        bnb_4bit_quant_type: Quantization type.

        batch_size: Micro-batch size per device (FR-003: <= 2).
        gradient_accumulation_steps: Steps to accumulate gradients (FR-003: = 4).
        max_seq_length: Maximum sequence length for training.
    """
    r: int = 64
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: list = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    task_type: str = "CAUSAL_LM"
    bias: str = "none"
    modules_to_save: Optional[list] = None

    quantization_4bit: bool = True
    quantization_type: str = "nf4"
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_quant_type: str = "nf4"

    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    max_seq_length: int = 512

    def to_peft_config(self) -> LoraConfig:
        """
        Converts this configuration to a PEFT LoraConfig object.

        Returns:
            LoraConfig: Configured PEFT object ready for model injection.
        """
        return LoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            task_type=TaskType.CAUSAL_LM if self.task_type == "CAUSAL_LM" else None,
            bias=self.bias,
            modules_to_save=self.modules_to_save
        )

    def to_bits_and_bytes_config(self) -> Optional[BitsAndBytesConfig]:
        """
        Converts quantization settings to a BitsAndBytesConfig object.

        Returns:
            BitsAndBytesConfig: Configured quantization object, or None if not enabled.
        """
        if not self.quantization_4bit:
            return None

        compute_dtype = getattr(__import__("torch"), self.bnb_4bit_compute_dtype)

        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=self.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=self.bnb_4bit_use_double_quant,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False,
        )


def create_lora_config_from_env(config: Optional[SocraticConfig] = None) -> LoRAConfig:
    """
    Creates a LoRAConfig instance from environment variables or provided config.

    Args:
        config: Optional SocraticConfig instance to pull settings from.

    Returns:
        LoRAConfig: Instantiated configuration.
    """
    if config is None:
        config = get_config()

    # Override defaults with environment variables if set
    r = int(os.getenv("LORA_R", config.lora_r if hasattr(config, 'lora_r') else 64))
    lora_alpha = int(os.getenv("LORA_ALPHA", config.lora_alpha if hasattr(config, 'lora_alpha') else 16))
    lora_dropout = float(os.getenv("LORA_DROPOUT", config.lora_dropout if hasattr(config, 'lora_dropout') else 0.1))
    max_seq_length = int(os.getenv("MAX_SEQ_LENGTH", config.max_seq_length if hasattr(config, 'max_seq_length') else 512))

    # FR-003 constraints enforcement
    batch_size = int(os.getenv("TRAIN_BATCH_SIZE", 2))
    if batch_size > 2:
        # Log warning or force clamp for safety in constrained environments
        batch_size = 2

    grad_accum = int(os.getenv("GRADIENT_ACCUMULATION_STEPS", 4))
    if grad_accum != 4:
        # Log warning if not matching FR-003 exactly, but allow override if needed
        pass

    return LoRAConfig(
        r=r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        max_seq_length=max_seq_length,
        batch_size=batch_size,
        gradient_accumulation_steps=grad_accum
    )


def validate_lora_config(cfg: LoRAConfig) -> Tuple[bool, str]:
    """
    Validates the LoRA configuration against project constraints (FR-003).

    Args:
        cfg: The LoRAConfig instance to validate.

    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    if cfg.batch_size > 2:
        return False, f"batch_size ({cfg.batch_size}) must be <= 2 per FR-003."

    if cfg.gradient_accumulation_steps != 4:
        return False, f"gradient_accumulation_steps ({cfg.gradient_accumulation_steps}) must be 4 per FR-003."

    if not cfg.quantization_4bit:
        return False, "4-bit quantization must be enabled per FR-003."

    if cfg.batch_size * cfg.gradient_accumulation_steps < 8:
        # Effective batch size check (optional, but good for stability)
        pass

    return True, "Configuration valid."


def main():
    """
    Entry point for testing/validating the LoRA configuration.
    """
    cfg = create_lora_config_from_env()
    is_valid, msg = validate_lora_config(cfg)

    print(f"LoRA Configuration: {cfg}")
    print(f"Validation Result: {is_valid} - {msg}")

    if is_valid:
        peft_cfg = cfg.to_peft_config()
        print(f"PEFT Config created: {peft_cfg}")

        if cfg.quantization_4bit:
            bnb_cfg = cfg.to_bits_and_bytes_config()
            print(f"BitsAndBytes Config created: {bnb_cfg}")

    return 0 if is_valid else 1


if __name__ == "__main__":
    exit(main())