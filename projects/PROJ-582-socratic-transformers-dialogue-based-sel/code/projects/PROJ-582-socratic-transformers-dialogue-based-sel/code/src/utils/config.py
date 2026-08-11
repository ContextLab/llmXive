"""
Environment configuration management for random seeds and model paths.

This module provides a centralized configuration system for the Socratic Transformers project,
handling random seeds, model paths, and other environment-dependent settings.
"""
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np
import torch

# Default configuration values
DEFAULT_SEED = 42
DEFAULT_MODEL_PATH = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
DEFAULT_CRITIC_MODEL = "TinyLlama/TinyLlama-1.1B-Instruct-v0.2"
DEFAULT_DATASETS = ["openai/gsm8k", "hendrycks/math"]
DEFAULT_DEVICE = "cpu"
DEFAULT_MAX_LENGTH = 512
DEFAULT_BATCH_SIZE = 2
DEFAULT_LEARNING_RATE = 2e-5
DEFAULT_NUM_EPOCHS = 3

@dataclass
class SocraticConfig:
    """
    Central configuration class for the Socratic Transformers project.

    Attributes:
        seed: Random seed for reproducibility
        model_path: Path to the base model
        critic_model_path: Path to the frozen critic model
        datasets: List of dataset identifiers to load
        device: Device to run on (cpu, cuda, mps)
        max_length: Maximum sequence length
        batch_size: Training batch size
        learning_rate: Learning rate for fine-tuning
        num_epochs: Number of training epochs
        output_dir: Directory for saving outputs
        data_dir: Directory for data storage
        log_dir: Directory for log files
        results_dir: Directory for results and metrics
        use_4bit: Whether to use 4-bit quantization
        lora_rank: LoRA rank for parameter-efficient fine-tuning
        lora_alpha: LoRA alpha scaling factor
        lora_dropout: Dropout rate for LoRA layers
        target_modules: List of modules to apply LoRA to
        gradient_accumulation_steps: Number of steps for gradient accumulation
        warmup_steps: Number of warmup steps for learning rate scheduler
        weight_decay: Weight decay for optimizer
        max_grad_norm: Maximum gradient norm for clipping
        logging_steps: Steps between logging events
        save_steps: Steps between saving checkpoints
        eval_steps: Steps between evaluation runs
        report_to: List of logging destinations (e.g., "wandb", "tensorboard")
        project_name: Name of the project for logging
        run_name: Name of the current run
        disable_tqdm: Whether to disable tqdm progress bars
        fp16: Whether to use mixed precision training
        bf16: Whether to use bfloat16 training
        optim: Optimizer to use (e.g., "adamw_torch", "adamw_8bit")
        lr_scheduler_type: Learning rate scheduler type
        include_tokens_per_second: Whether to include tokens per second in metrics
        include_num_iterations_per_second: Whether to include iterations per second
        dataloader_num_workers: Number of workers for data loading
        dataloader_prefetch_factor: Prefetch factor for data loading
        dataloader_pin_memory: Whether to pin memory for data loading
        dataloader_drop_last: Whether to drop the last incomplete batch
        remove_unused_columns: Whether to remove unused columns from datasets
        label_names: Names of columns to use as labels
        prediction_loss_only: Whether to only return loss in predictions
        per_device_train_batch_size: Per device training batch size
        per_device_eval_batch_size: Per device evaluation batch size
        gradient_checkpointing: Whether to use gradient checkpointing
        local_rank: Local rank for distributed training
        torch_compile: Whether to compile the model
        torch_compile_mode: Compilation mode
        ddp_backend: Distributed data parallel backend
        fsdp: Fully sharded data parallel settings
        fsdp_transformer_layer_cls_to_wrap: Transformer layer class to wrap for FSDP
        deepspeed: DeepSpeed configuration file path
        tp_size: Tensor parallel size
        pp_size: Pipeline parallel size
    """
    seed: int = DEFAULT_SEED
    model_path: str = DEFAULT_MODEL_PATH
    critic_model_path: str = DEFAULT_CRITIC_MODEL
    datasets: List[str] = field(default_factory=lambda: DEFAULT_DATASETS)
    device: str = DEFAULT_DEVICE
    max_length: int = DEFAULT_MAX_LENGTH
    batch_size: int = DEFAULT_BATCH_SIZE
    learning_rate: float = DEFAULT_LEARNING_RATE
    num_epochs: int = DEFAULT_NUM_EPOCHS
    output_dir: str = field(default_factory=lambda: str(Path("data/results")))
    data_dir: str = field(default_factory=lambda: str(Path("data/raw")))
    log_dir: str = field(default_factory=lambda: str(Path("logs")))
    results_dir: str = field(default_factory=lambda: str(Path("data/results")))
    use_4bit: bool = True
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    gradient_accumulation_steps: int = 4
    warmup_steps: int = 100
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    logging_steps: int = 50
    save_steps: int = 500
    eval_steps: int = 500
    report_to: List[str] = field(default_factory=lambda: ["tensorboard"])
    project_name: str = "socratic-transformers"
    run_name: Optional[str] = None
    disable_tqdm: bool = False
    fp16: bool = False
    bf16: bool = False
    optim: str = "adamw_torch"
    lr_scheduler_type: str = "linear"
    include_tokens_per_second: bool = True
    include_num_iterations_per_second: bool = True
    dataloader_num_workers: int = 0
    dataloader_prefetch_factor: Optional[int] = None
    dataloader_pin_memory: bool = True
    dataloader_drop_last: bool = False
    remove_unused_columns: bool = True
    label_names: Optional[List[str]] = None
    prediction_loss_only: bool = False
    per_device_train_batch_size: Optional[int] = None
    per_device_eval_batch_size: Optional[int] = None
    gradient_checkpointing: bool = False
    local_rank: int = -1
    torch_compile: bool = False
    torch_compile_mode: Optional[str] = None
    ddp_backend: Optional[str] = None
    fsdp: str = ""
    fsdp_transformer_layer_cls_to_wrap: Optional[str] = None
    deepspeed: Optional[str] = None
    tp_size: int = 1
    pp_size: int = 1

    def __post_init__(self):
        """Validate and post-process configuration values."""
        if self.per_device_train_batch_size is None:
            self.per_device_train_batch_size = self.batch_size
        if self.per_device_eval_batch_size is None:
            self.per_device_eval_batch_size = self.batch_size

        # Ensure output directories exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "seed": self.seed,
            "model_path": self.model_path,
            "critic_model_path": self.critic_model_path,
            "datasets": self.datasets,
            "device": self.device,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "num_epochs": self.num_epochs,
            "output_dir": self.output_dir,
            "data_dir": self.data_dir,
            "log_dir": self.log_dir,
            "results_dir": self.results_dir,
            "use_4bit": self.use_4bit,
            "lora_rank": self.lora_rank,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "target_modules": self.target_modules,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "warmup_steps": self.warmup_steps,
            "weight_decay": self.weight_decay,
            "max_grad_norm": self.max_grad_norm,
            "logging_steps": self.logging_steps,
            "save_steps": self.save_steps,
            "eval_steps": self.eval_steps,
            "report_to": self.report_to,
            "project_name": self.project_name,
            "run_name": self.run_name,
            "disable_tqdm": self.disable_tqdm,
            "fp16": self.fp16,
            "bf16": self.bf16,
            "optim": self.optim,
            "lr_scheduler_type": self.lr_scheduler_type,
            "include_tokens_per_second": self.include_tokens_per_second,
            "include_num_iterations_per_second": self.include_num_iterations_per_second,
            "dataloader_num_workers": self.dataloader_num_workers,
            "dataloader_prefetch_factor": self.dataloader_prefetch_factor,
            "dataloader_pin_memory": self.dataloader_pin_memory,
            "dataloader_drop_last": self.dataloader_drop_last,
            "remove_unused_columns": self.remove_unused_columns,
            "label_names": self.label_names,
            "prediction_loss_only": self.prediction_loss_only,
            "per_device_train_batch_size": self.per_device_train_batch_size,
            "per_device_eval_batch_size": self.per_device_eval_batch_size,
            "gradient_checkpointing": self.gradient_checkpointing,
            "local_rank": self.local_rank,
            "torch_compile": self.torch_compile,
            "torch_compile_mode": self.torch_compile_mode,
            "ddp_backend": self.ddp_backend,
            "fsdp": self.fsdp,
            "fsdp_transformer_layer_cls_to_wrap": self.fsdp_transformer_layer_cls_to_wrap,
            "deepspeed": self.deepspeed,
            "tp_size": self.tp_size,
            "pp_size": self.pp_size,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SocraticConfig":
        """Create configuration from dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_env(cls) -> "SocraticConfig":
        """Create configuration from environment variables."""
        return cls(
            seed=int(os.getenv("SEED", DEFAULT_SEED)),
            model_path=os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH),
            critic_model_path=os.getenv("CRITIC_MODEL_PATH", DEFAULT_CRITIC_MODEL),
            datasets=os.getenv("DATASETS", ",".join(DEFAULT_DATASETS)).split(","),
            device=os.getenv("DEVICE", DEFAULT_DEVICE),
            max_length=int(os.getenv("MAX_LENGTH", DEFAULT_MAX_LENGTH)),
            batch_size=int(os.getenv("BATCH_SIZE", DEFAULT_BATCH_SIZE)),
            learning_rate=float(os.getenv("LEARNING_RATE", DEFAULT_LEARNING_RATE)),
            num_epochs=int(os.getenv("NUM_EPOCHS", DEFAULT_NUM_EPOCHS)),
            output_dir=os.getenv("OUTPUT_DIR", str(Path("data/results"))),
            data_dir=os.getenv("DATA_DIR", str(Path("data/raw"))),
            log_dir=os.getenv("LOG_DIR", str(Path("logs"))),
            results_dir=os.getenv("RESULTS_DIR", str(Path("data/results"))),
            use_4bit=os.getenv("USE_4BIT", "true").lower() == "true",
            lora_rank=int(os.getenv("LORA_RANK", 16)),
            lora_alpha=int(os.getenv("LORA_ALPHA", 32)),
            lora_dropout=float(os.getenv("LORA_DROPOUT", 0.05)),
            target_modules=os.getenv("TARGET_MODULES", "q_proj,v_proj").split(","),
            gradient_accumulation_steps=int(os.getenv("GRADIENT_ACCUMULATION_STEPS", 4)),
            warmup_steps=int(os.getenv("WARMUP_STEPS", 100)),
            weight_decay=float(os.getenv("WEIGHT_DECAY", 0.01)),
            max_grad_norm=float(os.getenv("MAX_GRAD_NORM", 1.0)),
            logging_steps=int(os.getenv("LOGGING_STEPS", 50)),
            save_steps=int(os.getenv("SAVE_STEPS", 500)),
            eval_steps=int(os.getenv("EVAL_STEPS", 500)),
            report_to=os.getenv("REPORT_TO", "tensorboard").split(","),
            project_name=os.getenv("PROJECT_NAME", "socratic-transformers"),
            run_name=os.getenv("RUN_NAME", None),
            disable_tqdm=os.getenv("DISABLE_TQDM", "false").lower() == "true",
            fp16=os.getenv("FP16", "false").lower() == "true",
            bf16=os.getenv("BF16", "false").lower() == "true",
            optim=os.getenv("OPTIM", "adamw_torch"),
            lr_scheduler_type=os.getenv("LR_SCHEDULER_TYPE", "linear"),
            include_tokens_per_second=os.getenv("INCLUDE_TOKENS_PER_SECOND", "true").lower() == "true",
            include_num_iterations_per_second=os.getenv("INCLUDE_NUM_ITERATIONS_PER_SECOND", "true").lower() == "true",
            dataloader_num_workers=int(os.getenv("DATALOADER_NUM_WORKERS", 0)),
            dataloader_prefetch_factor=int(os.getenv("DATALOADER_PREFETCH_FACTOR", 2)) if os.getenv("DATALOADER_PREFETCH_FACTOR") else None,
            dataloader_pin_memory=os.getenv("DATALOADER_PIN_MEMORY", "true").lower() == "true",
            dataloader_drop_last=os.getenv("DATALOADER_DROP_LAST", "false").lower() == "true",
            remove_unused_columns=os.getenv("REMOVE_UNUSED_COLUMNS", "true").lower() == "true",
            label_names=os.getenv("LABEL_NAMES", None),
            prediction_loss_only=os.getenv("PREDICTION_LOSS_ONLY", "false").lower() == "true",
            per_device_train_batch_size=int(os.getenv("PER_DEVICE_TRAIN_BATCH_SIZE", DEFAULT_BATCH_SIZE)) if os.getenv("PER_DEVICE_TRAIN_BATCH_SIZE") else None,
            per_device_eval_batch_size=int(os.getenv("PER_DEVICE_EVAL_BATCH_SIZE", DEFAULT_BATCH_SIZE)) if os.getenv("PER_DEVICE_EVAL_BATCH_SIZE") else None,
            gradient_checkpointing=os.getenv("GRADIENT_CHECKPOINTING", "false").lower() == "true",
            local_rank=int(os.getenv("LOCAL_RANK", -1)),
            torch_compile=os.getenv("TORCH_COMPILE", "false").lower() == "true",
            torch_compile_mode=os.getenv("TORCH_COMPILE_MODE", None),
            ddp_backend=os.getenv("DDP_BACKEND", None),
            fsdp=os.getenv("FSDP", ""),
            fsdp_transformer_layer_cls_to_wrap=os.getenv("FSDP_TRANSFORMER_LAYER_CLS_TO_WRAP", None),
            deepspeed=os.getenv("DEEPSPEED", None),
            tp_size=int(os.getenv("TP_SIZE", 1)),
            pp_size=int(os.getenv("PP_SIZE", 1)),
        )

# Global configuration instance
_global_config: Optional[SocraticConfig] = None

def get_config() -> SocraticConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = SocraticConfig.from_env()
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """Set the global configuration instance."""
    global _global_config
    _global_config = config

def load_config_from_env() -> SocraticConfig:
    """Load configuration from environment variables and set as global."""
    global _global_config
    _global_config = SocraticConfig.from_env()
    return _global_config

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.

    Args:
        seed: Random seed to use. If None, uses the seed from the global config.
    """
    if seed is None:
        config = get_config()
        seed = config.seed

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Set environment variables for reproducibility
    os.environ["PYTHONHASHSEED"] = str(seed)

def init_project() -> SocraticConfig:
    """
    Initialize the project configuration.

    This function:
    1. Loads configuration from environment variables
    2. Sets random seeds for reproducibility
    3. Creates necessary directories
    4. Returns the initialized configuration

    Returns:
        SocraticConfig: The initialized configuration
    """
    config = load_config_from_env()
    set_seed(config.seed)
    return config

def main() -> None:
    """Main entry point for testing configuration."""
    config = init_project()
    print("Socratic Configuration:")
    print(f"  Seed: {config.seed}")
    print(f"  Model Path: {config.model_path}")
    print(f"  Critic Model Path: {config.critic_model_path}")
    print(f"  Datasets: {config.datasets}")
    print(f"  Device: {config.device}")
    print(f"  Max Length: {config.max_length}")
    print(f"  Batch Size: {config.batch_size}")
    print(f"  Learning Rate: {config.learning_rate}")
    print(f"  Num Epochs: {config.num_epochs}")
    print(f"  Output Dir: {config.output_dir}")
    print(f"  Data Dir: {config.data_dir}")
    print(f"  Log Dir: {config.log_dir}")
    print(f"  Results Dir: {config.results_dir}")
    print(f"  Use 4-bit: {config.use_4bit}")
    print(f"  LoRA Rank: {config.lora_rank}")
    print(f"  LoRA Alpha: {config.lora_alpha}")
    print(f"  LoRA Dropout: {config.lora_dropout}")
    print(f"  Target Modules: {config.target_modules}")
    print(f"  Gradient Accumulation Steps: {config.gradient_accumulation_steps}")

if __name__ == "__main__":
    main()
