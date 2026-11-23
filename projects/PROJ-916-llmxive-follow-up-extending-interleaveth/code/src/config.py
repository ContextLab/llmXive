"""
Environment configuration for the llmXive pipeline.

Handles random seeds, critic thresholds, batch sizes, and other
runtime parameters. Uses dataclasses for type safety and environment
variable overrides.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Config:
    """Global configuration container for the llmXive pipeline."""

    # Random seeds for reproducibility
    random_seed: int = 42
    torch_seed: int = 42
    numpy_seed: int = 42

    # Critic thresholds (sensitivity levels)
    critic_thresholds: List[float] = field(default_factory=lambda: [0.7, 0.8, 0.9])
    default_critic_threshold: float = 0.8

    # Batch sizes for processing
    batch_size: int = 8
    eval_batch_size: int = 4

    # LLM Inference settings
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.1

    # Pipeline execution limits
    max_steps_per_sample: int = 10
    timeout_per_sample_seconds: int = 30
    memory_limit_gb: float = 7.0

    # Noise injection parameters (for simulator)
    noise_target_min: float = 0.05
    noise_target_max: float = 0.15

    # Paths (relative to project root)
    data_dir: str = "data"
    logs_dir: str = "logs"
    figures_dir: str = "figures"

    # Simulation modes
    simulation_mode: str = "Noisy"  # Options: "Perfect", "Noisy"

    # Model settings
    model_name: str = "meta-llama/Llama-3-8B"
    device: str = "cpu"  # Options: "cpu", "cuda"

    # Logging verbosity
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """Initialize Config from environment variables."""
        return cls(
            random_seed=int(os.getenv("LLMXIVE_RANDOM_SEED", "42")),
            torch_seed=int(os.getenv("LLMXIVE_TORCH_SEED", "42")),
            numpy_seed=int(os.getenv("LLMXIVE_NUMPY_SEED", "42")),
            critic_thresholds=[
                float(x) for x in os.getenv("LLMXIVE_CRITIC_THRESHOLDS", "0.7,0.8,0.9").split(",")
            ],
            default_critic_threshold=float(os.getenv("LLMXIVE_DEFAULT_CRITIC_THRESHOLD", "0.8")),
            batch_size=int(os.getenv("LLMXIVE_BATCH_SIZE", "8")),
            eval_batch_size=int(os.getenv("LLMXIVE_EVAL_BATCH_SIZE", "4")),
            max_new_tokens=int(os.getenv("LLMXIVE_MAX_NEW_TOKENS", "512")),
            temperature=float(os.getenv("LLMXIVE_TEMPERATURE", "0.7")),
            top_p=float(os.getenv("LLMXIVE_TOP_P", "0.9")),
            repetition_penalty=float(os.getenv("LLMXIVE_REPETITION_PENALTY", "1.1")),
            max_steps_per_sample=int(os.getenv("LLMXIVE_MAX_STEPS_PER_SAMPLE", "10")),
            timeout_per_sample_seconds=int(os.getenv("LLMXIVE_TIMEOUT_PER_SAMPLE", "30")),
            memory_limit_gb=float(os.getenv("LLMXIVE_MEMORY_LIMIT_GB", "7.0")),
            noise_target_min=float(os.getenv("LLMXIVE_NOISE_TARGET_MIN", "0.05")),
            noise_target_max=float(os.getenv("LLMXIVE_NOISE_TARGET_MAX", "0.15")),
            data_dir=os.getenv("LLMXIVE_DATA_DIR", "data"),
            logs_dir=os.getenv("LLMXIVE_LOGS_DIR", "logs"),
            figures_dir=os.getenv("LLMXIVE_FIGURES_DIR", "figures"),
            simulation_mode=os.getenv("LLMXIVE_SIMULATION_MODE", "Noisy"),
            model_name=os.getenv("LLMXIVE_MODEL_NAME", "meta-llama/Llama-3-8B"),
            device=os.getenv("LLMXIVE_DEVICE", "cpu"),
            log_level=os.getenv("LLMXIVE_LOG_LEVEL", "INFO"),
        )


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Retrieve the global configuration instance.
    Initializes from environment variables if not already set.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.from_env()
    return _config_instance


def reset_config() -> None:
    """Reset the global configuration instance to allow re-initialization."""
    global _config_instance
    _config_instance = None
