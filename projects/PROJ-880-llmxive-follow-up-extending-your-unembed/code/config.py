import os
from pathlib import Path
from typing import Dict, Any, Optional

# Default paths relative to project root
DEFAULT_CONFIG = {
    'project_root': Path(__file__).resolve().parent.parent,
    'data_raw_dir': 'data/raw',
    'data_processed_dir': 'data/processed',
    'figures_dir': 'figures',
    'models_dir': 'data/models',
    
    # Output paths
    'similarity_matrix_path': 'data/processed/similarity_matrix.json',
    'anisotropy_deviation_path': 'data/processed/anisotropy_deviation.json',
    'permutation_result_path': 'data/processed/permutation_result.json',
    'wals_validation_path': 'data/processed/wals_validation.json',
    'run_summary_path': 'data/processed/run_summary.json',
    
    # Hyperparameters
    'hyperparameters': {
        'k': 100,                # Number of singular vectors
        'n_bootstrap': 1000,     # Number of bootstrap iterations
        'vocab_sample_size': 10, # For profiling (T008a)
        'seed': 42
    },
    
    # Model paths (placeholders, to be overridden or downloaded)
    'model_names': ['Llama-3', 'Mistral', 'BLOOM'],
    'model_ids': {
        'Llama-3': 'meta-llama/Meta-Llama-3-8B',
        'Mistral': 'mistralai/Mistral-7B-v0.1',
        'BLOOM': 'bigscience/bloom-560m'
    }
}

_config_cache = None

def load_config() -> Dict[str, Any]:
    """Load configuration, merging defaults with any environment overrides."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    
    # In a real implementation, we might load from a YAML/JSON file
    # For now, we use the defaults
    _config_cache = DEFAULT_CONFIG
    return _config_cache

def get_path(config: Dict[str, Any], key: str) -> Path:
    """Get a resolved absolute path for a given config key."""
    if key not in config:
        raise KeyError(f"Config key '{key}' not found.")
    
    path_str = config[key]
    root = config.get('project_root', Path.cwd())
    
    if isinstance(path_str, Path):
        return path_str
    
    # Handle relative paths
    if not os.path.isabs(path_str):
        return root / path_str
    return Path(path_str)

def get_hyperparameter(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get a hyperparameter value."""
    hps = config.get('hyperparameters', {})
    return hps.get(key, default)

def get_seed(config: Dict[str, Any]) -> int:
    """Get the random seed."""
    return get_hyperparameter(config, 'seed', 42)

def ensure_dirs(config: Dict[str, Any], paths: Optional[list] = None) -> None:
    """Ensure all required directories exist."""
    dirs_to_create = [
        get_path(config, 'data_raw_dir'),
        get_path(config, 'data_processed_dir'),
        get_path(config, 'figures_dir'),
        get_path(config, 'models_dir')
    ]
    
    if paths:
        for p in paths:
            if isinstance(p, str):
                dirs_to_create.append(get_path(config, p))
            elif isinstance(p, Path):
                dirs_to_create.append(p)
    
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)

def get_path_str(config: Dict[str, Any], key: str) -> str:
    """Get path as string."""
    return str(get_path(config, key))

def update_hyperparameters(config: Dict[str, Any], updates: Dict[str, Any]) -> None:
    """Update hyperparameters in place."""
    if 'hyperparameters' not in config:
        config['hyperparameters'] = {}
    config['hyperparameters'].update(updates)

def update_paths(config: Dict[str, Any], updates: Dict[str, Any]) -> None:
    """Update paths in place."""
    config.update(updates)

def main():
    """Simple CLI to print config."""
    config = load_config()
    print("Current Configuration:")
    for k, v in config.items():
        print(f"  {k}: {v}")

if __name__ == '__main__':
    main()