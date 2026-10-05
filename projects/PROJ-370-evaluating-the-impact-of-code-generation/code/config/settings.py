import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Configuration dictionary
CONFIG = {
    'target_repos': [
        'microsoft/vscode',
        'psf/requests',
        'pallets/flask',
        'numpy/numpy',
        'scikit-learn/scikit-learn'
    ],
    'github_token': os.getenv('GITHUB_TOKEN', ''),
    'max_retries': 3,
    'retry_delay_seconds': 2,
    'timeout_seconds': 300,
    'random_seed': 42,
    'max_prs_per_repo': 100,
    'context_window_tokens': 4096,
    'truncation_strategy': 'tail',
    'llm_model_id': 'bigcode/starcoder2-3b',
    'max_memory_gb': 7,
    'alignment_similarity_threshold': 0.85,
    'jaccard_threshold': 0.5,
    'line_shift_tolerance': 5,
}

def get_config() -> Dict[str, Any]:
    """Get the full configuration dictionary."""
    return CONFIG.copy()

def get_target_repos() -> List[str]:
    """Get the list of target repositories."""
    return CONFIG['target_repos'].copy()

def get_paths() -> Dict[str, Path]:
    """Get all project paths."""
    return {
        'project_root': PROJECT_ROOT,
        'code': PROJECT_ROOT / 'code',
        'data_raw': PROJECT_ROOT / 'data' / 'raw',
        'data_derived': PROJECT_ROOT / 'data' / 'derived',
        'data_annotations': PROJECT_ROOT / 'data' / 'annotations',
        'results': PROJECT_ROOT / 'results',
        'tests': PROJECT_ROOT / 'tests',
        'specs': PROJECT_ROOT / 'specs',
        'logs': PROJECT_ROOT / 'logs',
        'state': PROJECT_ROOT / 'state',
        'figures': PROJECT_ROOT / 'figures',
    }

def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    paths = get_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

def save_config(config_path: Path) -> None:
    """Save configuration to a JSON file."""
    with open(config_path, 'w') as f:
        json.dump(CONFIG, f, indent=2)

def load_config(config_path: Path) -> None:
    """Load configuration from a JSON file."""
    if config_path.exists():
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)
            CONFIG.update(loaded_config)
