"""
Environment configuration management for Socratic Transformers project.

This module defines all critical configuration constants, model paths,
and hyperparameters required for the research pipeline.
"""

import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np

# Project Root Paths
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_RAW = _PROJECT_ROOT / "data" / "raw"
_DATA_PROCESSED = _PROJECT_ROOT / "data" / "processed"
_DATA_RESULTS = _PROJECT_ROOT / "data" / "results"
_STATE_DIR = _PROJECT_ROOT / "state"

# Model IDs (HuggingFace)
# Using a small, CPU-friendly base model for the student
BASE_MODEL_ID: str = "distilbert/distilgpt2"

# Using a small, frozen model for the critic/adversarial component
# Phi-2 or similar small model is suitable for logical contradiction detection
CRITIC_MODEL_ID: str = "microsoft/phi-2"

# Data Paths
# Path to the question bank (downloaded datasets)
QUESTION_BANK_PATH: str = str(_DATA_RAW)

# Prompt Templates
# Adversarial prompt template for generating critiques
ADVERSARIAL_PROMPT_TEMPLATE: str = (
    "You are a critical Socratic tutor. Your goal is to identify logical "
    "contradictions, unsupported assumptions, or high-probability errors in "
    "the following answer. Output ONLY the critique, do not offer a corrected "
    "answer. Focus on the reasoning steps.\n\n"
    "Answer to critique: {answer}\n\n"
    "Critique:"
)

# Hyperparameters
# Threshold for semantic similarity rejection (0.0 to 1.0)
# If similarity(critique_error_span, candidate_answer) > threshold, reject candidate
SELECTION_THRESHOLD: float = 0.65

# Generation Parameters
GENERATION_TEMPERATURE: float = 0.7
MAX_RETRIES: int = 5
CANDIDATE_COUNT: int = 5

# Random Seed for reproducibility
RANDOM_SEED: int = 42

@dataclass
class SocraticConfig:
    """Dataclass holding the full runtime configuration."""
    base_model_id: str = BASE_MODEL_ID
    critic_model_id: str = CRITIC_MODEL_ID
    question_bank_path: str = QUESTION_BANK_PATH
    adversarial_prompt_template: str = ADVERSARIAL_PROMPT_TEMPLATE
    selection_threshold: float = SELECTION_THRESHOLD
    generation_temperature: float = GENERATION_TEMPERATURE
    max_retries: int = MAX_RETRIES
    candidate_count: int = CANDIDATE_COUNT
    random_seed: int = RANDOM_SEED
    data_raw: Path = field(default_factory=lambda: _DATA_RAW)
    data_processed: Path = field(default_factory=lambda: _DATA_PROCESSED)
    data_results: Path = field(default_factory=lambda: _DATA_RESULTS)
    state_dir: Path = field(default_factory=lambda: _STATE_DIR)

# Global configuration instance
_global_config: Optional[SocraticConfig] = None

def get_config() -> SocraticConfig:
    """Returns the global configuration, initializing it if necessary."""
    global _global_config
    if _global_config is None:
        _global_config = SocraticConfig()
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """Sets the global configuration instance."""
    global _global_config
    _global_config = config

def load_config_from_env() -> SocraticConfig:
    """Loads configuration from environment variables if present, otherwise uses defaults."""
    global _global_config
    if _global_config is None:
        _global_config = SocraticConfig()
    
    # Override with environment variables if set
    if os.getenv("BASE_MODEL_ID"):
        _global_config.base_model_id = os.getenv("BASE_MODEL_ID")
    if os.getenv("CRITIC_MODEL_ID"):
        _global_config.critic_model_id = os.getenv("CRITIC_MODEL_ID")
    if os.getenv("QUESTION_BANK_PATH"):
        _global_config.question_bank_path = os.getenv("QUESTION_BANK_PATH")
    if os.getenv("SELECTION_THRESHOLD"):
        _global_config.selection_threshold = float(os.getenv("SELECTION_THRESHOLD"))
    if os.getenv("RANDOM_SEED"):
        _global_config.random_seed = int(os.getenv("RANDOM_SEED"))
    
    return _global_config

def set_seed(seed: int) -> None:
    """Sets the random seed for reproducibility across libraries."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def init_project() -> None:
    """Initializes the project directory structure based on config."""
    config = get_config()
    config.data_raw.mkdir(parents=True, exist_ok=True)
    config.data_processed.mkdir(parents=True, exist_ok=True)
    config.data_results.mkdir(parents=True, exist_ok=True)
    config.state_dir.mkdir(parents=True, exist_ok=True)

def main():
    """Main entry point for testing configuration."""
    config = load_config_from_env()
    print(f"Base Model: {config.base_model_id}")
    print(f"Critic Model: {config.critic_model_id}")
    print(f"Selection Threshold: {config.selection_threshold}")
    print(f"Data Raw: {config.data_raw}")

if __name__ == "__main__":
    main()