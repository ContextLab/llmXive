"""
Configuration management for the LLM Vulnerability Evaluation Pipeline.

Implements FR-002 (Runtime Constraints) and SC-005 (Candidate Models).
Provides deterministic seeds, path resolution, runtime thresholds, and
the list of candidate LLMs.
"""
import os
import json
import random
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass, field, asdict
import logging

# Thread-safe singleton for configuration
_config_lock = threading.Lock()
_global_config: Optional['ProjectConfig'] = None

# Default Paths (Relative to Project Root)
DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = DEFAULT_PROJECT_ROOT / "data"
DEFAULT_DATA_RAW = DEFAULT_DATA_DIR / "raw"
DEFAULT_DATA_PROCESSED = DEFAULT_DATA_DIR / "processed"
DEFAULT_DATA_RESULTS = DEFAULT_DATA_DIR / "results"
DEFAULT_DATA_LOGS = DEFAULT_DATA_DIR / "logs"
DEFAULT_STATE_DIR = DEFAULT_PROJECT_ROOT / "state"
DEFAULT_CONTRACTS_DIR = DEFAULT_PROJECT_ROOT / "contracts"
DEFAULT_SPEC_DIR = DEFAULT_PROJECT_ROOT / "specs"

# Default Runtime Thresholds (FR-002, SC-005)
DEFAULT_MAX_RUNTIME_HOURS = 6.0
DEFAULT_MAX_RAM_GB = 14.0  # Conservative cap for CPU/GPU memory
DEFAULT_BATCH_SIZE = 32

# Candidate LLMs (SC-005)
# Prioritizing CPU-compatible, low-bit quantized models for reproducibility.
# All models listed here must support C, Python, and JS (verified in T004a).
CANDIDATE_MODELS = [
    "microsoft/phi-3-mini-4k-instruct",  # Strong reasoning, small footprint
    "microsoft/Phi-3-mini-4k-instruct",  # Alternative casing if needed
    "HuggingFaceH4/zephyr-7b-beta",      # Good general purpose, 4bit capable
    "mistralai/Mistral-7B-Instruct-v0.2",# Strong code capabilities
    "codellama/CodeLlama-7b-Instruct-hf" # Specialized for code
]

# Random Seed for Reproducibility (Constitution Principle I)
DEFAULT_SEED = 42


@dataclass
class RuntimeConfig:
    """Runtime constraints and resource limits."""
    max_runtime_hours: float = DEFAULT_MAX_RUNTIME_HOURS
    max_ram_gb: float = DEFAULT_MAX_RAM_GB
    batch_size: int = DEFAULT_BATCH_SIZE
    timeout_risk_threshold: float = 0.90  # Halt if 90% time used

@dataclass
class InferenceConfig:
    """Configuration for LLM inference parameters."""
    model_name: str = ""  # Set by model_selector
    quantization_bits: int = 4
    device: str = "cpu"
    max_new_tokens: int = 256
    temperature: float = 0.0  # Deterministic decoding
    top_p: float = 1.0
    prompt_template: str = "Identify any security vulnerability in the following code: {code}"

@dataclass
class AnalysisConfig:
    """Configuration for statistical analysis parameters."""
    significance_level: float = 0.05
    correction_method: str = "bonferroni"
    random_state: int = DEFAULT_SEED

@dataclass
class ProjectConfig:
    """Main configuration container."""
    project_root: Path = field(default_factory=lambda: DEFAULT_PROJECT_ROOT)
    data_dir: Path = field(default_factory=lambda: DEFAULT_DATA_DIR)
    data_raw: Path = field(default_factory=lambda: DEFAULT_DATA_RAW)
    data_processed: Path = field(default_factory=lambda: DEFAULT_DATA_PROCESSED)
    data_results: Path = field(default_factory=lambda: DEFAULT_DATA_RESULTS)
    data_logs: Path = field(default_factory=lambda: DEFAULT_DATA_LOGS)
    state_dir: Path = field(default_factory=lambda: DEFAULT_STATE_DIR)
    contracts_dir: Path = field(default_factory=lambda: DEFAULT_CONTRACTS_DIR)
    spec_dir: Path = field(default_factory=lambda: DEFAULT_SPEC_DIR)
    
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    
    candidate_models: List[str] = field(default_factory=lambda: CANDIDATE_MODELS)
    seed: int = DEFAULT_SEED

    def __post_init__(self):
        # Ensure paths are Path objects
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        # ... (other paths handled similarly if needed)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to dictionary."""
        return {
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "data_raw": str(self.data_raw),
            "data_processed": str(self.data_processed),
            "data_results": str(self.data_results),
            "data_logs": str(self.data_logs),
            "state_dir": str(self.state_dir),
            "runtime": asdict(self.runtime),
            "inference": asdict(self.inference),
            "analysis": asdict(self.analysis),
            "candidate_models": self.candidate_models,
            "seed": self.seed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Deserialize config from dictionary."""
        return cls(
            project_root=Path(data.get("project_root", DEFAULT_PROJECT_ROOT)),
            data_dir=Path(data.get("data_dir", DEFAULT_DATA_DIR)),
            data_raw=Path(data.get("data_raw", DEFAULT_DATA_RAW)),
            data_processed=Path(data.get("data_processed", DEFAULT_DATA_PROCESSED)),
            data_results=Path(data.get("data_results", DEFAULT_DATA_RESULTS)),
            data_logs=Path(data.get("data_logs", DEFAULT_DATA_LOGS)),
            state_dir=Path(data.get("state_dir", DEFAULT_STATE_DIR)),
            runtime=RuntimeConfig(**data.get("runtime", {})),
            inference=InferenceConfig(**data.get("inference", {})),
            analysis=AnalysisConfig(**data.get("analysis", {})),
            candidate_models=data.get("candidate_models", CANDIDATE_MODELS),
            seed=data.get("seed", DEFAULT_SEED)
        )

def get_config() -> ProjectConfig:
    """Retrieve the global configuration singleton."""
    global _global_config
    if _global_config is None:
        with _config_lock:
            if _global_config is None:
                _global_config = ProjectConfig()
    return _global_config

def reset_config() -> None:
    """Reset the global configuration to defaults (useful for testing)."""
    global _global_config
    with _config_lock:
        _global_config = None

def set_seed(seed: int) -> None:
    """Set the global random seed for reproducibility."""
    config = get_config()
    config.seed = seed
    random.seed(seed)
    # Note: numpy and torch seeds should be set by the modules that use them
    # but we log the intent here.
    logging.getLogger(__name__).info(f"Global seed set to {seed}")

def get_project_root() -> Path:
    """Get the project root directory."""
    return get_config().project_root

def get_data_processed_path() -> Path:
    """Get the path to the processed data directory."""
    return get_config().data_processed

def get_data_results_path() -> Path:
    """Get the path to the results data directory."""
    return get_config().data_results

def get_data_logs_path() -> Path:
    """Get the path to the logs directory."""
    return get_config().data_logs

def get_candidate_models() -> List[str]:
    """Get the list of candidate LLMs."""
    return get_config().candidate_models

def get_runtime_limits() -> Dict[str, float]:
    """Get runtime limits as a dictionary."""
    cfg = get_config().runtime
    return {
        "max_runtime_hours": cfg.max_runtime_hours,
        "max_ram_gb": cfg.max_ram_gb,
        "batch_size": cfg.batch_size,
        "timeout_risk_threshold": cfg.timeout_risk_threshold
    }

def get_inference_params() -> Dict[str, Any]:
    """Get inference parameters as a dictionary."""
    cfg = get_config().inference
    return asdict(cfg)

def save_config_to_json(filepath: Optional[Path] = None) -> Path:
    """Save the current configuration to a JSON file."""
    if filepath is None:
        filepath = get_config().data_logs / "config_snapshot.json"
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    config_dict = get_config().to_dict()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2)
    
    return filepath

def load_config_from_json(filepath: Path) -> ProjectConfig:
    """Load configuration from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return ProjectConfig.from_dict(data)

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Log initialization
logger.info("Configuration module loaded.")
logger.info(f"Default seed: {DEFAULT_SEED}")
logger.info(f"Default runtime limits: {get_runtime_limits()}")
logger.info(f"Candidate models: {len(CANDIDATE_MODELS)} models registered.")