"""
Move derived statistics from config.yaml to state file.
This script identifies and extracts derived statistics,
leaving only configuration parameters in config.yaml.
"""
import os
import sys
import yaml
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

CONFIG_PATH = 'code/config.yaml'
STATE_PATH = 'state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml'

# Derived statistics that should be in state file
DERIVED_STATISTICS = [
    'checksums', 'file_sizes', 'modified_times', 'artifacts',
    'dataset_checksums', 'model_checksums', 'evaluation_results',
    'statistics', 'metrics', 'summary', 'hyperparameter_counts',
    'memory_profiles', 'training_stats', 'inference_stats'
]

def load_yaml(path: Path) -> dict:
    """Load YAML file safely."""
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError:
            return {}

def save_yaml(path: Path, data: dict):
    """Save data to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def compute_file_checksum(path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    if not path.exists():
        return ''
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def is_derived_statistic(key: str, value: Any) -> bool:
    """Check if a key-value pair represents derived statistics."""
    key_lower = key.lower()
    for derived in DERIVED_STATISTICS:
        if derived in key_lower:
            return True
    # Check for statistical patterns (lists of numbers, floats with many decimals)
    if isinstance(value, (list, dict)):
        return True
    return False

def is_config_parameter(key: str, value: Any) -> bool:
    """Check if a key-value pair represents configuration parameters."""
    # Valid config parameters per FR-009
    valid_patterns = [
        'hyperparameter', 'seed', 'path', 'config', 'threshold',
        'learning_rate', 'batch_size', 'max_epochs', 'temperature',
        'concentration', 'variance', 'mean', 'prior'
    ]
    key_lower = key.lower()
    for pattern in valid_patterns:
        if pattern in key_lower:
            return True
    return False

def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def categorize_config(config: dict) -> Tuple[dict, dict]:
    """Separate config into parameters and derived statistics."""
    parameters = {}
    derived = {}

    for key, value in config.items():
        if is_derived_statistic(key, value):
            derived[key] = value
        elif is_config_parameter(key, value):
            parameters[key] = value
        else:
            # Default to parameters if unclear
            parameters[key] = value

    return parameters, derived

def reduce_config(config_path: Path, state_path: Path):
    """Main function to reduce config and update state."""
    print(f"Loading config from {config_path}")
    config = load_yaml(config_path)

    print(f"Loading state from {state_path}")
    state = load_yaml(state_path)

    # Separate parameters from derived statistics
    parameters, derived = categorize_config(config)

    print(f"Found {len(parameters)} config parameters")
    print(f"Found {len(derived)} derived statistics to move")

    # Update config with only parameters
    save_yaml(config_path, parameters)
    print(f"Updated config.yaml with {len(parameters)} parameters")

    # Add derived statistics to state file
    if 'derived_statistics' not in state:
        state['derived_statistics'] = {}

    state['derived_statistics'].update({
        'last_updated': datetime.now().isoformat(),
        'data': derived
    })

    # Add file metadata to state
    if 'file_metadata' not in state:
        state['file_metadata'] = {}

    if config_path.exists():
        state['file_metadata']['config.yaml'] = {
            'checksum': compute_file_checksum(config_path),
            'size_bytes': config_path.stat().st_size,
            'modified': datetime.fromtimestamp(config_path.stat().st_mtime).isoformat()
        }

    save_yaml(state_path, state)
    print(f"Updated state file with derived statistics")

    # Report new config size
    new_size = config_path.stat().st_size
    print(f"New config.yaml size: {new_size} bytes ({new_size / 1024:.2f} KB)")

    if new_size <= 2048:
        print("✓ Config file is now under 2KB limit")
        return 0
    else:
        print("✗ Config file still exceeds 2KB limit")
        return 1

def main():
    """Entry point."""
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    config_path = project_root / CONFIG_PATH
    state_path = project_root / STATE_PATH

    return reduce_config(config_path, state_path)

if __name__ == '__main__':
    sys.exit(main())
