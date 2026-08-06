"""
Environment configuration management for the Socratic Transformers project.

Handles random seeds, model paths, and global project configuration.
Ensures reproducibility and centralized management of hyperparameters.
"""
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np

# Global configuration instance (singleton pattern)
_global_config: Optional["SocraticConfig"] = None

@dataclass
class SocraticConfig:
    """
    Central configuration for the Socratic Transformers project.
    
    Attributes:
        project_root: Root directory of the project
        seed: Random seed for reproducibility
        data_dir: Directory for data storage
        model_dir: Directory for model checkpoints
        log_dir: Directory for log files
        results_dir: Directory for results and metrics
        device: Device to run models on (cpu, cuda, mps)
        max_tokens: Maximum number of tokens for generation
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        model_name: HuggingFace model identifier
        critic_model_name: HuggingFace identifier for the frozen critic model
        lora_rank: LoRA attention rank
        lora_alpha: LoRA scaling factor
        lora_dropout: LoRA dropout rate
        batch_size: Training batch size
        gradient_accumulation_steps: Gradient accumulation steps
        learning_rate: Learning rate for optimization
        num_epochs: Number of training epochs
        max_length: Maximum sequence length
        quantization_bits: Number of bits for quantization (4 or 8)
        timeout_seconds: Hard timeout for training loops (seconds)
        ablation_placeholder: Neutral placeholder text for ablation studies
    """
    # Project structure
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    
    # Reproducibility
    seed: int = 42
    
    # Directory paths (relative to project_root)
    data_dir: Path = field(default_factory=lambda: Path("data"))
    model_dir: Path = field(default_factory=lambda: Path("models"))
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    results_dir: Path = field(default_factory=lambda: Path("results"))
    
    # Model configuration
    device: str = "cpu"
    model_name: str = "meta-llama/Meta-Llama-3-8B"
    critic_model_name: str = "meta-llama/Meta-Llama-3-8B"
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    max_length: int = 2048
    quantization_bits: int = 4
    
    # Training hyperparameters
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    num_epochs: int = 3
    
    # Safety and constraints
    timeout_seconds: int = 3600  # 1 hour default timeout
    ablation_placeholder: str = "[CRITIQUE_REMOVED]"
    
    # Dataset configuration
    datasets: List[str] = field(default_factory=lambda: ["gsm8k", "math"])
    
    # Statistical analysis
    significance_level: float = 0.05
    bonferroni_correction: bool = True

    def __post_init__(self):
        """Initialize paths relative to project root."""
        self.data_dir = self.project_root / self.data_dir
        self.model_dir = self.project_root / self.model_dir
        self.log_dir = self.project_root / self.log_dir
        self.results_dir = self.project_root / self.results_dir

    def get_data_path(self, subpath: str) -> Path:
        """Get full path within data directory."""
        return self.data_dir / subpath

    def get_model_path(self, subpath: str) -> Path:
        """Get full path within model directory."""
        return self.model_dir / subpath

    def get_log_path(self, subpath: str) -> Path:
        """Get full path within log directory."""
        return self.log_dir / subpath

    def get_results_path(self, subpath: str) -> Path:
        """Get full path within results directory."""
        return self.results_dir / subpath

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            "seed": self.seed,
            "device": self.device,
            "model_name": self.model_name,
            "critic_model_name": self.critic_model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_length": self.max_length,
            "quantization_bits": self.quantization_bits,
            "lora_rank": self.lora_rank,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "learning_rate": self.learning_rate,
            "num_epochs": self.num_epochs,
            "timeout_seconds": self.timeout_seconds,
            "datasets": self.datasets,
            "significance_level": self.significance_level,
            "bonferroni_correction": self.bonferroni_correction,
            "ablation_placeholder": self.ablation_placeholder,
        }

def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.
    
    Environment variables override default values:
        SOCRATIC_SEED: Random seed
        SOCRATIC_DEVICE: Device (cpu, cuda, mps)
        SOCRATIC_MODEL_NAME: Base model identifier
        SOCRATIC_CRITIC_MODEL_NAME: Critic model identifier
        SOCRATIC_MAX_TOKENS: Maximum generation tokens
        SOCRATIC_TEMPERATURE: Sampling temperature
        SOCRATIC_LORA_RANK: LoRA rank
        SOCRATIC_BATCH_SIZE: Batch size
        SOCRATIC_LEARNING_RATE: Learning rate
        SOCRATIC_TIMEOUT_SECONDS: Training timeout
    """
    config = SocraticConfig()
    
    # Override with environment variables if set
    if seed := os.getenv("SOCRATIC_SEED"):
        config.seed = int(seed)
    
    if device := os.getenv("SOCRATIC_DEVICE"):
        config.device = device
    
    if model_name := os.getenv("SOCRATIC_MODEL_NAME"):
        config.model_name = model_name
    
    if critic_model_name := os.getenv("SOCRATIC_CRITIC_MODEL_NAME"):
        config.critic_model_name = critic_model_name
    
    if max_tokens := os.getenv("SOCRATIC_MAX_TOKENS"):
        config.max_tokens = int(max_tokens)
    
    if temperature := os.getenv("SOCRATIC_TEMPERATURE"):
        config.temperature = float(temperature)
    
    if top_p := os.getenv("SOCRATIC_TOP_P"):
        config.top_p = float(top_p)
    
    if max_length := os.getenv("SOCRATIC_MAX_LENGTH"):
        config.max_length = int(max_length)
    
    if quantization_bits := os.getenv("SOCRATIC_QUANTIZATION_BITS"):
        config.quantization_bits = int(quantization_bits)
    
    if lora_rank := os.getenv("SOCRATIC_LORA_RANK"):
        config.lora_rank = int(lora_rank)
    
    if lora_alpha := os.getenv("SOCRATIC_LORA_ALPHA"):
        config.lora_alpha = int(lora_alpha)
    
    if lora_dropout := os.getenv("SOCRATIC_LORA_DROPOUT"):
        config.lora_dropout = float(lora_dropout)
    
    if batch_size := os.getenv("SOCRATIC_BATCH_SIZE"):
        config.batch_size = int(batch_size)
    
    if gradient_accumulation := os.getenv("SOCRATIC_GRADIENT_ACCUMULATION"):
        config.gradient_accumulation_steps = int(gradient_accumulation)
    
    if learning_rate := os.getenv("SOCRATIC_LEARNING_RATE"):
        config.learning_rate = float(learning_rate)
    
    if num_epochs := os.getenv("SOCRATIC_NUM_EPOCHS"):
        config.num_epochs = int(num_epochs)
    
    if timeout_seconds := os.getenv("SOCRATIC_TIMEOUT_SECONDS"):
        config.timeout_seconds = int(timeout_seconds)
    
    return config

def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.
    
    Returns:
        SocraticConfig: The global configuration object.
        
    Raises:
        RuntimeError: If configuration has not been initialized.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance.
    
    Args:
        config: The configuration to set as global.
    """
    global _global_config
    _global_config = config

def ensure_directories(config: Optional[SocraticConfig] = None) -> None:
    """
    Ensure all required directories exist.
    
    Args:
        config: Configuration object. If None, uses global config.
    """
    if config is None:
        config = get_config()
    
    dirs = [
        config.data_dir,
        config.data_dir / "raw",
        config.data_dir / "processed",
        config.data_dir / "results",
        config.model_dir,
        config.log_dir,
        config.results_dir,
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

def init_project() -> SocraticConfig:
    """
    Initialize the project by setting up global config and directories.
    
    Returns:
        SocraticConfig: The initialized configuration.
    """
    config = load_config_from_env()
    set_global_config(config)
    ensure_directories(config)
    return config

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed. If None, uses the seed from global config.
    """
    if seed is None:
        seed = get_config().seed
    
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_model_path() -> Path:
    """Get the path to store/load models."""
    return get_config().model_dir

def get_data_path() -> Path:
    """Get the path to store/load data."""
    return get_config().data_dir

def get_log_path() -> Path:
    """Get the path to store logs."""
    return get_config().log_dir