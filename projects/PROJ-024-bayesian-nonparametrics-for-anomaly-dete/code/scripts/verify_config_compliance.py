#!/usr/bin/env python3
"""
Verify that config.yaml contains only hyperparameters, seeds, and base paths.
No derived statistics should be present.

Per T082: config.yaml must be under 2KB and contain only configuration parameters.
Per T083: Verify no derived statistics (metrics, computed values) are in config.
"""

import os
import sys
import yaml
from pathlib import Path
from datetime import datetime
import json

# Define allowed config sections
ALLOWED_SECTIONS = {
    'hyperparameters',
    'seeds',
    'paths',
    'base_paths',
    'model',
    'training',
    'evaluation',
    'datasets',
    'thresholds',
    'logging',
    'memory_limits',
    'runtime_limits',
    'experimental'
}

# Define patterns that indicate derived statistics (should NOT be in config)
DERIVED_STATISTICS_PATTERNS = [
    'f1_score',
    'precision',
    'recall',
    'auc',
    'accuracy',
    'mean_',
    'std_',
    'variance',
    'computed_',
    'calculated_',
    'result_',
    'metric_',
    'score_',
    'anomaly_rate',
    'elapsed_',
    'runtime_',
    'memory_',
    'size_',
    'count_',
    'total_',
    'sum_',
    'average_',
    'statistics',
    'metrics',
    'results',
    'summary',
    'report',
    'convergence',
    'elbo'
]

def load_config(config_path: Path) -> dict:
    """Load YAML config file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

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

def check_section_allowed(section: str) -> bool:
    """Check if top-level section is allowed."""
    return section in ALLOWED_SECTIONS or section.startswith('experimental')

def check_for_derived_statistics(key: str, value) -> list:
    """Check if a key-value pair represents derived statistics."""
    issues = []
    key_lower = key.lower()
    
    # Check key name
    for pattern in DERIVED_STATISTICS_PATTERNS:
        if pattern in key_lower:
            issues.append(f"Key '{key}' matches derived statistic pattern '{pattern}'")
            break
    
    # Check value type (should not be lists of metrics, etc.)
    if isinstance(value, dict):
        for sub_key, sub_value in value.items():
            sub_issues = check_for_derived_statistics(f"{key}.{sub_key}", sub_value)
            issues.extend(sub_issues)
    elif isinstance(value, (list, tuple)):
        if len(value) > 0 and isinstance(value[0], (int, float)):
            # Could be metrics array
            issues.append(f"Key '{key}' has array value (potential metrics): {str(value)[:50]}...")
    
    return issues

def validate_config(config: dict, config_path: Path) -> dict:
    """Validate config against rules."""
    results = {
        'valid': True,
        'issues': [],
        'warnings': [],
        'config_size_bytes': 0,
        'timestamp': datetime.now().isoformat()
    }
    
    # Check file size (T082 requirement: <2KB)
    results['config_size_bytes'] = os.path.getsize(config_path)
    if results['config_size_bytes'] > 2048:
        results['issues'].append(f"Config file size ({results['config_size_bytes']} bytes) exceeds 2KB limit")
        results['valid'] = False
    
    # Flatten config for easier checking
    flat_config = flatten_dict(config)
    
    # Check top-level sections
    for section in config.keys():
        if not check_section_allowed(section):
            results['warnings'].append(f"Top-level section '{section}' not in standard allowed sections")
    
    # Check for derived statistics
    for key, value in flat_config.items():
        issues = check_for_derived_statistics(key, value)
        results['issues'].extend(issues)
        if issues:
            results['valid'] = False
    
    return results

def main():
    """Main entry point."""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    config_path = project_root / 'code' / 'config.yaml'
    
    print("=" * 60)
    print("CONFIG COMPLIANCE VERIFICATION")
    print("=" * 60)
    print(f"Config path: {config_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Check if config exists
    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)
    
    # Load config
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}")
        sys.exit(1)
    
    # Validate
    results = validate_config(config, config_path)
    
    # Report
    print(f"Config Size: {results['config_size_bytes']} bytes")
    if results['config_size_bytes'] <= 2048:
        print("✓ Size check PASSED (<2KB)")
    else:
        print("✗ Size check FAILED (>2KB)")
    print()
    
    if results['warnings']:
        print("WARNINGS:")
        for w in results['warnings']:
            print(f"  - {w}")
        print()
    
    if results['issues']:
        print("ISSUES FOUND:")
        for i in results['issues']:
            print(f"  ✗ {i}")
        print()
        print("RESULT: FAILED")
        sys.exit(1)
    else:
        print("✓ No derived statistics detected")
        print()
        print("RESULT: PASSED")
        sys.exit(0)

if __name__ == '__main__':
    main()
