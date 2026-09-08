"""
Configuration management for seeds, tolerances, and paths.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

def get_project_paths() -> Dict[str, Path]:
    """
    Get project directory paths.
    
    Returns:
        Dict mapping path names to Path objects
    """
    # Assume running from code/ directory or project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    return {
        'root': project_root,
        'code': project_root / 'code',
        'data': project_root / 'data',
        'raw': project_root / 'data' / 'raw',
        'processed': project_root / 'data' / 'processed',
        'logs': project_root / 'data' / 'logs',
        'figures': project_root / 'data' / 'figures',
        'state': project_root / 'state',
        'tests': project_root / 'tests',
    }

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to config file (default: project root config.json)
        
    Returns:
        Dict containing configuration values
    """
    if config_path is None:
        paths = get_project_paths()
        config_path = paths['root'] / 'config.json'
    
    if not config_path.exists():
        # Return default configuration if file doesn't exist
        return {
            'seed': 42,
            'tolerance': 1e-10,
            'matrix_size': 1000,
            'num_eigenvalues': 10,
            'perturbation_norm': 2.5,
            'sparsity_density': 0.1,
            'num_mc_iterations': 100
        }
    
    import json
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_directories() -> None:
    """Create all required project directories if they don't exist."""
    paths = get_project_paths()
    for path in paths.values():
        if path.name in ['raw', 'processed', 'logs', 'figures', 'state']:
            path.mkdir(parents=True, exist_ok=True)

def get_seed(config: Optional[Dict[str, Any]] = None) -> int:
    """Get random seed from config or environment."""
    if config is None:
        config = load_config()
    
    # Check environment variable first
    env_seed = os.environ.get('SIMULATION_SEED')
    if env_seed is not None:
        return int(env_seed)
    
    return config.get('seed', 42)

def get_tolerance(config: Optional[Dict[str, Any]] = None) -> float:
    """Get numerical tolerance from config."""
    if config is None:
        config = load_config()
    
    return config.get('tolerance', 1e-10)

def get_matrix_size(config: Optional[Dict[str, Any]] = None) -> int:
    """Get matrix size N from config."""
    if config is None:
        config = load_config()
    
    return config.get('matrix_size', 1000)

def get_num_eigenvalues(config: Optional[Dict[str, Any]] = None) -> int:
    """Get number of eigenvalues to compute from config."""
    if config is None:
        config = load_config()
    
    return config.get('num_eigenvalues', 10)

def get_perturbation_norm(config: Optional[Dict[str, Any]] = None) -> float:
    """Get perturbation norm (theta) from config."""
    if config is None:
        config = load_config()
    
    return config.get('perturbation_norm', 2.5)

def get_sparsity_density(config: Optional[Dict[str, Any]] = None) -> float:
    """Get sparsity density from config."""
    if config is None:
        config = load_config()
    
    return config.get('sparsity_density', 0.1)

def get_num_mc_iterations(config: Optional[Dict[str, Any]] = None) -> int:
    """Get number of Monte Carlo iterations from config."""
    if config is None:
        config = load_config()
    
    return config.get('num_mc_iterations', 100)
