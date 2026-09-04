import os
from pathlib import Path
from typing import Any, Dict, Optional

# Default configuration values
DEFAULT_N_PERMUTATIONS = 1000
DEFAULT_RANDOM_SEED = 42
DEFAULT_DATA_SPLIT_RATIO = 0.2
DEFAULT_MIN_ROWS = 50
DEFAULT_MAX_ROWS = 10000
DEFAULT_OUTLIER_PERCENTILE = 99

# Environment variable names
ENV_N_PERMUTATIONS = "N_PERMUTATIONS"
ENV_RANDOM_SEED = "RANDOM_SEED"
ENV_DATA_SPLIT_RATIO = "DATA_SPLIT_RATIO"
ENV_MIN_ROWS = "MIN_ROWS"
ENV_MAX_ROWS = "MAX_ROWS"
ENV_OUTLIER_PERCENTILE = "OUTLIER_PERCENTILE"
ENV_PROJECT_ROOT = "PROJECT_ROOT"

def load_env_config(env_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables and .env file.
    
    Args:
        env_path: Path to .env file. If None, looks for .env in project root.
        
    Returns:
        Dictionary of configuration values with types converted appropriately.
    """
    config = {}
    
    # Load .env file if it exists
    if env_path is None:
        # Try to find .env in common locations
        possible_paths = [
            Path.cwd() / ".env",
            Path.cwd().parent / ".env",
            Path(__file__).parent.parent / ".env"
        ]
        for p in possible_paths:
            if p.exists():
                env_path = p
                break
    
    if env_path and env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")
    
    # Load configuration from environment variables with type conversion
    # N_PERMUTATIONS - integer, default 1000
    n_permutations = os.environ.get(ENV_N_PERMUTATIONS)
    if n_permutations is not None:
        try:
            config[ENV_N_PERMUTATIONS] = int(n_permutations)
        except ValueError:
            print(f"Warning: Invalid value for {ENV_N_PERMUTATIONS}, using default {DEFAULT_N_PERMUTATIONS}")
            config[ENV_N_PERMUTATIONS] = DEFAULT_N_PERMUTATIONS
    else:
        config[ENV_N_PERMUTATIONS] = DEFAULT_N_PERMUTATIONS
    
    # RANDOM_SEED - integer, default 42
    random_seed = os.environ.get(ENV_RANDOM_SEED)
    if random_seed is not None:
        try:
            config[ENV_RANDOM_SEED] = int(random_seed)
        except ValueError:
            print(f"Warning: Invalid value for {ENV_RANDOM_SEED}, using default {DEFAULT_RANDOM_SEED}")
            config[ENV_RANDOM_SEED] = DEFAULT_RANDOM_SEED
    else:
        config[ENV_RANDOM_SEED] = DEFAULT_RANDOM_SEED
    
    # DATA_SPLIT_RATIO - float, default 0.2
    data_split_ratio = os.environ.get(ENV_DATA_SPLIT_RATIO)
    if data_split_ratio is not None:
        try:
            config[ENV_DATA_SPLIT_RATIO] = float(data_split_ratio)
        except ValueError:
            print(f"Warning: Invalid value for {ENV_DATA_SPLIT_RATIO}, using default {DEFAULT_DATA_SPLIT_RATIO}")
            config[ENV_DATA_SPLIT_RATIO] = DEFAULT_DATA_SPLIT_RATIO
    else:
        config[ENV_DATA_SPLIT_RATIO] = DEFAULT_DATA_SPLIT_RATIO
    
    # MIN_ROWS - integer, default 50
    min_rows = os.environ.get(ENV_MIN_ROWS)
    if min_rows is not None:
        try:
            config[ENV_MIN_ROWS] = int(min_rows)
        except ValueError:
            print(f"Warning: Invalid value for {ENV_MIN_ROWS}, using default {DEFAULT_MIN_ROWS}")
            config[ENV_MIN_ROWS] = DEFAULT_MIN_ROWS
    else:
        config[ENV_MIN_ROWS] = DEFAULT_MIN_ROWS
    
    # MAX_ROWS - integer, default 10000
    max_rows = os.environ.get(ENV_MAX_ROWS)
    if max_rows is not None:
        try:
            config[ENV_MAX_ROWS] = int(max_rows)
        except ValueError:
            print(f"Warning: Invalid value for {ENV_MAX_ROWS}, using default {DEFAULT_MAX_ROWS}")
            config[ENV_MAX_ROWS] = DEFAULT_MAX_ROWS
    else:
        config[ENV_MAX_ROWS] = DEFAULT_MAX_ROWS
    
    # OUTLIER_PERCENTILE - integer, default 99
    outlier_percentile = os.environ.get(ENV_OUTLIER_PERCENTILE)
    if outlier_percentile is not None:
        try:
            config[ENV_OUTLIER_PERCENTILE] = int(outlier_percentile)
        except ValueError:
            print(f"Warning: Invalid value for {ENV_OUTLIER_PERCENTILE}, using default {DEFAULT_OUTLIER_PERCENTILE}")
            config[ENV_OUTLIER_PERCENTILE] = DEFAULT_OUTLIER_PERCENTILE
    else:
        config[ENV_OUTLIER_PERCENTILE] = DEFAULT_OUTLIER_PERCENTILE
    
    # PROJECT_ROOT - string, default current directory
    project_root = os.environ.get(ENV_PROJECT_ROOT)
    if project_root is not None:
        config[ENV_PROJECT_ROOT] = Path(project_root)
    else:
        config[ENV_PROJECT_ROOT] = Path.cwd()
    
    return config

def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Get a configuration value from the config dictionary.
    
    Args:
        config: Configuration dictionary (from load_env_config)
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    return config.get(key, default)

def get_n_permutations(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get N_PERMUTATIONS configuration value.
    
    Args:
        config: Optional configuration dictionary. If None, loads fresh config.
        
    Returns:
        Number of permutations for statistical tests
    """
    if config is None:
        config = load_env_config()
    return config.get(ENV_N_PERMUTATIONS, DEFAULT_N_PERMUTATIONS)

def get_random_seed(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get RANDOM_SEED configuration value.
    
    Args:
        config: Optional configuration dictionary. If None, loads fresh config.
        
    Returns:
        Random seed value
    """
    if config is None:
        config = load_env_config()
    return config.get(ENV_RANDOM_SEED, DEFAULT_RANDOM_SEED)

def get_data_split_ratio(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get DATA_SPLIT_RATIO configuration value.
    
    Args:
        config: Optional configuration dictionary. If None, loads fresh config.
        
    Returns:
        Data split ratio (test set proportion)
    """
    if config is None:
        config = load_env_config()
    return config.get(ENV_DATA_SPLIT_RATIO, DEFAULT_DATA_SPLIT_RATIO)

def get_min_rows(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get MIN_ROWS configuration value.
    
    Args:
        config: Optional configuration dictionary. If None, loads fresh config.
        
    Returns:
        Minimum required rows in dataset
    """
    if config is None:
        config = load_env_config()
    return config.get(ENV_MIN_ROWS, DEFAULT_MIN_ROWS)

def get_max_rows(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get MAX_ROWS configuration value.
    
    Args:
        config: Optional configuration dictionary. If None, loads fresh config.
        
    Returns:
        Maximum allowed rows in dataset
    """
    if config is None:
        config = load_env_config()
    return config.get(ENV_MAX_ROWS, DEFAULT_MAX_ROWS)

def get_outlier_percentile(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get OUTLIER_PERCENTILE configuration value.
    
    Args:
        config: Optional configuration dictionary. If None, loads fresh config.
        
    Returns:
        Percentile for outlier clipping
    """
    if config is None:
        config = load_env_config()
    return config.get(ENV_OUTLIER_PERCENTILE, DEFAULT_OUTLIER_PERCENTILE)

def get_project_root(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get PROJECT_ROOT configuration value.
    
    Args:
        config: Optional configuration dictionary. If None, loads fresh config.
        
    Returns:
        Project root path
    """
    if config is None:
        config = load_env_config()
    return config.get(ENV_PROJECT_ROOT, Path.cwd())
