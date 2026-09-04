"""
BES Configuration Module

This module provides configuration for the Bidirectional Evolutionary Search (BES)
framework, specifically focusing on LLM selection and execution parameters.

Constraints enforced:
- Primary model: distilbert-base-uncased
- Device: CPU only (device='cpu')
- No bitsandbytes usage (explicitly forbidden)
- Execution engine: optimum.onnxruntime for CPU optimization
- Fallback model: TinyBERT if memory limits are exceeded
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# Constants for model configuration
PRIMARY_MODEL_NAME = "distilbert-base-uncased"
FALLBACK_MODEL_NAME = "prajjwal1/bert-tiny"  # TinyBERT alternative
MAX_MEMORY_MB = 2048  # 2GB memory limit threshold for fallback

# Execution constraints
DEVICE = "cpu"
USE_BITSANDBYTES = False  # Explicitly forbidden per task constraints
USE_ONNX_RUNTIME = True   # Mandated for CPU execution

# ONNX configuration
ONNX_OPTIMIZATION_LEVEL = "all"
ONNX_DYNAMIC_AXES = {
    "input_ids": {0: "batch_size", 1: "sequence_length"},
    "attention_mask": {0: "batch_size", 1: "sequence_length"}
}

# BES Hyperparameters
POPULATION_SIZE_DEFAULT = 50
GENERATIONS_DEFAULT = 20
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.7
ELITISM_COUNT = 5

# Logging and paths
LOG_LEVEL = "INFO"
CACHE_DIR = Path.home() / ".cache" / "bes_models"


class BESConfig:
    """
    Configuration container for the Bidirectional Evolutionary Search.

    Attributes:
        model_name (str): Name of the primary model to use.
        fallback_model_name (str): Name of the fallback model if primary fails.
        device (str): Execution device ('cpu' or 'cuda').
        use_onnx (bool): Whether to use ONNX Runtime for inference.
        optimization_level (str): ONNX optimization level.
        pop_size (int): Initial population size.
        generations (int): Number of evolutionary generations.
        mutation_rate (float): Probability of mutation.
        crossover_rate (float): Probability of crossover.
        elitism_count (int): Number of top individuals to preserve.
        cache_dir (Path): Directory for model caching.
        max_memory_mb (int): Memory limit in MB to trigger fallback.
    """

    def __init__(
        self,
        model_name: str = PRIMARY_MODEL_NAME,
        fallback_model_name: str = FALLBACK_MODEL_NAME,
        device: str = DEVICE,
        use_onnx: bool = USE_ONNX_RUNTIME,
        optimization_level: str = ONNX_OPTIMIZATION_LEVEL,
        pop_size: int = POPULATION_SIZE_DEFAULT,
        generations: int = GENERATIONS_DEFAULT,
        mutation_rate: float = MUTATION_RATE,
        crossover_rate: float = CROSSOVER_RATE,
        elitism_count: int = ELITISM_COUNT,
        cache_dir: Optional[Path] = None,
        max_memory_mb: int = MAX_MEMORY_MB
    ):
        # Validate constraints
        if device != "cpu":
            raise ValueError("Device must be 'cpu' as per project constraints.")
        
        if USE_BITSANDBYTES:
            raise ValueError("bitsandbytes is explicitly forbidden in this configuration.")

        self.model_name = model_name
        self.fallback_model_name = fallback_model_name
        self.device = device
        self.use_onnx = use_onnx
        self.optimization_level = optimization_level
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_count = elitism_count
        self.cache_dir = cache_dir if cache_dir else CACHE_DIR
        self.max_memory_mb = max_memory_mb

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "model_name": self.model_name,
            "fallback_model_name": self.fallback_model_name,
            "device": self.device,
            "use_onnx": self.use_onnx,
            "optimization_level": self.optimization_level,
            "pop_size": self.pop_size,
            "generations": self.generations,
            "mutation_rate": self.mutation_rate,
            "crossover_rate": self.crossover_rate,
            "elitism_count": self.elitism_count,
            "cache_dir": str(self.cache_dir),
            "max_memory_mb": self.max_memory_mb,
            "constraints": {
                "no_bitsandbytes": True,
                "cpu_only": True,
                "optimum_onnx": True
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BESConfig":
        """Create a configuration instance from a dictionary."""
        return cls(
            model_name=data.get("model_name", PRIMARY_MODEL_NAME),
            fallback_model_name=data.get("fallback_model_name", FALLBACK_MODEL_NAME),
            device=data.get("device", DEVICE),
            use_onnx=data.get("use_onnx", USE_ONNX_RUNTIME),
            optimization_level=data.get("optimization_level", ONNX_OPTIMIZATION_LEVEL),
            pop_size=data.get("pop_size", POPULATION_SIZE_DEFAULT),
            generations=data.get("generations", GENERATIONS_DEFAULT),
            mutation_rate=data.get("mutation_rate", MUTATION_RATE),
            crossover_rate=data.get("crossover_rate", CROSSOVER_RATE),
            elitism_count=data.get("elitism_count", ELITISM_COUNT),
            cache_dir=Path(data.get("cache_dir", CACHE_DIR)),
            max_memory_mb=data.get("max_memory_mb", MAX_MEMORY_MB)
        )

    def __repr__(self) -> str:
        return (
            f"BESConfig(model={self.model_name}, "
            f"device={self.device}, "
            f"onnx={self.use_onnx}, "
            f"pop_size={self.pop_size})"
        )


def get_default_config() -> BESConfig:
    """
    Returns the default BES configuration.

    Returns:
        BESConfig: A default configuration instance.
    """
    return BESConfig()


def main():
    """
    Entry point for testing and displaying the configuration.
    """
    import json
    
    config = get_default_config()
    config_dict = config.to_dict()
    
    print("BES Configuration Generated:")
    print(json.dumps(config_dict, indent=2))
    
    # Verify constraints
    assert config.device == "cpu", "Device must be CPU"
    assert not config.use_onnx == False, "ONNX Runtime must be enabled"
    assert config.model_name == PRIMARY_MODEL_NAME, "Primary model must be distilbert-base-uncased"
    
    print("\nAll constraints verified successfully.")


if __name__ == "__main__":
    main()