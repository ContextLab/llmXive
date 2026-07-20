"""
LoRA Configuration Module for CPU-Constrained Fine-Tuning.

Implements FR-003: Low-rank adaptation with strict memory constraints:
- batch_size <= 2
- gradient_accumulation_steps = 4
- 4-bit quantization (bitsandbytes)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os
from peft import LoraConfig, TaskType
from transformers import BitsAndBytesConfig
from src.utils.config import get_config, SocraticConfig


@dataclass
class LoRAConfig:
    """
    Configuration container for LoRA fine-tuning parameters.

    Attributes:
        r: Rank of the update matrices.
        lora_alpha: Alpha scaling factor for LoRA.
        lora_dropout: Dropout rate for LoRA layers.
        target_modules: List of module names to apply LoRA to.
        task_type: Task type for PEFT (CAUSAL_LM for language modeling).
        per_device_train_batch_size: Batch size per device (constrained to <= 2).
        gradient_accumulation_steps: Steps for gradient accumulation (set to 4).
        max_grad_norm: Maximum gradient norm for clipping.
        learning_rate: Initial learning rate.
        num_train_epochs: Number of training epochs.
        weight_decay: Weight decay for optimizer.
        use_4bit_quantization: Flag to enable 4-bit quantization.
        bnb_4bit_compute_dtype: Compute dtype for 4-bit quantization.
        bnb_4bit_quant_type: Quantization type (nf4).
        output_dir: Directory to save the model and adapters.
    """
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: list = field(default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    task_type: str = "CAUSAL_LM"
    
    # Memory constraints per FR-003
    per_device_train_batch_size: int = 2
    gradient_accumulation_steps: int = 4
    max_grad_norm: float = 1.0
    
    # Training hyperparameters
    learning_rate: float = 2e-4
    num_train_epochs: int = 3
    weight_decay: float = 0.01
    
    # Quantization settings
    use_4bit_quantization: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    
    # Output
    output_dir: str = "data/results/finetuned_model"

    def to_peft_config(self) -> LoraConfig:
        """
        Converts this configuration to a PEFT LoraConfig object.
        
        Returns:
            LoraConfig: Config object ready for PEFT training.
        """
        return LoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            task_type=TaskType.CAUSAL_LM,
            bias="none",
            fan_in_fan_out=False,
            modules_to_save=None
        )

    def to_bitsandbytes_config(self) -> Optional[BitsAndBytesConfig]:
        """
        Creates a BitsAndBytesConfig for 4-bit quantization if enabled.
        
        Returns:
            BitsAndBytesConfig or None: Config object if quantization is enabled.
        """
        if not self.use_4bit_quantization:
            return None
        
        # Determine compute dtype
        compute_dtype = getattr(torch, self.bnb_4bit_compute_dtype)
        
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=self.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
            llm_int8_threshold=6.0,
            llm_int8_has_fp16_weight=False,
            llm_int8_skip_modules=["lm_head"]
        )

    def validate(self) -> bool:
        """
        Validates the configuration against hardware constraints.
        
        Returns:
            bool: True if valid, False otherwise.
        """
        if self.per_device_train_batch_size > 2:
            raise ValueError(f"batch_size must be <= 2 for CPU constraints, got {self.per_device_train_batch_size}")
        
        if self.gradient_accumulation_steps < 1:
            raise ValueError("gradient_accumulation_steps must be at least 1")
        
        return True


def create_lora_config_from_env() -> LoRAConfig:
    """
    Creates a LoRAConfig from environment variables or defaults.
    
    Reads configuration from environment variables if available, otherwise
    uses sensible defaults that adhere to FR-003 constraints.
    
    Returns:
        LoRAConfig: Config object with environment overrides applied.
    """
    config = LoRAConfig()
    
    # Override with environment variables if present
    if os.getenv("LORA_R"):
        config.r = int(os.getenv("LORA_R"))
    if os.getenv("LORA_ALPHA"):
        config.lora_alpha = int(os.getenv("LORA_ALPHA"))
    if os.getenv("LORA_DROPOUT"):
        config.lora_dropout = float(os.getenv("LORA_DROPOUT"))
    if os.getenv("BATCH_SIZE"):
        batch_size = int(os.getenv("BATCH_SIZE"))
        if batch_size > 2:
            raise ValueError(f"Environment BATCH_SIZE must be <= 2 for CPU constraints, got {batch_size}")
        config.per_device_train_batch_size = batch_size
    if os.getenv("GRADIENT_ACCUMULATION_STEPS"):
        config.gradient_accumulation_steps = int(os.getenv("GRADIENT_ACCUMULATION_STEPS"))
    if os.getenv("LEARNING_RATE"):
        config.learning_rate = float(os.getenv("LEARNING_RATE"))
    if os.getenv("OUTPUT_DIR"):
        config.output_dir = os.getenv("OUTPUT_DIR")
        
    return config


def validate_lora_config(config: LoRAConfig) -> Dict[str, Any]:
    """
    Validates a LoRAConfig and returns a report of its properties.
    
    Args:
        config: The LoRAConfig to validate.
        
    Returns:
        Dict containing validation status and configuration summary.
    """
    validation_result = {
        "valid": True,
        "issues": [],
        "config_summary": {}
    }
    
    try:
        config.validate()
    except ValueError as e:
        validation_result["valid"] = False
        validation_result["issues"].append(str(e))
    
    # Create summary
    validation_result["config_summary"] = {
        "r": config.r,
        "lora_alpha": config.lora_alpha,
        "lora_dropout": config.lora_dropout,
        "target_modules": config.target_modules,
        "per_device_train_batch_size": config.per_device_train_batch_size,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "learning_rate": config.learning_rate,
        "use_4bit_quantization": config.use_4bit_quantization,
        "output_dir": config.output_dir
    }
    
    return validation_result


# Import torch here to avoid circular imports if this module is imported early
import torch

def main():
    """
    Main function to demonstrate LoRA configuration creation and validation.
    """
    print("Creating default LoRA configuration...")
    config = LoRAConfig()
    
    print(f"Configuration: {config}")
    print(f"Batch size: {config.per_device_train_batch_size}")
    print(f"Gradient accumulation steps: {config.gradient_accumulation_steps}")
    print(f"4-bit quantization enabled: {config.use_4bit_quantization}")
    
    print("\nValidating configuration...")
    validation_report = validate_lora_config(config)
    print(f"Validation result: {validation_report}")
    
    if validation_report["valid"]:
        print("\nConverting to PEFT config...")
        peft_config = config.to_peft_config()
        print(f"PEFT Config created: {peft_config}")
        
        print("\nCreating BitsAndBytes config...")
        bnb_config = config.to_bitsandbytes_config()
        if bnb_config:
            print(f"BitsAndBytes Config created: {bnb_config}")
        else:
            print("BitsAndBytes Config not created (quantization disabled)")
    else:
        print("Configuration validation failed!")
        for issue in validation_report["issues"]:
            print(f"  - {issue}")

if __name__ == "__main__":
    main()