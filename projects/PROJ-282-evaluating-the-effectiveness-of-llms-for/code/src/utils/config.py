"""
Configuration management for the LLM Vulnerability Evaluation pipeline.
Implements FR-002 (Zero-Shot constraints) and SC-005 (Runtime thresholds).
"""
import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

# --- Constants & Defaults ---
DEFAULT_SEED = 42
DEFAULT_HOURLY_LIMIT_HOURS = 6.0
DEFAULT_RAM_CAP_GB = 14.0  # Conservative limit for CPU/low-bit inference
DEFAULT_BATCH_SIZE = 4

# Candidate LLMs compatible with Python, C, and JS (Zero-Shot)
# Selected for multi-language support and availability via HuggingFace
CANDIDATE_MODELS = [
    "microsoft/phi-2",           # Good general code understanding
    "Salesforce/codegen-6B-multi", # Trained on multiple languages
    "stabilityai/stable-code-3b", # Lightweight, multi-lang
    "bigcode/starcoderbase-1b"   # Very small, fast for CPU
]

# Root paths relative to project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RESULTS_DIR = DATA_DIR / "results"
DATA_HUMAN_REVIEW_DIR = DATA_DIR / "human_review"
STATE_DIR = ROOT_DIR / "state"
LOGS_DIR = ROOT_DIR / "logs"
FIGURES_DIR = ROOT_DIR / "figures"
SPECS_DIR = ROOT_DIR / "specs"

# File paths for contracts
DATASET_SCHEMA_PATH = SPECS_DIR / "contracts" / "dataset.schema.yaml"
FEATURE_SCHEMA_PATH = SPECS_DIR / "contracts" / "feature.schema.yaml"
PREDICTION_SCHEMA_PATH = SPECS_DIR / "contracts" / "prediction.schema.yaml"

@dataclass
class RuntimeConfig:
    """Runtime constraints to prevent pipeline failure."""
    hourly_limit_hours: float = DEFAULT_HOURLY_LIMIT_HOURS
    ram_cap_gb: float = DEFAULT_RAM_CAP_GB
    batch_size: int = DEFAULT_BATCH_SIZE
    max_retries: int = 3
    timeout_per_sample_seconds: float = 300.0

@dataclass
class InferenceConfig:
    """Configuration specific to LLM Inference."""
    model_name: str = "stabilityai/stable-code-3b"
    quantization_bits: int = 4
    device: str = "cpu"
    prompt_template: str = "Identify any security vulnerability in the following code:\n{code}"
    temperature: float = 0.0  # Deterministic for zero-shot
    max_new_tokens: int = 128
    # Mapping for ambiguous responses (FR-002)
    ambiguous_responses: List[str] = field(default_factory=lambda: [
        "maybe", "unclear", "possibly", "likely", "unknown error"
    ])

@dataclass
class AnalysisConfig:
    """Configuration for statistical analysis."""
    correlation_method: str = "pearson"
    p_value_threshold: float = 0.05
    correction_method: str = "benjamini_hochberg"  # FDR
    regression_model: str = "logistic"

@dataclass
class ProjectConfig:
    """Master configuration container."""
    seed: int = DEFAULT_SEED
    candidate_models: List[str] = field(default_factory=lambda: CANDIDATE_MODELS)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    paths: Dict[str, str] = field(default_factory=lambda: {
        "root": str(ROOT_DIR),
        "data_raw": str(DATA_RAW_DIR),
        "data_processed": str(DATA_PROCESSED_DIR),
        "data_results": str(DATA_RESULTS_DIR),
        "data_human_review": str(DATA_HUMAN_REVIEW_DIR),
        "state": str(STATE_DIR),
        "logs": str(LOGS_DIR),
        "figures": str(FIGURES_DIR),
        "specs": str(SPECS_DIR),
    })

    def __post_init__(self):
        # Ensure deterministic behavior
        random.seed(self.seed)
        # Validate paths exist (create if missing)
        for path_str in self.paths.values():
            p = Path(path_str)
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, path: Optional[Path] = None):
        """Save config to JSON."""
        if path is None:
            path = self.paths["state"] / "config.json"
        else:
            path = Path(path)
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'ProjectConfig':
        """Load config from JSON."""
        if path is None:
            path = cls().paths["state"] / "config.json"
        else:
            path = Path(path)

        if not path.exists():
            # Return default if not found
            return cls()

        with open(path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct nested objects
        runtime = RuntimeConfig(**data.get('runtime', {}))
        inference = InferenceConfig(**data.get('inference', {}))
        analysis = AnalysisConfig(**data.get('analysis', {}))
        
        return cls(
            seed=data.get('seed', DEFAULT_SEED),
            candidate_models=data.get('candidate_models', CANDIDATE_MODELS),
            runtime=runtime,
            inference=inference,
            analysis=analysis,
            paths=data.get('paths', {})
        )

# Global singleton instance for convenience
_config_instance: Optional[ProjectConfig] = None

def get_config() -> ProjectConfig:
    """Get or create the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ProjectConfig()
    return _config_instance

def reset_config():
    """Reset the global configuration (useful for testing)."""
    global _config_instance
    _config_instance = None

def get_project_root() -> Path:
    """Convenience wrapper for root path."""
    return get_config().paths["root"]

def get_data_processed_path() -> Path:
    """Convenience wrapper for processed data path."""
    return get_config().paths["data_processed"]

def get_data_results_path() -> Path:
    """Convenience wrapper for results path."""
    return get_config().paths["data_results"]

def get_candidate_models() -> List[str]:
    """Get the list of candidate LLMs."""
    return get_config().candidate_models

def get_runtime_limits() -> Dict[str, Any]:
    """Get runtime constraints."""
    cfg = get_config().runtime
    return {
        "hourly_limit_hours": cfg.hourly_limit_hours,
        "ram_cap_gb": cfg.ram_cap_gb,
        "batch_size": cfg.batch_size
    }

def get_inference_params() -> Dict[str, Any]:
    """Get inference specific parameters."""
    cfg = get_config().inference
    return asdict(cfg)
