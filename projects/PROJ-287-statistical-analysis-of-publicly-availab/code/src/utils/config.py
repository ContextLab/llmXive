import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar
import numpy as np

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

T = TypeVar('T')

def load_env_variable(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Load an environment variable.
    
    Args:
        name: The name of the environment variable.
        default: Default value if the variable is not set.
        required: If True, raise ConfigError if the variable is missing.
        
    Returns:
        The value of the environment variable or the default.
        
    Raises:
        ConfigError: If the variable is required but not found.
    """
    value = os.getenv(name, default)
    if value is None and required:
        raise ConfigError(f"Required environment variable '{name}' is not set.")
    return value

def get_random_seed(seed_name: str = "RANDOM_SEED") -> int:
    """
    Get a random seed from the environment or generate one.
    
    This function ensures reproducibility by allowing the seed to be
    set via an environment variable. If not set, a random seed is generated.
    
    Args:
        seed_name: The name of the environment variable holding the seed.
        
    Returns:
        An integer random seed.
    """
    seed_str = os.getenv(seed_name)
    if seed_str:
        try:
            seed = int(seed_str)
        except ValueError:
            raise ConfigError(f"Environment variable '{seed_name}' must be an integer.")
    else:
        seed = random.randint(0, 2**32 - 1)
        # Optionally log this if a logger were available here, but we avoid circular imports
        # print(f"No seed set in env, generating random seed: {seed}")
    
    # Set seeds for reproducibility across libraries
    random.seed(seed)
    np.random.seed(seed)
    
    return seed

def get_config_dict() -> Dict[str, Any]:
    """
    Load a configuration dictionary from environment variables or defaults.
    
    This aggregates common configuration parameters used throughout the pipeline.
    
    Returns:
        A dictionary containing configuration parameters.
    """
    config = {
        "random_seed": get_random_seed(),
        "data_raw_dir": os.getenv("DATA_RAW_DIR", "data/raw"),
        "data_processed_dir": os.getenv("DATA_PROCESSED_DIR", "data/processed"),
        "results_figures_dir": os.getenv("RESULTS_FIGURES_DIR", "results/figures"),
        "results_stats_dir": os.getenv("RESULTS_STATS_DIR", "results/stats"),
        "manifest_path": os.getenv("MANIFEST_PATH", "results/manifest.json"),
        "arxiv_api_url": os.getenv("ARXIV_API_URL", "http://export.arxiv.org/api/query"),
        "pubmed_api_url": os.getenv("PUBMED_API_URL", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"),
        "year_start": int(os.getenv("YEAR_START", "2000")),
        "year_end": int(os.getenv("YEAR_END", "2024")),
        "min_tokens": int(os.getenv("MIN_TOKENS", "20")),
        "k_topics": int(os.getenv("K_TOPICS", "10")),
        "max_iter_lda": int(os.getenv("MAX_ITER_LDA", "20")),
        "coherence_threshold": float(os.getenv("COHERENCE_THRESHOLD", "0.4")),
        "permutation_iterations": int(os.getenv("PERMUTATION_ITERATIONS", "1000")),
        "permutation_sample_size": int(os.getenv("PERMUTATION_SAMPLE_SIZE", "2000")),
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),
        "timeout_seconds": int(os.getenv("TIMEOUT_SECONDS", "30")),
    }
    return config

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Ensure that all required directories exist based on the configuration.
    
    Args:
        config: A configuration dictionary. If None, loads defaults.
        
    Raises:
        ConfigError: If a directory cannot be created.
    """
    if config is None:
        config = get_config_dict()
    
    directories = [
        config.get("data_raw_dir"),
        config.get("data_processed_dir"),
        config.get("results_figures_dir"),
        config.get("results_stats_dir"),
    ]
    
    for dir_path in directories:
        if dir_path:
            path = Path(dir_path)
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ConfigError(f"Failed to create directory '{dir_path}': {e}")