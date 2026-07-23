import os
import random
import subprocess
import sys
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# ============================================================================
# Paths Configuration
# ============================================================================

@dataclass
class Paths:
    """
    Centralized path management for the project.
    Implements a tolerant attribute access pattern to support various
    calling conventions across the codebase.
    """
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_root: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")
    code_root: Path = field(default_factory=lambda: Path(__file__).parent)
    tests_root: Path = field(default_factory=lambda: Path(__file__).parent.parent / "tests")
    specs_root: Path = field(default_factory=lambda: Path(__file__).parent.parent / "specs")

    # Data Subdirectories
    data_raw: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "raw")
    data_processed: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "processed")
    data_figures: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "figures")

    # Specific file paths
    config_file: Path = field(default_factory=lambda: Path(__file__).parent / "config.yaml")
    state_file: Path = field(default_factory=lambda: Path(__file__).parent.parent / "state.yaml")

    # Legacy/Alternative attribute names for compatibility
    # These are added explicitly to satisfy various callers that might look for these names
    DATA_RAW: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "raw")
    DATA_PROCESSED: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "processed")
    DATA_FIGURES: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "figures")
    CODE_ROOT: Path = field(default_factory=lambda: Path(__file__).parent)
    TESTS_ROOT: Path = field(default_factory=lambda: Path(__file__).parent.parent / "tests")
    SPECS_ROOT: Path = field(default_factory=lambda: Path(__file__).parent.parent / "specs")

    # Local path for dataset (used by loader)
    LOCAL_PATH: Optional[Path] = None

    def __post_init__(self):
        # Ensure LOCAL_PATH is initialized if not set
        if self.LOCAL_PATH is None:
            self.LOCAL_PATH = self.data_raw

    def __getattr__(self, name: str) -> Any:
        """
        Tolerant attribute access.
        If an attribute is not found, return a no-op callable for logger-like usage
        or raise AttributeError for actual missing attributes (to catch bugs).
        """
        # Common logger-like methods that should be no-ops if missing
        logger_methods = ['info', 'debug', 'warning', 'error', 'critical', 'log', 'exception', 'trace']
        if name in logger_methods:
            def _noop(*args, **kwargs):
                return None
            return _noop
        
        # For other attributes, raise the standard error
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def ensure_directories(self):
        """Create all required directories if they don't exist."""
        for path in [
            self.data_raw, self.data_processed, self.data_figures,
            self.code_root, self.tests_root, self.specs_root
        ]:
            path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Resource Limits Configuration
# ============================================================================

@dataclass
class ResourceLimits:
    """Resource limits for the execution environment."""
    max_cpu_percent: float = 90.0
    max_ram_gb: float = 6.5
    timeout_seconds: int = 3600  # 1 hour default timeout
    max_threads: int = 4

# ============================================================================
# Model Configuration
# ============================================================================

@dataclass
class ModelConfig:
    """Configuration for ML models."""
    model_name: str = "phi-3-mini"
    device: str = "cpu"
    dtype: str = "float32"
    max_length: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    seed: int = 42

# ============================================================================
# Dataset Configuration
# ============================================================================

@dataclass
class DatasetConfig:
    """Configuration for datasets."""
    # AdaPlanBench Configuration
    dataset_name: str = "AdaPlanBench"
    dataset_id: str = "llmXive/AdaPlanBench"  # HuggingFace dataset ID
    dataset_url: str = "https://huggingface.co/datasets/llmXive/AdaPlanBench"
    dataset_local_path: Optional[Path] = None
    
    # Fallback URLs for official sources
    official_url_fallbacks: List[str] = field(default_factory=lambda: [
        "https://huggingface.co/datasets/llmXive/AdaPlanBench",
        "https://raw.githubusercontent.com/llmXive/AdaPlanBench/main/data.json"
    ])
    
    # Filter configuration
    min_progressive_constraints: int = 5
    max_samples: Optional[int] = None  # None means all samples
    
    # Data loading options
    streaming: bool = False
    trust_remote_code: bool = False

# ============================================================================
# Analysis Configuration
# ============================================================================

@dataclass
class AnalysisConfig:
    """Configuration for statistical analysis."""
    # GLMM Configuration
    glmm_alpha: float = 0.05
    glmm_max_iter: int = 100
    glmm_tol: float = 1e-6
    
    # Power Analysis Configuration
    power_effect_size: float = 0.15
    power_alpha: float = 0.05
    power_groups: int = 2
    
    # Annotation Configuration
    annotation_seed: int = 42
    annotation_sample_size: Optional[int] = None
    annotation_bins: List[int] = field(default_factory=lambda: [5, 6, 7])  # [5, 6, 7+]
    
    # Adherence Threshold
    adherence_threshold: float = 0.85

# ============================================================================
# Global Configuration Management
# ============================================================================

_paths: Optional[Paths] = None
_resource_limits: Optional[ResourceLimits] = None
_model_config: Optional[ModelConfig] = None
_dataset_config: Optional[DatasetConfig] = None
_analysis_config: Optional[AnalysisConfig] = None
_logger: Optional[logging.Logger] = None

def get_paths() -> Paths:
    """Get or create the global Paths instance."""
    global _paths
    if _paths is None:
        _paths = Paths()
    return _paths

def get_resource_limits() -> ResourceLimits:
    """Get or create the global ResourceLimits instance."""
    global _resource_limits
    if _resource_limits is None:
        _resource_limits = ResourceLimits()
    return _resource_limits

def get_model_config() -> ModelConfig:
    """Get or create the global ModelConfig instance."""
    global _model_config
    if _model_config is None:
        _model_config = ModelConfig()
    return _model_config

def get_dataset_config() -> DatasetConfig:
    """Get or create the global DatasetConfig instance."""
    global _dataset_config
    if _dataset_config is None:
        _dataset_config = DatasetConfig()
    return _dataset_config

def get_analysis_config() -> AnalysisConfig:
    """Get or create the global AnalysisConfig instance."""
    global _analysis_config
    if _analysis_config is None:
        _analysis_config = AnalysisConfig()
    return _analysis_config

def set_all_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: torch and numpy seeds would be set in modules that import them
    # to avoid circular imports here.

def ensure_directories():
    """Ensure all required directories exist."""
    paths = get_paths()
    paths.ensure_directories()

def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable with an optional default."""
    return os.environ.get(name, default)

def parse_bool(value: Union[str, bool]) -> bool:
    """Parse a boolean value from string or bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)

# ============================================================================
# Project Logger
# ============================================================================

class ProjectLogger:
    """A simple project logger that can be used across modules."""
    
    def __init__(self, name: str = "llmXive"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)

def get_logger(name: str = "llmXive") -> ProjectLogger:
    """Get or create a project logger."""
    global _logger
    if _logger is None:
        _logger = ProjectLogger(name)
    return _logger