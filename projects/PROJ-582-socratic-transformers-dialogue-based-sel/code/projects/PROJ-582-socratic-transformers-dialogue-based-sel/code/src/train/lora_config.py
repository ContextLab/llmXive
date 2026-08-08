"""
LoRA Configuration Module for Socratic Transformers.

This module defines the configuration class and factory functions for setting up
Low-Rank Adaptation (LoRA) parameters and 4-bit quantization settings required
for CPU-constrained fine-tuning (FR-003).

Dependencies:
    - peft: For LoraConfig
    - transformers: For BitsAndBytesConfig
    - src.utils.config: For SocraticConfig
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
    Configuration container for LoRA fine-tuning parameters.

    Attributes:
        r (int): Rank of the update matrices.
        lora_alpha (int): Alpha scaling factor for LoRA.
        lora_dropout (float): Dropout probability for LoRA layers.
        target_modules (list[str]): List of module names to apply LoRA to.
        task_type (str): Task type for PEFT (e.g., CAUSAL_LM).
        bias (str): Bias type for LoRA (none, lora_only, all).
        modules_to_save (list[str], optional): Modules to be trained from scratch.
    """
    r: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: list = field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"]
    )
    task_type: str = "CAUSAL_LM"
    bias: str = "none"
    modules_to_save: Optional[list] = None

    def to_peft_config(self) -> LoraConfig:
        """
        Converts this configuration into a PEFT LoraConfig object.

        Returns:
            LoraConfig: Configured PEFT instance ready for model attachment.
        """
        task_type_enum = TaskType.CAUSAL_LM if self.task_type == "CAUSAL_LM" else None

        return LoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            task_type=task_type_enum,
            bias=self.bias,
            modules_to_save=self.modules_to_save,
        )


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Creates a BitsAndBytesConfig for 4-bit quantization (NF4) with CPU compatibility.

    This satisfies FR-003 requirement for 4-bit quantization to reduce memory footprint
    on constrained hardware.

    Returns:
        BitsAndBytesConfig: Configuration for 4-bit loading.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype="float32", # Use float32 for CPU stability
        llm_int8_threshold=6.0,
    )


def create_lora_config_from_env() -> Tuple[LoRAConfig, BitsAndBytesConfig]:
    """
    Reads LoRA and quantization settings from environment variables.

    Environment Variables:
        LORA_R: Rank (default: 8)
        LORA_ALPHA: Alpha (default: 32)
        LORA_DROPOUT: Dropout (default: 0.1)
        BATCH_SIZE: Per-device batch size (must be <= 2 for CPU constraints)
        GRAD_ACCUMULATION: Gradient accumulation steps (default: 4)

    Returns:
        Tuple[LoRAConfig, BitsAndBytesConfig]: Configured LoRA and Quantization objects.
    """
    # Parse LoRA parameters from environment
    r = int(os.getenv("LORA_R", 8))
    lora_alpha = int(os.getenv("LORA_ALPHA", 32))
    lora_dropout = float(os.getenv("LORA_DROPOUT", 0.1))
    batch_size = int(os.getenv("BATCH_SIZE", 2))
    grad_accum = int(os.getenv("GRAD_ACCUMULATION", 4))

    # Enforce CPU constraints from task description
    if batch_size > 2:
        raise ValueError(f"BATCH_SIZE must be <= 2 for CPU constraints. Got {batch_size}")
    if grad_accum < 4:
        raise ValueError(f"GRAD_ACCUMULATION must be >= 4 to compensate for small batch. Got {grad_accum}")

    lora_cfg = LoRAConfig(
        r=r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
    )

    quant_cfg = get_4bit_quantization_config()

    return lora_cfg, quant_cfg


def validate_lora_config(lora_cfg: LoRAConfig, quant_cfg: BitsAndBytesConfig) -> bool:
    """
    Validates that the configuration meets project constraints (FR-003).

    Checks:
        - 4-bit quantization is enabled.
        - Target modules are specified.

    Args:
        lora_cfg: LoRA configuration object.
        quant_cfg: Quantization configuration object.

    Returns:
        bool: True if valid.

    Raises:
        ValueError: If configuration violates constraints.
    """
    if not quant_cfg.load_in_4bit:
        raise ValueError("4-bit quantization must be enabled (load_in_4bit=True).")

    if not lora_cfg.target_modules:
        raise ValueError("target_modules must be specified for LoRA.")

    return True


def main() -> None:
    """
    Entry point for CLI testing of LoRA configuration.
    Prints the generated configuration to stdout.
    """
    print("Initializing LoRA Configuration for Socratic Transformers...")
    try:
        lora_cfg, quant_cfg = create_lora_config_from_env()
        validate_lora_config(lora_cfg, quant_cfg)

        print(f"LoRA Config: r={lora_cfg.r}, alpha={lora_cfg.lora_alpha}, dropout={lora_cfg.lora_dropout}")
        print(f"Target Modules: {lora_cfg.target_modules}")
        print(f"Quantization: 4-bit enabled={quant_cfg.load_in_4bit}, type={quant_cfg.bnb_4bit_quant_type}")
        print("Configuration validated successfully.")
    except Exception as e:
        print(f"Configuration Error: {e}")
        raise


if __name__ == "__main__":
    main()