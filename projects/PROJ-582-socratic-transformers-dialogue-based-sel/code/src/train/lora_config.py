"""
LoRA Configuration Module for Socratic Transformers.

Implements Low-Rank Adaptation (LoRA) configuration with 4-bit quantization
support for CPU-constrained fine-tuning as per FR-003.

Requirements:
- batch_size <= 2
- gradient_accumulation_steps = 4
- 4-bit quantization via bitsandbytes
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple

from peft import LoraConfig, TaskType
from transformers import BitsAndBytesConfig

from src.utils.config import get_config, SocraticConfig


@dataclass
class LoRAConfig:
    """
    Configuration container for LoRA fine-tuning parameters.

    Enforces FR-003 constraints:
    - batch_size <= 2
    - gradient_accumulation_steps = 4
    - 4-bit quantization
    """
    # LoRA specific parameters
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: list = field(default_factory=lambda: ["q_proj", "v_proj"])
    task_type: str = "CAUSAL_LM"

    # Training hyperparameters (FR-003 constraints)
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    max_steps: int = 1000  # Default safety limit
    save_steps: int = 100
    logging_steps: int = 10

    # Quantization settings
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float32"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True

    # Paths
    output_dir: str = "data/results/lora_checkpoint"
    model_id: Optional[str] = None

    def __post_init__(self):
        """Validate constraints immediately upon initialization."""
        if self.batch_size > 2:
            raise ValueError(f"FR-003 Violation: batch_size must be <= 2, got {self.batch_size}")
        if self.gradient_accumulation_steps != 4:
            raise ValueError(f"FR-003 Violation: gradient_accumulation_steps must be 4, got {self.gradient_accumulation_steps}")

    def to_peft_config(self) -> LoraConfig:
        """Convert to PEFT LoraConfig instance."""
        task_type_map = {
            "CAUSAL_LM": TaskType.CAUSAL_LM,
            "SEQ_2_SEQ_LM": TaskType.SEQ_2_SEQ_LM,
            "TOKEN_CLS": TaskType.TOKEN_CLS,
            "SEQ_CLS": TaskType.SEQ_CLS
        }

        return LoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            task_type=task_type_map.get(self.task_type, TaskType.CAUSAL_LM),
            bias="none",
            inference_mode=False
        )

    def to_quantization_config(self) -> Optional[BitsAndBytesConfig]:
        """Create BitsAndBytesConfig for 4-bit quantization."""
        if not self.use_4bit:
            return None

        compute_dtype = getattr(__import__('torch'), self.bnb_4bit_compute_dtype)

        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_quant_type=self.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=self.bnb_4bit_use_double_quant,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False
        )

    def to_training_args(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for HuggingFace TrainingArguments."""
        return {
            "output_dir": self.output_dir,
            "per_device_train_batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "max_steps": self.max_steps,
            "save_steps": self.save_steps,
            "logging_steps": self.logging_steps,
            "fp16": False,  # Disabled for CPU safety unless explicitly enabled
            "bf16": False,
            "optim": "adamw_torch",
            "lr_scheduler_type": "linear",
            "warmup_ratio": 0.03,
            "report_to": "none",
            "remove_unused_columns": False,
            "disable_tqdm": False,
            "seed": 42
        }


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Factory function to create the standard 4-bit quantization config.

    Returns:
        BitsAndBytesConfig configured for CPU-friendly 4-bit loading.
    """
    import torch
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float32,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        llm_int8_threshold=6.0
    )


def create_lora_config_from_env() -> LoRAConfig:
    """
    Create LoRAConfig from environment variables or defaults.

    Reads configuration from environment to allow runtime override without code changes.
    Falls back to FR-003 compliant defaults if not specified.

    Returns:
        LoRAConfig instance.
    """
    config = get_config()
    model_id = getattr(config, 'BASE_MODEL_ID', 'microsoft/phi-2')

    # Environment overrides with strict validation
    batch_size = int(os.getenv('LORA_BATCH_SIZE', '2'))
    if batch_size > 2:
        raise ValueError(f"Environment variable LORA_BATCH_SIZE={batch_size} violates FR-003 (must be <= 2)")

    grad_accum = int(os.getenv('LORA_GRADIENT_ACCUMULATION', '4'))
    if grad_accum != 4:
        raise ValueError(f"Environment variable LORA_GRADIENT_ACCUMULATION={grad_accum} violates FR-003 (must be 4)")

    r = int(os.getenv('LORA_R', '16'))
    lora_alpha = int(os.getenv('LORA_ALPHA', '32'))

    return LoRAConfig(
        r=r,
        lora_alpha=lora_alpha,
        batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        model_id=model_id,
        output_dir=os.getenv('LORA_OUTPUT_DIR', 'data/results/lora_checkpoint')
    )


def validate_lora_config(config: LoRAConfig) -> Tuple[bool, str]:
    """
    Validate a LoRAConfig instance against FR-003 requirements.

    Args:
        config: The LoRAConfig to validate.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    errors = []

    if config.batch_size > 2:
        errors.append(f"batch_size {config.batch_size} exceeds maximum of 2")

    if config.gradient_accumulation_steps != 4:
        errors.append(f"gradient_accumulation_steps {config.gradient_accumulation_steps} must be 4")

    if not config.use_4bit:
        errors.append("4-bit quantization is required for CPU-constrained training")

    if errors:
        return False, "; ".join(errors)

    return True, ""


def main():
    """Entry point for testing and validation."""
    print("Testing LoRA configuration generation...")

    # Test default config
    default_config = LoRAConfig()
    is_valid, error_msg = validate_lora_config(default_config)
    assert is_valid, f"Default config validation failed: {error_msg}"
    print(f"✓ Default config valid: batch_size={default_config.batch_size}, grad_accum={default_config.gradient_accumulation_steps}")

    # Test PEFT conversion
    peft_config = default_config.to_peft_config()
    assert peft_config.r == 16
    print(f"✓ PEFT config created successfully")

    # Test quantization config
    quant_config = default_config.to_quantization_config()
    assert quant_config is not None
    assert quant_config.load_in_4bit
    print(f"✓ Quantization config created successfully")

    # Test environment-based config
    try:
        env_config = create_lora_config_from_env()
        is_valid, error_msg = validate_lora_config(env_config)
        assert is_valid, f"Env config validation failed: {error_msg}"
        print(f"✓ Environment config valid")
    except ValueError as e:
        print(f"⚠ Environment config validation skipped (expected if env vars set incorrectly): {e}")

    print("\nAll LoRA configuration tests passed!")


if __name__ == "__main__":
    main()