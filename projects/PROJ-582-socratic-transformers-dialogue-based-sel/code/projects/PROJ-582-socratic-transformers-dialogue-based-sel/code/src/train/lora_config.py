"""
LoRA Configuration Module for Socratic Transformers.

Implements configuration for Low-Rank Adaptation (LoRA) with 4-bit quantization
to ensure training fits within CPU memory constraints (< 7GB) as per FR-003.
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
    Configuration dataclass for LoRA fine-tuning parameters.

    Attributes:
        r: Rank of the LoRA update matrices.
        lora_alpha: Scaling factor for LoRA updates.
        lora_dropout: Dropout probability for LoRA layers.
        target_modules: List of module names to apply LoRA to.
        task_type: Type of task for PEFT (CAUSAL_LM for generative models).
        bias: Bias type for LoRA.
        modules_to_save: List of modules to save in addition to LoRA.
    """
    r: int = 64
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: list = field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"]
    )
    task_type: str = "CAUSAL_LM"
    bias: str = "none"
    modules_to_save: Optional[list] = None

    def to_peft_config(self) -> LoraConfig:
        """Convert this configuration to a PEFT LoraConfig object."""
        return LoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            task_type=TaskType[self.task_type],
            bias=self.bias,
            modules_to_save=self.modules_to_save,
        )


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Create a 4-bit quantization configuration using BitsAndBytes.

    Returns:
        BitsAndBytesConfig: Configuration for 4-bit quantization optimized for CPU.
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype="float32",  # Use float32 for CPU stability
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        llm_int8_threshold=6.0,
        llm_int8_has_fp16_weight=False,
    )


def create_lora_config_from_env() -> Tuple[LoRAConfig, BitsAndBytesConfig]:
    """
    Create LoRA and quantization configurations from environment variables.

    Returns:
        Tuple containing LoRAConfig and BitsAndBytesConfig instances.
    """
    # Get base config from environment
    base_config = get_config()

    # Extract LoRA parameters from environment or use defaults
    r = int(os.environ.get("LORA_R", 64))
    lora_alpha = int(os.environ.get("LORA_ALPHA", 16))
    lora_dropout = float(os.environ.get("LORA_DROPOUT", 0.1))

    # Parse target modules from environment
    target_modules_str = os.environ.get(
        "LORA_TARGET_MODULES", "q_proj,k_proj,v_proj,o_proj"
    )
    target_modules = [m.strip() for m in target_modules_str.split(",")]

    # Create LoRA configuration
    lora_config = LoRAConfig(
        r=r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=target_modules,
    )

    # Create quantization config
    quant_config = get_4bit_quantization_config()

    return lora_config, quant_config


def validate_lora_config(
    lora_config: LoRAConfig, quant_config: BitsAndBytesConfig
) -> bool:
    """
    Validate LoRA configuration against project constraints.

    Args:
        lora_config: LoRA configuration to validate.
        quant_config: Quantization configuration to validate.

    Returns:
        bool: True if configuration is valid, False otherwise.

    Raises:
        ValueError: If configuration violates constraints.
    """
    # Validate batch size constraint (FR-003)
    batch_size = int(os.environ.get("TRAIN_BATCH_SIZE", 2))
    if batch_size > 2:
        raise ValueError(
            f"Batch size {batch_size} exceeds maximum of 2 per FR-003"
        )

    # Validate gradient accumulation steps (FR-003)
    grad_accum = int(os.environ.get("GRADIENT_ACCUMULATION_STEPS", 4))
    if grad_accum < 4:
        raise ValueError(
            f"Gradient accumulation steps {grad_accum} must be at least 4 per FR-003"
        )

    # Validate 4-bit quantization is enabled
    if not quant_config.load_in_4bit:
        raise ValueError("4-bit quantization must be enabled per FR-003")

    # Validate LoRA parameters
    if lora_config.r <= 0:
        raise ValueError(f"LoRA rank must be positive, got {lora_config.r}")

    if lora_config.lora_alpha <= 0:
        raise ValueError(f"LoRA alpha must be positive, got {lora_config.lora_alpha}")

    if not 0 <= lora_config.lora_dropout <= 1:
        raise ValueError(
            f"LoRA dropout must be between 0 and 1, got {lora_config.lora_dropout}"
        )

    return True


def main() -> None:
    """
    Main function to demonstrate LoRA configuration creation and validation.
    """
    print("Creating LoRA configuration...")

    # Create configurations
    lora_config, quant_config = create_lora_config_from_env()

    # Validate configuration
    try:
        is_valid = validate_lora_config(lora_config, quant_config)
        print(f"Configuration validation: {'PASSED' if is_valid else 'FAILED'}")
    except ValueError as e:
        print(f"Configuration validation FAILED: {e}")
        return

    # Display configuration details
    print("\n=== LoRA Configuration ===")
    print(f"Rank (r): {lora_config.r}")
    print(f"Alpha: {lora_config.lora_alpha}")
    print(f"Dropout: {lora_config.lora_dropout}")
    print(f"Target Modules: {lora_config.target_modules}")
    print(f"Task Type: {lora_config.task_type}")

    print("\n=== Quantization Configuration ===")
    print(f"4-bit Load: {quant_config.load_in_4bit}")
    print(f"Compute Dtype: {quant_config.bnb_4bit_compute_dtype}")
    print(f"Double Quant: {quant_config.bnb_4bit_use_double_quant}")
    print(f"Quant Type: {quant_config.bnb_4bit_quant_type}")

    # Convert to PEFT config
    peft_config = lora_config.to_peft_config()
    print(f"\nPEFT Config Type: {type(peft_config).__name__}")

    print("\nConfiguration ready for training.")


if __name__ == "__main__":
    main()
