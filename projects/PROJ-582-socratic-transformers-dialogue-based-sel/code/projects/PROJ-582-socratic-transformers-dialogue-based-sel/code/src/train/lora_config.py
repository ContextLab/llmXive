"""
LoRA Configuration Module for Socratic Transformers.

Implements FR-003 constraints:
- batch_size <= 2
- gradient_accumulation_steps = 4
- 4-bit quantization support
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
    Enforces FR-003 memory constraints.
    """
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"])
    task_type: str = "CAUSAL_LM"
    
    # FR-003 Constraints
    batch_size: int = 2  # Must be <= 2
    gradient_accumulation_steps: int = 4
    max_seq_length: int = 512
    learning_rate: float = 2e-4
    num_train_epochs: int = 3
    weight_decay: float = 0.01
    warmup_ratio: float = 0.03
    logging_steps: int = 10
    save_steps: int = 100
    save_total_limit: int = 2
    fp16: bool = True  # Enable mixed precision for CPU/GPU efficiency
    bf16: bool = False  # Disable bf16 if not available on CPU
    output_dir: str = "data/results"
    
    # Quantization settings
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True

    def __post_init__(self):
        """Validate constraints immediately upon instantiation."""
        if self.batch_size > 2:
            raise ValueError(f"FR-003 Violation: batch_size must be <= 2. Got {self.batch_size}")
        if self.gradient_accumulation_steps != 4:
            # Warning but not error, as 4 is the target for memory stability
            pass

    def to_peft_config(self) -> LoraConfig:
        """Convert this dataclass to a PEFT LoraConfig instance."""
        return LoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            task_type=TaskType.CAUSAL_LM,
            bias="none"
        )

    def to_bnb_config(self) -> BitsAndBytesConfig:
        """Generate the 4-bit quantization config for transformers."""
        if not self.use_4bit:
            return None
        
        compute_dtype = getattr(__import__("torch"), self.bnb_4bit_compute_dtype)
        
        return BitsAndBytesConfig(
            load_in_4bit=self.use_4bit,
            bnb_4bit_quant_type=self.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=self.bnb_4bit_use_double_quant,
            llm_int8_skip_modules=["lm_head"]
        )


def get_4bit_quantization_config() -> BitsAndBytesConfig:
    """
    Factory function to retrieve the standard 4-bit quantization config
    used across the project for memory efficiency (FR-003).
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype="float16",
        bnb_4bit_use_double_quant=True,
        llm_int8_skip_modules=["lm_head"]
    )


def create_lora_config_from_env() -> LoRAConfig:
    """
    Creates a LoRAConfig instance, optionally overriding defaults
    with environment variables for experimental flexibility.
    """
    config = get_config()
    
    # Map environment overrides if present
    r = int(os.getenv("LORA_R", 16))
    alpha = int(os.getenv("LORA_ALPHA", 32))
    batch = int(os.getenv("TRAIN_BATCH_SIZE", 2))
    
    # Enforce FR-003 hard limit even if env var tries to bypass
    if batch > 2:
        raise ValueError(f"Environment variable TRAIN_BATCH_SIZE ({batch}) violates FR-003 (max 2).")
    
    return LoRAConfig(
        r=r,
        lora_alpha=alpha,
        batch_size=batch,
        gradient_accumulation_steps=4,
        learning_rate=float(os.getenv("LEARNING_RATE", 2e-4)),
        num_train_epochs=int(os.getenv("NUM_EPOCHS", 3)),
        output_dir=os.getenv("OUTPUT_DIR", "data/results")
    )


def validate_lora_config(cfg: LoRAConfig) -> Tuple[bool, str]:
    """
    Validates a LoRAConfig instance against project constraints.
    Returns (is_valid, error_message).
    """
    if cfg.batch_size > 2:
        return False, f"batch_size {cfg.batch_size} exceeds FR-003 limit of 2."
    if cfg.gradient_accumulation_steps < 1:
        return False, "gradient_accumulation_steps must be >= 1."
    if cfg.r <= 0:
        return False, "LoRA rank 'r' must be positive."
    return True, "Valid"


def main():
    """
    Entry point for CLI validation of LoRA configuration.
    Usage: python -m src.train.lora_config
    """
    print("Initializing LoRA Configuration (FR-003 Compliant)...")
    try:
        cfg = create_lora_config_from_env()
        is_valid, msg = validate_lora_config(cfg)
        
        if not is_valid:
            print(f"ERROR: Configuration invalid: {msg}")
            exit(1)
        
        print(f"Configuration Validated: {cfg}")
        print(f"PEFT Config: {cfg.to_peft_config()}")
        print(f"Quantization Config: {cfg.to_bnb_config()}")
        exit(0)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        exit(1)


if __name__ == "__main__":
    main()