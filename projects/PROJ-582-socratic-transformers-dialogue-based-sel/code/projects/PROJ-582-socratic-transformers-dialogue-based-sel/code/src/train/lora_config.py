"""
LoRA Configuration Module for Socratic Transformers.

Implements FR-003: CPU-constrained fine-tuning configuration with:
- batch_size <= 2
- gradient_accumulation_steps = 4
- 4-bit quantization via bitsandbytes
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
    Enforces CPU-constrained limits as per FR-003.
    """
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list = field(default_factory=lambda: ["q_proj", "v_proj"])
    task_type: str = "CAUSAL_LM"
    bias: str = "none"
    fan_in_fan_out: bool = False
    enable_lora: Optional[list] = None

    # Training constraints (FR-003)
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    max_seq_length: int = 512
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_steps: int = 100
    num_train_epochs: int = 3
    save_steps: int = 500
    logging_steps: int = 10
    output_dir: str = "data/results"

    # Quantization settings
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True
    llm_int8_threshold: float = 6.0

    def __post_init__(self):
        """Validate constraints after initialization."""
        if self.batch_size > 2:
            raise ValueError(f"batch_size must be <= 2 for CPU constraints (FR-003), got {self.batch_size}")
        if self.gradient_accumulation_steps != 4:
            raise ValueError(f"gradient_accumulation_steps must be 4 for CPU constraints (FR-003), got {self.gradient_accumulation_steps}")

    def to_peft_config(self) -> LoraConfig:
        """Convert to PEFT LoraConfig object."""
        return LoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            task_type=TaskType.CAUSAL_LM if self.task_type == "CAUSAL_LM" else TaskType.SEQ_2_SEQ_LM,
            bias=self.bias,
            fan_in_fan_out=self.fan_in_fan_out,
            enable_lora=self.enable_lora,
        )

    def to_transformers_quant_config(self) -> BitsAndBytesConfig:
        """Convert to HuggingFace BitsAndBytesConfig for 4-bit quantization."""
        compute_dtype_map = {
            "float16": "float16",
            "float32": "float32",
            "bfloat16": "bfloat16",
        }
        compute_dtype = compute_dtype_map.get(self.bnb_4bit_compute_dtype, "float16")

        return BitsAndBytesConfig(
            load_in_4bit=self.load_in_4bit,
            bnb_4bit_quant_type=self.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=self.bnb_4bit_use_double_quant,
            llm_int8_threshold=self.llm_int8_threshold,
            llm_int8_has_fp16_weight=False,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging/checkpointing."""
        return {
            "lora": {
                "r": self.r,
                "lora_alpha": self.lora_alpha,
                "lora_dropout": self.lora_dropout,
                "target_modules": self.target_modules,
                "task_type": self.task_type,
                "bias": self.bias,
            },
            "training": {
                "batch_size": self.batch_size,
                "gradient_accumulation_steps": self.gradient_accumulation_steps,
                "max_seq_length": self.max_seq_length,
                "learning_rate": self.learning_rate,
                "weight_decay": self.weight_decay,
                "warmup_steps": self.warmup_steps,
                "num_train_epochs": self.num_train_epochs,
                "save_steps": self.save_steps,
                "logging_steps": self.logging_steps,
                "output_dir": self.output_dir,
            },
            "quantization": {
                "load_in_4bit": self.load_in_4bit,
                "bnb_4bit_quant_type": self.bnb_4bit_quant_type,
                "bnb_4bit_compute_dtype": self.bnb_4bit_compute_dtype,
                "bnb_4bit_use_double_quant": self.bnb_4bit_use_double_quant,
                "llm_int8_threshold": self.llm_int8_threshold,
            },
        }


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Factory function to create the 4-bit quantization config.
    Uses defaults from LoRAConfig but can be overridden by environment.
    """
    config = LoRAConfig()
    return config.to_transformers_quant_config()


def create_lora_config_from_env() -> LoRAConfig:
    """
    Create LoRAConfig from environment variables if present, otherwise defaults.
    """
    config = LoRAConfig()

    # Override with environment variables if present
    if os.getenv("LORA_R"):
        config.r = int(os.getenv("LORA_R"))
    if os.getenv("LORA_ALPHA"):
        config.lora_alpha = int(os.getenv("LORA_ALPHA"))
    if os.getenv("LORA_DROPOUT"):
        config.lora_dropout = float(os.getenv("LORA_DROPOUT"))
    if os.getenv("TARGET_MODULES"):
        config.target_modules = os.getenv("TARGET_MODULES").split(",")
    if os.getenv("BATCH_SIZE"):
        batch_size = int(os.getenv("BATCH_SIZE"))
        if batch_size > 2:
            raise ValueError(f"Environment BATCH_SIZE must be <= 2 for CPU constraints (FR-003), got {batch_size}")
        config.batch_size = batch_size
    if os.getenv("GRADIENT_ACCUMULATION_STEPS"):
        grad_acc = int(os.getenv("GRADIENT_ACCUMULATION_STEPS"))
        if grad_acc != 4:
            raise ValueError(f"Environment GRADIENT_ACCUMULATION_STEPS must be 4 for CPU constraints (FR-003), got {grad_acc}")
        config.gradient_accumulation_steps = grad_acc
    if os.getenv("LEARNING_RATE"):
        config.learning_rate = float(os.getenv("LEARNING_RATE"))
    if os.getenv("OUTPUT_DIR"):
        config.output_dir = os.getenv("OUTPUT_DIR")

    return config


def validate_lora_config(config: LoRAConfig) -> Tuple[bool, str]:
    """
    Validate that the LoRAConfig meets all CPU constraints.
    Returns (is_valid, error_message).
    """
    errors = []

    if config.batch_size > 2:
        errors.append(f"batch_size ({config.batch_size}) must be <= 2")
    if config.gradient_accumulation_steps != 4:
        errors.append(f"gradient_accumulation_steps ({config.gradient_accumulation_steps}) must be 4")
    if not config.load_in_4bit:
        errors.append("load_in_4bit must be True for CPU constraints")

    if errors:
        return False, "; ".join(errors)
    return True, "Valid"


def main():
    """Main entry point for testing/validating LoRA configuration."""
    print("Testing LoRA configuration...")

    # Test default configuration
    try:
        config = LoRAConfig()
        print(f"✓ Default config created: batch_size={config.batch_size}, grad_acc={config.gradient_accumulation_steps}")

        # Validate
        is_valid, msg = validate_lora_config(config)
        if is_valid:
            print(f"✓ Configuration validation passed: {msg}")
        else:
            print(f"✗ Configuration validation failed: {msg}")
            return 1

        # Test PEFT config conversion
        peft_config = config.to_peft_config()
        print(f"✓ PEFT config created: r={peft_config.r}, lora_alpha={peft_config.lora_alpha}")

        # Test quantization config conversion
        quant_config = config.to_transformers_quant_config()
        print(f"✓ Quantization config created: load_in_4bit={quant_config.load_in_4bit}")

        # Test environment-based config
        env_config = create_lora_config_from_env()
        print(f"✓ Environment config created: batch_size={env_config.batch_size}")

        # Test dict conversion
        config_dict = config.to_dict()
        print(f"✓ Config dict created with {len(config_dict)} sections")

        print("\n✓ All LoRA configuration tests passed!")
        return 0

    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())