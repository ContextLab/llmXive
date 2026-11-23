"""
Configuration management for the MOND analysis pipeline.
"""
import os
import yaml
from pathlib import Path

def ensure_dirs():
    """Create required project directories if they don't exist."""
    dirs = ['code', 'data', 'data/raw', 'data/processed', 'results', 'tests', 'state']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    return dirs

def load_config(path='data/metadata.yaml'):
    """Load configuration from a YAML file."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_config():
    """Get the global configuration (lazy load)."""
    if not hasattr(get_config, '_cache'):
        get_config._cache = load_config()
    return get_config._cache

def create_default_metadata():
    """Create a default metadata.yaml file if it doesn't exist."""
    metadata_path = Path('data/metadata.yaml')
    if not metadata_path.exists():
        default_meta = {
            'project': 'PROJ-076-assessing-the-validity-of-modified-newto',
            'version': '1.0.0',
            'data_source': 'SPARC',
            'download_timestamp': None,
            'processing_timestamp': None
        }
        with open(metadata_path, 'w') as f:
            yaml.dump(default_meta, f, default_flow_style=False)
        return default_meta
    return load_config()
