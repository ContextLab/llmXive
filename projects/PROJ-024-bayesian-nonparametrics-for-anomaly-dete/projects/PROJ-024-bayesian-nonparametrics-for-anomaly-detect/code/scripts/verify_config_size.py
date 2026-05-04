"""
Verify config.yaml stays under 2KB and derived statistics are in state file.
Per FR-009: config.yaml should contain only hyperparameters, seeds, and dataset paths.
Derived statistics (checksums, file sizes, timestamps) belong in state file.
"""
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

CONFIG_SIZE_LIMIT = 2048  # 2KB in bytes

# Derived statistics that should NOT be in config.yaml
DERIVED_STATISTICS = [
    'checksums',
    'file_sizes',
    'modified_times',
    'artifacts',
    'dataset_checksums',
    'model_checksums',
    'evaluation_results',
    'statistics',
    'metrics',
    'summary',
    'hyperparameter_counts',
    'memory_profiles'
]

# Valid config parameters per FR-009
VALID_CONFIG_PARAMS = [
    'hyperparameters',
    'random_seeds',
    'dataset_paths',
    'model_config',
    'training_config',
    'inference_config',
    'logging_config',
    'threshold_config',
    'baseline_config'
]

def check_config_file_size(config_path: Path) -> dict:
    """Check if config.yaml is under 2KB limit."""
    if not config_path.exists():
        return {
            'exists': False,
            'size_bytes': 0,
            'within_limit': True,
            'message': f'Config file not found at {config_path}'
        }

    size_bytes = config_path.stat().st_size
    within_limit = size_bytes <= CONFIG_SIZE_LIMIT

    return {
        'exists': True,
        'size_bytes': size_bytes,
        'within_limit': within_limit,
        'message': f'Config size: {size_bytes} bytes ({size_bytes / 1024:.2f} KB)'
                   f' - {"PASS" if within_limit else "FAIL: exceeds 2KB limit"}'
    }

def check_derived_statistics_in_config(config_path: Path) -> dict:
    """Check that derived statistics are NOT in config.yaml."""
    if not config_path.exists():
        return {
            'found_derived': False,
            'derived_keys': [],
            'message': 'Config file not found'
        }

    with open(config_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return {
                'found_derived': False,
                'derived_keys': [],
                'message': f'Failed to parse config.yaml: {e}'
            }

    if not isinstance(config, dict):
        return {
            'found_derived': False,
            'derived_keys': [],
            'message': 'Config is not a dictionary'
        }

    # Check top-level keys
    derived_found = []
    for key in config.keys():
        if key.lower() in [d.lower() for d in DERIVED_STATISTICS]:
            derived_found.append(key)

    # Check nested keys in common sections
    for section in ['hyperparameters', 'training_config', 'model_config']:
        if section in config and isinstance(config[section], dict):
            for key in config[section].keys():
                if key.lower() in [d.lower() for d in DERIVED_STATISTICS]:
                    derived_found.append(f'{section}.{key}')

    return {
        'found_derived': len(derived_found) > 0,
        'derived_keys': derived_found,
        'message': f"Found {len(derived_found)} derived statistics in config.yaml"
                   f" - {'FAIL: move to state file' if derived_found else 'PASS: no derived stats'}"
    }

def verify_state_file_exists(state_path: Path) -> dict:
    """Verify state file exists for storing derived statistics."""
    exists = state_path.exists()
    return {
        'exists': exists,
        'message': f"State file {'found' if exists else 'NOT FOUND'} at {state_path}"
                   f" - {'PASS' if exists else 'FAIL: create state file'}"
    }

def main():
    """Main verification routine."""
    # Determine project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    config_path = project_root / 'code' / 'config.yaml'
    state_path = project_root / 'state' / 'projects' / 'PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml'

    results = {
        'timestamp': datetime.now().isoformat(),
        'config_path': str(config_path),
        'state_path': str(state_path),
        'checks': {}
    }

    # Check 1: Config file size
    size_result = check_config_file_size(config_path)
    results['checks']['config_size'] = size_result
    print(f"[SIZE CHECK] {size_result['message']}")

    # Check 2: Derived statistics in config
    derived_result = check_derived_statistics_in_config(config_path)
    results['checks']['derived_statistics'] = derived_result
    print(f"[DERIVED CHECK] {derived_result['message']}")

    # Check 3: State file exists
    state_result = verify_state_file_exists(state_path)
    results['checks']['state_file'] = state_result
    print(f"[STATE CHECK] {state_result['message']}")

    # Overall verdict
    all_pass = (
        size_result['within_limit'] and
        not derived_result['found_derived'] and
        state_result['exists']
    )

    results['overall'] = {
        'status': 'PASS' if all_pass else 'FAIL',
        'summary': f"T151 verification: {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}"
    }
    print(f"\n[OVERALL] {results['overall']['summary']}")

    # Return results as JSON for script execution
    import json
    print(json.dumps(results, indent=2))

    return 0 if all_pass else 1

if __name__ == '__main__':
    sys.exit(main())
