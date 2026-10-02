import os
import random
import numpy as np
import torch
import re
import logging
from typing import Optional, Dict, Any, List

# Configure logging for the module
logger = logging.getLogger(__name__)

class Hyperparameters:
    """Container for training hyperparameters."""
    def __init__(self, lr: float = 5e-5, batch_size: int = 4, seed: int = 42, epochs: int = 1):
        self.lr = lr
        self.batch_size = batch_size
        self.seed = seed
        self.epochs = epochs

class SafetyConstraints:
    """Container for safety and resource constraints."""
    def __init__(self, max_ram_gb: float = 7.0, max_param_increase_ratio: Optional[float] = None):
        self.max_ram_gb = max_ram_gb
        # If None, it means the value is deferred or not yet determined by research
        self.max_param_increase_ratio = max_param_increase_ratio

class PathConfig:
    """Container for project directory paths."""
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.data_raw = os.path.join(base_dir, "data", "raw")
        self.data_processed = os.path.join(base_dir, "data", "processed")
        self.results = os.path.join(base_dir, "results")
        self.state = os.path.join(base_dir, "state")
        self.code = os.path.join(base_dir, "code")
        self.research_md = os.path.join(base_dir, "research.md")

class Config:
    """Master configuration object."""
    def __init__(self, hyperparams: Hyperparameters, safety: SafetyConstraints, paths: PathConfig):
        self.hyperparams = hyperparams
        self.safety = safety
        self.paths = paths

# Global configuration instance
_config: Optional[Config] = None

def _parse_research_md_for_param_limit(research_path: str) -> Optional[float]:
    """
    Parses research.md to find a defined MAX_PARAM_INCREASE_RATIO.
    Looks for patterns like 'MAX_PARAM_INCREASE_RATIO: 0.25' or 'ratio: 0.25'
    in the 'Methodology for Parameter Limit' section.
    Returns None if not found or if the value is marked as deferred.
    """
    if not os.path.exists(research_path):
        logger.warning(f"research.md not found at {research_path}. Using default/provisional constraints.")
        return None

    try:
        with open(research_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the methodology section exists
        if "## Methodology for Parameter Limit" not in content:
            logger.warning("Methodology for Parameter Limit section not found in research.md.")
            return None

        # Simple regex to find a float value associated with param limit
        # Matches patterns like "0.25", "ratio: 0.25", "limit: 0.25"
        # We look for a float in the vicinity of the section header
        section_start = content.find("## Methodology for Parameter Limit")
        if section_start == -1:
            return None
        
        # Look within the next 2000 characters for a ratio definition
        section_content = content[section_start : section_start + 2000]
        
        # Check for deferred markers first
        if "[deferred]" in section_content.lower() or "deferred" in section_content.lower():
            logger.info("Parameter limit found as [deferred] in research.md.")
            return None

        # Try to find a specific float value
        # Pattern: number (possibly with leading 0.)
        pattern = r'(?:ratio|limit|max_param|increase).*[:\s=]+([0-9]*\.?[0-9]+)'
        matches = re.findall(pattern, section_content, re.IGNORECASE)
        
        if matches:
            try:
                val = float(matches[0])
                if 0.0 < val <= 1.0:
                    logger.info(f"Found defined parameter increase ratio {val} in research.md.")
                    return val
            except ValueError:
                pass
        
        logger.warning("No valid numeric parameter limit found in research.md methodology section.")
        return None

    except Exception as e:
        logger.error(f"Error parsing research.md for parameter limit: {e}")
        return None

def get_config() -> Config:
    """Returns the global configuration, initializing it if necessary."""
    global _config
    if _config is None:
        _config = _init_config()
    return _config

def set_config(cfg: Config) -> None:
    """Sets the global configuration."""
    global _config
    _config = cfg

def _init_config() -> Config:
    """Initializes the configuration with defaults and research overrides."""
    base_dir = os.getenv("PROJECT_ROOT", ".")
    
    # Initialize paths
    paths = PathConfig(base_dir)
    
    # Initialize safety constraints
    # Default provisional value is 0.30, but we check research.md first
    research_path = paths.research_md
    param_ratio = _parse_research_md_for_param_limit(research_path)
    
    if param_ratio is None:
        # If research.md doesn't define it, we use None (deferred) or a provisional default
        # The task says: set to None (or '[DEFERRED]') and log a warning that default 0.30 is provisional.
        # We will store None to indicate it's not set, and the system should handle the default logic where used.
        # However, for the SafetyConstraints object, we can store a provisional default if needed, 
        # but the task implies we should reflect the "deferred" state.
        # Let's store None to represent "not defined by research", and let consumers handle the 0.30 default.
        # But the task says: "set to None (or '[DEFERRED]')". We'll use None.
        safety = SafetyConstraints(max_param_increase_ratio=None)
        logger.warning("MAX_PARAM_INCREASE_RATIO not defined in research.md. Using None (provisional default 0.30 must be handled by consumers).")
    else:
        safety = SafetyConstraints(max_param_increase_ratio=param_ratio)

    # Initialize hyperparameters
    hyperparams = Hyperparameters(
        lr=5e-5,
        batch_size=4,
        seed=42,
        epochs=1
    )

    return Config(hyperparams, safety, paths)

def get_learning_rate() -> float:
    """Returns the learning rate from the global config."""
    return get_config().hyperparams.lr

def get_batch_size() -> int:
    """Returns the batch size from the global config."""
    return get_config().hyperparams.batch_size

def get_seed() -> int:
    """Returns the random seed from the global config."""
    return get_config().hyperparams.seed

def get_ram_limit() -> float:
    """Returns the RAM limit in GB from the global config."""
    return get_config().safety.max_ram_gb

def get_trajectory_path() -> str:
    """Returns the path to the trajectory file."""
    return os.path.join(get_config().paths.results, "trajectory.json")

def get_max_param_increase_percent() -> Optional[float]:
    """
    Returns the max parameter increase ratio.
    If research.md defined a value, returns it.
    If not, returns None (indicating the provisional 0.30 default is in effect but not formally set).
    """
    return get_config().safety.max_param_increase_ratio

def get_bootstrap_resamples() -> int:
    """Returns the number of bootstrap resamples for statistical testing."""
    return 1000  # Default, can be made configurable

def set_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def ensure_directories() -> None:
    """Creates all required directories defined in PathConfig."""
    cfg = get_config()
    dirs = [
        cfg.paths.data_raw,
        cfg.paths.data_processed,
        cfg.paths.results,
        cfg.paths.state
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        logger.debug(f"Ensured directory exists: {d}")
