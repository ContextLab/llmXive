"""
Configuration management for the LLMXive research pipeline.
Provides centralized configuration for seeds, paths, runtime limits, and model candidates.
"""
import os
import json
import random
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

# Global configuration singleton
_config_instance: Optional['ProjectConfig'] = None
_config_lock = threading.Lock()


@dataclass
class RuntimeConfig:
    """Runtime execution constraints."""
    max_runtime_hours: float = 6.0
    max_memory_gb: float = 14.0
    batch_size: int = 32
    timeout_risk_threshold: float = 0.90  # Reduce dataset if 90% time used


@dataclass
class InferenceConfig:
    """LLM inference parameters."""
    model_name: str = "microsoft/Phi-3-mini-4k-instruct"
    quantization_bits: int = 4
    device: str = "cpu"
    max_context_length: int = 4096
    temperature: float = 0.0  # Deterministic for reproducibility
    top_p: float = 1.0
    zero_shot_prompt_template: str = "Identify any security vulnerability in the following code:\n{code}\n\nVulnerability type:"


@dataclass
class AnalysisConfig:
    """Statistical analysis parameters."""
    significance_level: float = 0.05
    bonferroni_correction: bool = True
    random_state: int = 42
    regression_family: str = "binomial"


@dataclass
class ProjectConfig:
    """Main project configuration container."""
    # Paths
    project_root: str = ""
    data_raw_path: str = "data/raw"
    data_processed_path: str = "data/processed"
    data_results_path: str = "data/results"
    data_logs_path: str = "data/logs"
    state_path: str = "state"
    contracts_path: str = "contracts"
    figures_path: str = "figures"

    # Runtime settings
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)

    # Candidate LLMs (ordered by preference)
    candidate_models: List[str] = field(default_factory=lambda: [
        "microsoft/Phi-3-mini-4k-instruct",
        "mistralai/Mistral-7B-Instruct-v0.2",
        "google/codegemma-7b-it",
        "meta-llama/Llama-2-7b-chat-hf"
    ])

    # Fixed seeds for reproducibility
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            'project_root': self.project_root,
            'data_raw_path': self.data_raw_path,
            'data_processed_path': self.data_processed_path,
            'data_results_path': self.data_results_path,
            'data_logs_path': self.data_logs_path,
            'state_path': self.state_path,
            'contracts_path': self.contracts_path,
            'figures_path': self.figures_path,
            'runtime': asdict(self.runtime),
            'inference': asdict(self.inference),
            'analysis': asdict(self.analysis),
            'candidate_models': self.candidate_models,
            'seed': self.seed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Create config from dictionary."""
        runtime = RuntimeConfig(**data.get('runtime', {}))
        inference = InferenceConfig(**data.get('inference', {}))
        analysis = AnalysisConfig(**data.get('analysis', {}))
        return cls(
            project_root=data.get('project_root', ''),
            data_raw_path=data.get('data_raw_path', 'data/raw'),
            data_processed_path=data.get('data_processed_path', 'data/processed'),
            data_results_path=data.get('data_results_path', 'data/results'),
            data_logs_path=data.get('data_logs_path', 'data/logs'),
            state_path=data.get('state_path', 'state'),
            contracts_path=data.get('contracts_path', 'contracts'),
            figures_path=data.get('figures_path', 'figures'),
            runtime=runtime,
            inference=inference,
            analysis=analysis,
            candidate_models=data.get('candidate_models', []),
            seed=data.get('seed', 42)
        )


def get_config() -> ProjectConfig:
    """Get the global configuration singleton."""
    global _config_instance
    with _config_lock:
        if _config_instance is None:
            _config_instance = ProjectConfig()
        return _config_instance


def reset_config() -> None:
    """Reset the global configuration to defaults."""
    global _config_instance
    with _config_lock:
        _config_instance = None


def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    config = get_config()
    config.seed = seed
    random.seed(seed)
    # Note: numpy and torch seeds would be set here if imported
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_project_root() -> Path:
    """Get the project root directory as Path object."""
    config = get_config()
    if config.project_root:
        return Path(config.project_root)
    # Default to parent of src/utils
    return Path(__file__).resolve().parents[2]


def get_data_processed_path() -> Path:
    """Get the path to processed data directory."""
    return get_project_root() / get_config().data_processed_path


def get_data_results_path() -> Path:
    """Get the path to results directory."""
    return get_project_root() / get_config().data_results_path


def get_data_logs_path() -> Path:
    """Get the path to logs directory."""
    return get_project_root() / get_config().data_logs_path


def get_candidate_models() -> List[str]:
    """Get the list of candidate LLM models."""
    return get_config().candidate_models.copy()


def get_runtime_limits() -> Dict[str, float]:
    """Get runtime limits as dictionary."""
    runtime = get_config().runtime
    return {
        'max_runtime_hours': runtime.max_runtime_hours,
        'max_memory_gb': runtime.max_memory_gb,
        'batch_size': runtime.batch_size,
        'timeout_risk_threshold': runtime.timeout_risk_threshold
    }


def get_inference_params() -> Dict[str, Any]:
    """Get inference parameters as dictionary."""
    inference = get_config().inference
    return {
        'model_name': inference.model_name,
        'quantization_bits': inference.quantization_bits,
        'device': inference.device,
        'max_context_length': inference.max_context_length,
        'temperature': inference.temperature,
        'top_p': inference.top_p,
        'zero_shot_prompt_template': inference.zero_shot_prompt_template
    }


def save_config_to_json(filepath: str) -> None:
    """Save current configuration to a JSON file."""
    config = get_config()
    data = config.to_dict()
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def load_config_from_json(filepath: str) -> ProjectConfig:
    """Load configuration from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    config = ProjectConfig.from_dict(data)
    global _config_instance
    with _config_lock:
        _config_instance = config
    return config
