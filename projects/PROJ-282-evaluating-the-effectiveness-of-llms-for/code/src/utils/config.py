"""
Configuration management for the research pipeline.
Handles seeds, paths, runtime thresholds, and model lists.
"""
import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

# Singleton pattern for configuration
_config_instance: Optional["ProjectConfig"] = None

@dataclass
class RuntimeConfig:
    """Runtime constraints and settings."""
    seed: int = 42
    max_runtime_hours: float = 6.0
    max_memory_gb: float = 14.0
    batch_size: int = 32
    max_workers: int = 4

@dataclass
class InferenceConfig:
    """LLM Inference specific settings."""
    model_name: str = "distilbert/distilroberta-base"
    quantization_mode: str = "4bit"
    prompt_template: str = "Identify any security vulnerability in the following code: {code}"
    max_tokens: int = 512
    temperature: float = 0.0

@dataclass
class AnalysisConfig:
    """Statistical analysis settings."""
    significance_level: float = 0.05
    correction_method: str = "benjamini_hochberg"
    regression_model: str = "logistic"

@dataclass
class ProjectConfig:
    """Main project configuration."""
    project_name: str = "PROJ-282-evaluating-the-effectiveness-of-llms-for"
    root_path: str = ""
    data_path: str = "data"
    results_path: str = "data/results"
    state_path: str = "state"
    
    # Runtime settings
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    
    # Candidate models list (T004)
    candidate_models: List[str] = field(default_factory=lambda: [
        "distilbert/distilroberta-base",
        "microsoft/deberta-v3-base",
        "Salesforce/codebert-base"
    ])

def get_project_root() -> Path:
    """Returns the project root path."""
    global _config_instance
    if _config_instance is None:
        get_config()
    return Path(_config_instance.root_path or Path.cwd())

def get_config() -> ProjectConfig:
    """
    Returns the singleton ProjectConfig instance.
    Initializes with defaults if not set.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ProjectConfig()
        # Set root to current working directory if not explicitly set
        if not _config_instance.root_path:
            _config_instance.root_path = str(Path.cwd())
    return _config_instance

def reset_config():
    """Resets the configuration to defaults."""
    global _config_instance
    _config_instance = None

def get_data_processed_path() -> Path:
    """Returns the path to processed data directory."""
    return get_project_root() / "data" / "processed"

def get_data_results_path() -> Path:
    """Returns the path to results directory."""
    return get_project_root() / "data" / "results"

def get_candidate_models() -> List[str]:
    """Returns the list of candidate LLMs."""
    config = get_config()
    return config.candidate_models

def get_runtime_limits() -> Dict[str, float]:
    """Returns runtime limits as a dictionary."""
    config = get_config()
    return {
        "max_hours": config.runtime.max_runtime_hours,
        "max_memory_gb": config.runtime.max_memory_gb
    }

def get_inference_params() -> Dict[str, Any]:
    """Returns inference parameters as a dictionary."""
    config = get_config()
    return {
        "model_name": config.inference.model_name,
        "quantization_mode": config.inference.quantization_mode,
        "prompt_template": config.inference.prompt_template,
        "max_tokens": config.inference.max_tokens,
        "temperature": config.inference.temperature
    }

# Set random seed globally
def set_seed(seed: int):
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: torch and numpy seeds would be set here if imported
    get_config().runtime.seed = seed

if __name__ == "__main__":
    # Test configuration
    config = get_config()
    print(f"Project: {config.project_name}")
    print(f"Root: {config.root_path}")
    print(f"Models: {config.candidate_models}")
    print(f"Runtime Limits: {get_runtime_limits()}")
