"""
Environment configuration for the llmXive pipeline.

This module provides centralized configuration management for:
- Random seeds (reproducibility)
- Critic thresholds (0.7, 0.8, 0.9)
- Batch sizes
- Execution limits (timeouts, memory)
- Dataset paths and flags
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Config:
    """Centralized configuration for the llmXive project."""

    # Random Seeds
    random_seed: int = 42
    torch_seed: int = 42
    numpy_seed: int = 42

    # Critic Configuration
    critic_thresholds: List[float] = field(default_factory=lambda: [0.7, 0.8, 0.9])
    default_critic_threshold: float = 0.8

    # Batch Sizes
    train_batch_size: int = 16
    eval_batch_size: int = 32
    simulator_batch_size: int = 64

    # Execution Limits
    generator_timeout_seconds: int = 30
    max_memory_gb: float = 7.0
    max_runtime_hours: int = 6

    # Dataset Paths
    data_raw_dir: str = "data/raw"
    data_intermediate_dir: str = "data/intermediate"
    data_simulator_validation_dir: str = "data/simulator_validation"
    specs_dir: str = "specs/001-llmxive-interleave-structure-vs-modality"

    # Dataset Availability Flags
    # If these are not available, the pipeline should fail loudly or fallback to text baseline
    wise_available: bool = True
    rise_available: bool = True
    vg_available: bool = False
    gqa_available: bool = False

    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # Model Configuration
    generator_model_name: str = "meta-llama/Llama-3-8B"
    critic_model_name: str = "meta-llama/Llama-3-8B"
    use_cpu: bool = True
    use_bfloat16: bool = False

    def validate(self) -> None:
        """Validate configuration consistency."""
        if not all(0.0 <= t <= 1.0 for t in self.critic_thresholds):
            raise ValueError("All critic thresholds must be between 0.0 and 1.0")

        if self.default_critic_threshold not in self.critic_thresholds:
            raise ValueError("Default critic threshold must be one of the configured thresholds")

        if self.max_memory_gb <= 0:
            raise ValueError("Max memory must be positive")

        if self.generator_timeout_seconds <= 0:
            raise ValueError("Generator timeout must be positive")

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            random_seed=int(os.getenv("LLMXIVE_RANDOM_SEED", "42")),
            torch_seed=int(os.getenv("LLMXIVE_TORCH_SEED", "42")),
            numpy_seed=int(os.getenv("LLMXIVE_NUMPY_SEED", "42")),
            critic_thresholds=[
                float(x) for x in os.getenv("LLMXIVE_CRITIC_THRESHOLDS", "0.7,0.8,0.9").split(",")
            ],
            default_critic_threshold=float(os.getenv("LLMXIVE_DEFAULT_CRITIC_THRESHOLD", "0.8")),
            train_batch_size=int(os.getenv("LLMXIVE_TRAIN_BATCH_SIZE", "16")),
            eval_batch_size=int(os.getenv("LLMXIVE_EVAL_BATCH_SIZE", "32")),
            simulator_batch_size=int(os.getenv("LLMXIVE_SIMULATOR_BATCH_SIZE", "64")),
            generator_timeout_seconds=int(os.getenv("LLMXIVE_GENERATOR_TIMEOUT", "30")),
            max_memory_gb=float(os.getenv("LLMXIVE_MAX_MEMORY_GB", "7.0")),
            max_runtime_hours=int(os.getenv("LLMXIVE_MAX_RUNTIME_HOURS", "6")),
            data_raw_dir=os.getenv("LLMXIVE_DATA_RAW_DIR", "data/raw"),
            data_intermediate_dir=os.getenv("LLMXIVE_DATA_INTERMEDIATE_DIR", "data/intermediate"),
            data_simulator_validation_dir=os.getenv(
                "LLMXIVE_DATA_SIMULATOR_VALIDATION_DIR", "data/simulator_validation"
            ),
            specs_dir=os.getenv("LLMXIVE_SPECS_DIR", "specs/001-llmxive-interleave-structure-vs-modality"),
            wise_available=os.getenv("LLMXIVE_WISE_AVAILABLE", "true").lower() == "true",
            rise_available=os.getenv("LLMXIVE_RISE_AVAILABLE", "true").lower() == "true",
            vg_available=os.getenv("LLMXIVE_VG_AVAILABLE", "false").lower() == "true",
            gqa_available=os.getenv("LLMXIVE_GQA_AVAILABLE", "false").lower() == "true",
            log_level=os.getenv("LLMXIVE_LOG_LEVEL", "INFO"),
            log_file=os.getenv("LLMXIVE_LOG_FILE", None),
            generator_model_name=os.getenv("LLMXIVE_GENERATOR_MODEL", "meta-llama/Llama-3-8B"),
            critic_model_name=os.getenv("LLMXIVE_CRITIC_MODEL", "meta-llama/Llama-3-8B"),
            use_cpu=os.getenv("LLMXIVE_USE_CPU", "true").lower() == "true",
            use_bfloat16=os.getenv("LLMXIVE_USE_BFLOAT16", "false").lower() == "true",
        )


# Global configuration instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance, initializing if necessary."""
    global config
    if config is None:
        config = Config.from_env()
        config.validate()
    return config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global config
    config = None
