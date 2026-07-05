"""
LoRA configuration module for CPU-constrained fine-tuning.

Implements FR-003:
- batch_size <= 2
- gradient_accumulation_steps = 4
- 4-bit quantization support

This module provides configuration objects compatible with PEFT and transformers
for low-resource fine-tuning scenarios.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from peft import LoraConfig, TaskType
from transformers import BitsAndBytesConfig

from src.utils.config import get_config


@dataclass
class LoRAConfig:
    """
    Configuration for Low-Rank Adaptation (LoRA) fine-tuning.

    Attributes:
        r: Rank of the update matrices (default: 8)
        lora_alpha: Alpha scaling factor for LoRA (default: 16)
        lora_dropout: Dropout rate for LoRA layers (default: 0.1)
        target_modules: List of module names to apply LoRA to (default: all linear)
        task_type: Task type for PEFT (default: CAUSAL_LM)
        batch_size: Training batch size (max 2 for CPU constraints)
        gradient_accumulation_steps: Steps for gradient accumulation (default: 4)
        use_4bit: Whether to enable 4-bit quantization (default: True)
        quantization_type: Quantization type ('nf4' or 'fp4')
        bnb_4bit_compute_dtype: Compute dtype for 4-bit quantization
        bnb_4bit_quant_storage: Storage dtype for quantized weights
        max_seq_length: Maximum sequence length for training
    """
    r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    target_modules: list = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    task_type: str = "CAUSAL_LM"
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    use_4bit: bool = True
    quantization_type: str = "nf4"
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_storage: str = "uint8"
    max_seq_length: int = 512

    def __post_init__(self):
        """Validate configuration constraints."""
        if self.batch_size > 2:
            raise ValueError(f"batch_size must be <= 2 for CPU constraints, got {self.batch_size}")
        if self.gradient_accumulation_steps != 4:
            raise ValueError(f"gradient_accumulation_steps must be 4, got {self.gradient_accumulation_steps}")

    def get_peft_config(self) -> LoraConfig:
        """
        Create and return a PEFT LoraConfig instance.

        Returns:
            LoraConfig: Configured LoRA parameters for fine-tuning.
        """
        return LoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            task_type=TaskType.CAUSAL_LM if self.task_type == "CAUSAL_LM" else None,
            bias="none"
        )

    def get_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """
        Create and return a BitsAndBytesConfig for 4-bit quantization.

        Returns:
            BitsAndBytesConfig: Quantization configuration, or None if 4-bit disabled.
        """
        if not self.use_4bit:
            return None

        compute_dtype_map = {
            "float16": "float16",
            "float32": "float32",
            "bfloat16": "bfloat16"
        }

        compute_dtype = getattr(__import__("torch"), self.bnb_4bit_compute_dtype)
        quant_storage = getattr(__import__("torch"), self.bnb_4bit_quant_storage)

        return BitsAndBytesConfig(
            load_in_4bit=self.use_4bit,
            bnb_4bit_quant_type=self.quantization_type,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_quant_storage=quant_storage,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the configuration.
        """
        return {
            "r": self.r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "target_modules": self.target_modules,
            "task_type": self.task_type,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "use_4bit": self.use_4bit,
            "quantization_type": self.quantization_type,
            "bnb_4bit_compute_dtype": self.bnb_4bit_compute_dtype,
            "bnb_4bit_quant_storage": self.bnb_4bit_quant_storage,
            "max_seq_length": self.max_seq_length
        }


def create_lora_config_from_env() -> LoRAConfig:
    """
    Create a LoRAConfig instance from environment variables or defaults.

    Uses the project's global configuration if available, otherwise falls back
    to FR-003 compliant defaults.

    Returns:
        LoRAConfig: Configured LoRA parameters.
    """
    try:
        global_config = get_config()
        # Override with global config values if available
        return LoRAConfig(
            r=getattr(global_config, 'lora_r', 8),
            lora_alpha=getattr(global_config, 'lora_alpha', 16),
            lora_dropout=getattr(global_config, 'lora_dropout', 0.1),
            batch_size=getattr(global_config, 'train_batch_size', 2),
            gradient_accumulation_steps=getattr(global_config, 'gradient_accumulation_steps', 4),
            max_seq_length=getattr(global_config, 'max_seq_length', 512)
        )
    except Exception:
        # Fall back to FR-003 compliant defaults
        return LoRAConfig(
            batch_size=2,
            gradient_accumulation_steps=4,
            use_4bit=True
        )


def validate_lora_config(config: LoRAConfig) -> bool:
    """
    Validate that a LoRAConfig meets all CPU-constraint requirements.

    Args:
        config: LoRAConfig instance to validate.

    Returns:
        bool: True if configuration is valid, False otherwise.
    """
    if config.batch_size > 2:
        return False
    if config.gradient_accumulation_steps != 4:
        return False
    if config.use_4bit and config.quantization_type not in ["nf4", "fp4"]:
        return False
    return True


if __name__ == "__main__":
    # Test the configuration creation and validation
    import json

    config = create_lora_config_from_env()
    print("LoRA Configuration:")
    print(json.dumps(config.to_dict(), indent=2))

    print("\nValidation Result:", validate_lora_config(config))

    # Test PEFT config generation
    peft_cfg = config.get_peft_config()
    print(f"\nPEFT Config created: r={peft_cfg.r}, alpha={peft_cfg.lora_alpha}")

    # Test quantization config generation
    if config.use_4bit:
        quant_cfg = config.get_quantization_config()
        print(f"Quantization enabled: type={config.quantization_type}, compute_dtype={config.bnb_4bit_compute_dtype}")