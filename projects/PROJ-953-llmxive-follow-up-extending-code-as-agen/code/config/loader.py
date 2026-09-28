import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Config:
    """Base configuration holder for the llmXive pipeline."""
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    data_raw_dir: Path = field(init=False)
    data_processed_dir: Path = field(init=False)
    data_graphs_dir: Path = field(init=False)
    code_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    state_dir: Path = field(init=False)
    contracts_dir: Path = field(init=False)
    
    # Dataset paths (from env or defaults)
    swe_bench_dataset_name: str = field(default="princeton-nlp/SWE-bench_Lite")
    agent_bench_dataset_name: str = field(default="openbmb/AgentBench")
    swe_bench_split: str = field(default="test")
    agent_bench_split: str = field(default="dev")
    
    # Execution settings
    execution_timeout_seconds: int = field(default=300)
    max_retries: int = field(default=3)
    
    # Model settings
    random_seed: int = field(default=42)
    model_type: str = field(default="random_forest")
    
    # Thresholds for sensitivity analysis
    sensitivity_thresholds: list = field(default_factory=lambda: [0.01, 0.05, 0.1])

def __post_init__(self):
    """Initialize derived paths based on project_root."""
    self.data_raw_dir = self.project_root / "data" / "raw"
    self.data_processed_dir = self.project_root / "data" / "processed"
    self.data_graphs_dir = self.project_root / "data" / "graphs"
    self.code_dir = self.project_root / "code"
    self.models_dir = self.project_root / "models"
    self.state_dir = self.project_root / "state"
    self.contracts_dir = self.project_root / "contracts"

def get_dataset_path(self, dataset_type: str) -> str:
    """Get the dataset name/path from environment variables or defaults."""
    if dataset_type == "swe_bench":
        return os.getenv("LLMXIVE_SWE_BENCH_NAME", self.swe_bench_dataset_name)
    elif dataset_type == "agent_bench":
        return os.getenv("LLMXIVE_AGENT_BENCH_NAME", self.agent_bench_dataset_name)
    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}")

def validate_config(self) -> bool:
    """Validate that all required directories exist and are writable."""
    required_dirs = [
        self.data_raw_dir,
        self.data_processed_dir,
        self.data_graphs_dir,
        self.models_dir,
        self.state_dir,
        self.contracts_dir,
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            # Attempt to create if missing (optional, depending on strictness)
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except OSError:
                return False
        elif not os.access(dir_path, os.W_OK):
            return False
    
    return True

# Global config instance
_global_config: Optional[Config] = None

def get_config() -> Config:
    """Retrieve the current configuration, initializing from env if needed."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
        # Override with env vars if present
        if "LLMXIVE_PROJECT_ROOT" in os.environ:
            _global_config.project_root = Path(os.environ["LLMXIVE_PROJECT_ROOT"])
            # Re-trigger post_init logic manually since dataclass fields are frozen after init
            # We re-calculate derived paths
            _global_config.data_raw_dir = _global_config.project_root / "data" / "raw"
            _global_config.data_processed_dir = _global_config.project_root / "data" / "processed"
            _global_config.data_graphs_dir = _global_config.project_root / "data" / "graphs"
            _global_config.code_dir = _global_config.project_root / "code"
            _global_config.models_dir = _global_config.project_root / "models"
            _global_config.state_dir = _global_config.project_root / "state"
            _global_config.contracts_dir = _global_config.project_root / "contracts"
        
        # Override dataset names
        if "LLMXIVE_SWE_BENCH_NAME" in os.environ:
            _global_config.swe_bench_dataset_name = os.environ["LLMXIVE_SWE_BENCH_NAME"]
        if "LLMXIVE_AGENT_BENCH_NAME" in os.environ:
            _global_config.agent_bench_dataset_name = os.environ["LLMXIVE_AGENT_BENCH_NAME"]
        
        # Override execution timeout
        if "LLMXIVE_EXECUTION_TIMEOUT" in os.environ:
            try:
                _global_config.execution_timeout_seconds = int(os.environ["LLMXIVE_EXECUTION_TIMEOUT"])
            except ValueError:
                pass

    return _global_config

def get_global_config() -> Config:
    """Alias for get_config() to match API surface."""
    return get_config()

def validate_config(config: Optional[Config] = None) -> bool:
    """Validate the provided config or the global config."""
    if config is None:
        config = get_global_config()
    return config.validate_config()
