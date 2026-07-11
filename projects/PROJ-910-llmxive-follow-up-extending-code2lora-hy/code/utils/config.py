"""
Configuration management for llmXive.

This module handles loading of random seeds, base model paths, and data paths
from a YAML configuration file.

NOTE ON STATISTICAL TESTS (T000 Override):
Per Spec SC-005, the Wilcoxon signed-rank test is the primary method for
statistical comparison. The Plan's instruction for a Paired t-test is overridden
here and in code/evaluation/stats.py. This configuration file does not perform
stats but sets up the environment for the evaluation pipeline.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Default configuration values
DEFAULT_BASE_MODEL = "TinyLlama-1.1B-Chat-hf"
DEFAULT_RANDOM_SEED = 42
DEFAULT_FEATURE_VECTOR_SIZE = 128  # Default if not in model config
DEFAULT_HIDDEN_SIZE = 4096  # Typical for Llama models, overridden by model config
DEFAULT_REPO_PEFT_BENCH_PATH = "data/raw/repo-peft-bench"

class Config:
    """Container for all project configuration settings."""

    def __init__(
        self,
        base_model: str = DEFAULT_BASE_MODEL,
        random_seed: int = DEFAULT_RANDOM_SEED,
        repo_peft_bench_path: str = DEFAULT_REPO_PEFT_BENCH_PATH,
        feature_vector_size: int = DEFAULT_FEATURE_VECTOR_SIZE,
        hidden_size: int = DEFAULT_HIDDEN_SIZE,
        device: str = "cpu",
        max_memory_gb: float = 7.0,
        cpu_cores: int = 2,
        timeout_seconds: int = 3600,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.base_model = base_model
        self.random_seed = random_seed
        self.repo_peft_bench_path = repo_peft_bench_path
        self.feature_vector_size = feature_vector_size
        self.hidden_size = hidden_size
        self.device = device
        self.max_memory_gb = max_memory_gb
        self.cpu_cores = cpu_cores
        self.timeout_seconds = timeout_seconds
        self.extra = extra or {}

        # Apply random seed immediately
        self.set_seed(random_seed)

    def set_seed(self, seed: int):
        """Set the random seed for reproducibility."""
        self.random_seed = seed
        random.seed(seed)
        # Note: torch and numpy seeding are handled in specific modules
        # to avoid circular imports or unnecessary global state changes here.

    @property
    def data_raw_path(self) -> Path:
        return Path("data/raw")

    @property
    def data_processed_path(self) -> Path:
        return Path("data/processed")

    @property
    def data_adapters_path(self) -> Path:
        return Path("data/adapters")

    @property
    def data_results_path(self) -> Path:
        return Path("data/results")

    def __repr__(self) -> str:
        return (
            f"Config(base_model={self.base_model}, "
            f"seed={self.random_seed}, "
            f"peft_path={self.repo_peft_bench_path}, "
            f"feature_size={self.feature_vector_size}, "
            f"hidden_size={self.hidden_size})"
        )

def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from a YAML file or return defaults.

    Args:
        config_path: Path to the YAML config file. If None, defaults are used.

    Returns:
        Config: A populated configuration object.
    """
    if config_path is None:
        # Check for default locations
        default_paths = [
            Path("config.yaml"),
            Path("configs/config.yaml"),
            Path("data/config.yaml"),
        ]
        for p in default_paths:
            if p.exists():
                config_path = p
                break

    if config_path is None or not Path(config_path).exists():
        # Return default config if no file found
        return Config()

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return Config()

    # Extract values with defaults
    base_model = data.get("base_model", DEFAULT_BASE_MODEL)
    random_seed = data.get("random_seed", DEFAULT_RANDOM_SEED)
    repo_peft_bench_path = data.get("repo_peft_bench_path", DEFAULT_REPO_PEFT_BENCH_PATH)
    feature_vector_size = data.get("feature_vector_size", DEFAULT_FEATURE_VECTOR_SIZE)
    hidden_size = data.get("hidden_size", DEFAULT_HIDDEN_SIZE)
    device = data.get("device", "cpu")
    max_memory_gb = data.get("max_memory_gb", 7.0)
    cpu_cores = data.get("cpu_cores", 2)
    timeout_seconds = data.get("timeout_seconds", 3600)

    # Handle nested 'model' config if present
    if "model" in data:
        model_data = data["model"]
        if "base_model" in model_data:
            base_model = model_data["base_model"]
        if "hidden_size" in model_data:
            hidden_size = model_data["hidden_size"]

    return Config(
        base_model=base_model,
        random_seed=random_seed,
        repo_peft_bench_path=repo_peft_bench_path,
        feature_vector_size=feature_vector_size,
        hidden_size=hidden_size,
        device=device,
        max_memory_gb=max_memory_gb,
        cpu_cores=cpu_cores,
        timeout_seconds=timeout_seconds,
        extra={k: v for k, v in data.items() if k not in [
            "base_model", "random_seed", "repo_peft_bench_path",
            "feature_vector_size", "hidden_size", "device", "model",
            "max_memory_gb", "cpu_cores", "timeout_seconds"
        ]},
    )