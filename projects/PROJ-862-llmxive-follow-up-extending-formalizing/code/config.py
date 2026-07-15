"""
Configuration management for the llmXive noise injection pipeline.

Defines noise sweep parameters, model paths, random seeds, and memory limits.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional
import logging

# Configure logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NoiseSweepConfig:
    """Configuration for the Gaussian noise injection sweep."""
    sigma_low: float = 0.01
    sigma_high: float = 1.0
    sigma_steps: int = 10
    sigma_log_scale: bool = True  # If True, sample log-uniformly between low and high

    def get_sigma_values(self) -> List[float]:
        """Generate the list of sigma values to sweep."""
        if self.sigma_log_scale:
            import numpy as np
            return list(np.logspace(np.log10(self.sigma_low), np.log10(self.sigma_high), self.sigma_steps))
        else:
            import numpy as np
            return list(np.linspace(self.sigma_low, self.sigma_high, self.sigma_steps))


@dataclass
class ModelConfig:
    """Configuration for model loading and paths."""
    # Default to a distilled model suitable for CPU inference
    model_name_or_path: str = "distilbert-base-uncased"
    tokenizer_name_or_path: str = "distilbert-base-uncased"
    device: str = "cpu"  # Enforced CPU-only as per project constraints
    max_length: int = 512
    hidden_size: int = 768  # Default for BERT-base, overridden by model config at runtime

    # Paths for the model (can be local or HF hub)
    cache_dir: Optional[str] = None


@dataclass
class ValidityConfig:
    """Configuration for semantic validity checks."""
    # Input drift check (Sentence-BERT)
    input_drift_threshold: float = 0.95
    sbert_model_name: str = "all-MiniLM-L6-v2"

    # Output validity check (BERTScore)
    output_validity_f1_threshold: float = 0.85
    perplexity_multiplier_limit: float = 2.0

    # Validity collapse detection
    validity_collapse_threshold: float = 0.10  # 10% pass rate triggers collapse


@dataclass
class MemoryConfig:
    """Configuration for memory limits and monitoring."""
    # Peak RSS limit in GB (SC-004)
    peak_rss_limit_gb: float = 7.0
    
    # Convert to bytes for internal checks
    @property
    def peak_rss_limit_bytes(self) -> int:
        return int(self.peak_rss_limit_gb * 1024 * 1024 * 1024)


@dataclass
class DataConfig:
    """Configuration for dataset loading and processing."""
    # Dataset source (BigBench subset or similar)
    dataset_name: str = "bigbench"
    dataset_subset: str = "logical_args"
    dataset_split: str = "train"
    
    # Streaming configuration
    streaming_enabled: bool = True
    batch_size: int = 32
    
    # Random seed for reproducibility
    random_seed: int = 42


@dataclass
class OutputPaths:
    """Configuration for output file paths."""
    base_dir: str = "data/processed"
    
    # Derived paths
    pairing_config: str = field(default="data/processed/pairing_config.json")
    baseline_vectors: str = field(default="data/processed/baseline_vectors.csv")
    perturbed_vectors: str = field(default="data/processed/perturbed_vectors.csv")
    filtered_pairs_input_drift: str = field(default="data/processed/filtered_pairs_input_drift.csv")
    validity_log: str = field(default="data/processed/validity_log.csv")
    sensitivity_report: str = field(default="data/processed/sensitivity_report.json")
    statistical_results: str = field(default="data/processed/statistical_results.json")


@dataclass
class PipelineConfig:
    """Master configuration for the entire pipeline."""
    noise: NoiseSweepConfig = field(default_factory=NoiseSweepConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    validity: ValidityConfig = field(default_factory=ValidityConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    data: DataConfig = field(default_factory=DataConfig)
    output: OutputPaths = field(default_factory=OutputPaths)

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables if present
        if "NOISE_SIGMA_LOW" in os.environ:
            config.noise.sigma_low = float(os.environ["NOISE_SIGMA_LOW"])
        if "NOISE_SIGMA_HIGH" in os.environ:
            config.noise.sigma_high = float(os.environ["NOISE_SIGMA_HIGH"])
        if "NOISE_SIGMA_STEPS" in os.environ:
            config.noise.sigma_steps = int(os.environ["NOISE_SIGMA_STEPS"])
        
        if "MODEL_NAME" in os.environ:
            config.model.model_name_or_path = os.environ["MODEL_NAME"]
            config.model.tokenizer_name_or_path = os.environ["MODEL_NAME"]
        
        if "MEMORY_LIMIT_GB" in os.environ:
            config.memory.peak_rss_limit_gb = float(os.environ["MEMORY_LIMIT_GB"])
        
        if "RANDOM_SEED" in os.environ:
            config.data.random_seed = int(os.environ["RANDOM_SEED"])
        
        logger.info("Configuration loaded from environment variables")
        return config

    def validate(self) -> bool:
        """Validate configuration parameters."""
        errors = []
        
        if self.noise.sigma_low <= 0:
            errors.append("sigma_low must be positive")
        
        if self.noise.sigma_high <= self.noise.sigma_low:
            errors.append("sigma_high must be greater than sigma_low")
        
        if self.validity.input_drift_threshold < 0 or self.validity.input_drift_threshold > 1:
            errors.append("input_drift_threshold must be between 0 and 1")
        
        if self.validity.output_validity_f1_threshold < 0 or self.validity.output_validity_f1_threshold > 1:
            errors.append("output_validity_f1_threshold must be between 0 and 1")
        
        if self.memory.peak_rss_limit_gb <= 0:
            errors.append("peak_rss_limit_gb must be positive")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        logger.info("Configuration validation passed")
        return True


# Global default configuration instance
DEFAULT_CONFIG = PipelineConfig()