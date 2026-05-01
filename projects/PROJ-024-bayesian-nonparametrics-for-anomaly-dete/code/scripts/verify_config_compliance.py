"""
T089: Verify config.yaml contains only hyperparameters, seeds, and base paths.

This script validates that config.yaml adheres to Constitution Principle I
by ensuring no derived statistics (e.g., dataset observation counts, computed
metrics, runtime measurements) are stored in the configuration file.

Derived statistics should be moved to state files (state/projects/*.yaml).

Usage:
    python scripts/verify_config_compliance.py [--fix]

The --fix flag will automatically move derived statistics to state files.
"""
import os
import sys
import yaml
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict, field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'code'))

CONFIG_PATH = PROJECT_ROOT / 'code' / 'config.yaml'
STATE_PATH = PROJECT_ROOT / 'state' / 'projects' / 'PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml'

@dataclass
class ComplianceViolation:
    """Represents a configuration compliance violation."""
    section: str
    key: str
    value: Any
    violation_type: str  # 'derived_statistic', 'runtime_metric', 'dataset_metadata'
    reason: str
    suggested_action: str

@dataclass
class ComplianceReport:
    """Full compliance report for config.yaml."""
    compliant: bool
    total_keys_checked: int
    violations: List[ComplianceViolation] = field(default_factory=list)
    clean_keys: List[str] = field(default_factory=list)
    derived_keys_moved: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

def load_config() -> Dict[str, Any]:
    """Load the config.yaml file."""
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        sys.exit(1)
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def save_config(config: Dict[str, Any]) -> None:
    """Save the config.yaml file."""
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def load_state() -> Dict[str, Any]:
    """Load the state YAML file."""
    if not STATE_PATH.exists():
        # Create state file structure if it doesn't exist
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return {
            'project_id': 'PROJ-024-bayesian-nonparametrics-for-anomaly-dete',
            'artifacts': {},
            'derived_statistics': {}
        }
    
    with open(STATE_PATH, 'r') as f:
        return yaml.safe_load(f)

def save_state(state: Dict[str, Any]) -> None:
    """Save the state YAML file."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def is_derived_statistic(key: str, value: Any) -> Tuple[bool, str, str]:
    """
    Check if a config key/value pair is a derived statistic that should
    not be in config.yaml.
    
    Returns: (is_derived, violation_type, reason)
    """
    derived_patterns = {
        'observation_count': ('dataset_metadata', 'Dataset observation count is a derived statistic'),
        'num_observations': ('dataset_metadata', 'Number of observations is computed from data'),
        'sample_size': ('dataset_metadata', 'Sample size is derived from dataset'),
        'data_size_mb': ('dataset_metadata', 'Data size is a runtime measurement'),
        'file_size': ('dataset_metadata', 'File size is a filesystem property'),
        'checksum': ('data_integrity', 'Checksum should be in state file, not config'),
        'hash': ('data_integrity', 'Hash should be in state file, not config'),
        'elapsed_time': ('runtime_metric', 'Elapsed time is a runtime measurement'),
        'runtime': ('runtime_metric', 'Runtime is measured during execution'),
        'duration': ('runtime_metric', 'Duration is computed during processing'),
        'memory_peak': ('runtime_metric', 'Memory usage is monitored at runtime'),
        'peak_memory': ('runtime_metric', 'Peak memory is measured during execution'),
        'f1_score': ('performance_metric', 'F1-score is computed during evaluation'),
        'precision': ('performance_metric', 'Precision is computed during evaluation'),
        'recall': ('performance_metric', 'Recall is computed during evaluation'),
        'auc': ('performance_metric', 'AUC is computed during evaluation'),
        'accuracy': ('performance_metric', 'Accuracy is computed during evaluation'),
        'elbo': ('model_metric', 'ELBO is computed during training'),
        'convergence': ('model_metric', 'Convergence is measured during inference'),
        'num_clusters': ('model_metric', 'Number of clusters is learned from data'),
        'num_components': ('model_metric', 'Number of components is learned from data'),
        'active_components': ('model_metric', 'Active components count is learned'),
        'threshold': ('calibrated_metric', 'Threshold is calibrated from data (see T044)'),
        'anomaly_rate': ('calibrated_metric', 'Anomaly rate is computed from scores'),
        'last_updated': ('metadata', 'Timestamp is runtime metadata'),
        'created_at': ('metadata', 'Creation timestamp is metadata'),
        'processed_at': ('metadata', 'Processing timestamp is metadata'),
        'version': ('metadata', 'Version tracking should be in state, not config'),
    }
    
    key_lower = key.lower()
    for pattern, (violation_type, reason) in derived_patterns.items():
        if pattern in key_lower:
            return True, violation_type, reason
    
    # Check if value looks like a computed statistic
    if isinstance(value, (int, float)):
        # Large integers might be counts
        if isinstance(value, int) and value > 1000:
            return True, 'dataset_metadata', 'Large integer likely represents observation count'
    
    return False, '', ''

def is_config_parameter(key: str, value: Any) -> bool:
    """
    Check if a config key/value pair is a legitimate configuration parameter
    (hyperparameter, seed, or base path).
    """
    allowed_patterns = {
        'seed': True,
        'random_seed': True,
        'np_seed': True,
        'alpha': True,  # DPGMM concentration parameter
        'beta': True,
        'gamma': True,
        'temperature': True,
        'learning_rate': True,
        'lr': True,
        'max_iter': True,
        'max_iterations': True,
        'n_iter': True,
        'tol': True,
        'tolerance': True,
        'threshold': True,  # Base threshold, not calibrated
        'percentile': True,
        'window_size': True,
        'n_components': True,  # Initial guess, not learned
        'max_components': True,
        'min_components': True,
        'path': True,
        'base_path': True,
        'data_path': True,
        'model_path': True,
        'output_path': True,
        'log_path': True,
        'checkpoint_path': True,
        'raw_data_dir': True,
        'processed_data_dir': True,
        'model_dir': True,
        'log_dir': True,
        'fig_dir': True,
        'url': True,
        'dataset_url': True,
        'batch_size': True,
        'num_workers': True,
        'verbose': True,
        'debug': True,
        'log_level': True,
        'random_state': True,
    }
    
    key_lower = key.lower()
    for pattern in allowed_patterns:
        if pattern in key_lower:
            return True
    
    return False

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """Unflatten a dictionary."""
    out = {}
    for key, value in d.items():
        parts = key.split(sep)
        d_temp = out
        for part in parts[:-1]:
            if part not in d_temp:
                d_temp[part] = {}
            d_temp = d_temp[part]
        d_temp[parts[-1]] = value
    return out

def verify_config(config: Dict[str, Any]) -> ComplianceReport:
    """
    Verify that config.yaml contains only hyperparameters, seeds, and base paths.
    Returns a compliance report with any violations found.
    """
    report = ComplianceReport(compliant=True, total_keys_checked=0)
    
    # Flatten the config for easier checking
    flat_config = flatten_dict(config)
    report.total_keys_checked = len(flat_config)
    
    for key, value in flat_config.items():
        is_derived, violation_type, reason = is_derived_statistic(key, value)
        
        if is_derived:
            report.compliant = False
            violation = ComplianceViolation(
                section=key.rsplit('.', 1)[0] if '.' in key else 'root',
                key=key,
                value=value,
                violation_type=violation_type,
                reason=reason,
                suggested_action=f"Move '{key}' to state file's derived_statistics section"
            )
            report.violations.append(violation)
        else:
            report.clean_keys.append(key)
    
    return report

def move_derived_to_state(config: Dict[str, Any], state: Dict[str, Any], 
                           violations: List[ComplianceViolation]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Move derived statistics from config to state file.
    Returns updated config and state.
    """
    updated_config = config.copy()
    updated_state = state.copy()
    
    if 'derived_statistics' not in updated_state:
        updated_state['derived_statistics'] = {}
    
    for violation in violations:
        # Remove from config
        parts = violation.key.split('.')
        temp = updated_config
        for part in parts[:-1]:
            if part in temp:
                temp = temp[part]
            else:
                break
        if parts[-1] in temp:
            del temp[parts[-1]]
            print(f"  Removed from config: {violation.key}")
        
        # Add to state
        updated_state['derived_statistics'][violation.key] = {
            'value': violation.value,
            'violation_type': violation.violation_type,
            'reason': violation.reason,
            'removed_at': datetime.utcnow().isoformat()
        }
        print(f"  Moved to state: {violation.key}")
    
    return updated_config, updated_state

def compute_config_checksum(config: Dict[str, Any]) -> str:
    """Compute SHA256 checksum of config content."""
    config_str = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(config_str.encode()).hexdigest()

def main(fix: bool = False) -> int:
    """
    Main entry point for config compliance verification.
    
    Args:
        fix: If True, automatically move derived statistics to state file.
    
    Returns:
        0 if compliant (or fixed), 1 if violations remain.
    """
    print("=" * 70)
    print("T089: Config.yaml Compliance Verification")
    print("=" * 70)
    print(f"Config path: {CONFIG_PATH}")
    print(f"State path: {STATE_PATH}")
    print()
    
    # Load config
    print("[1/4] Loading config.yaml...")
    config = load_config()
    print(f"  Loaded {len(config)} top-level sections")
    
    # Verify compliance
    print("\n[2/4] Checking for derived statistics...")
    report = verify_config(config)
    print(f"  Checked {report.total_keys_checked} configuration keys")
    print(f"  Found {len(report.violations)} violations")
    
    if report.violations:
        print("\n  Violations found:")
        for v in report.violations:
            print(f"    - {v.key}: {v.reason}")
            print(f"      Type: {v.violation_type}")
            print(f"      Action: {v.suggested_action}")
    else:
        print("\n  No violations found! Config is compliant.")
    
    # Fix if requested
    if fix and report.violations:
        print("\n[3/4] Moving derived statistics to state file...")
        config, state = move_derived_to_state(config, load_state(), report.violations)
        
        # Save updated files
        print("\n[4/4] Saving updated files...")
        save_config(config)
        save_state(state)
        
        # Update state checksum
        if 'artifacts' not in state:
            state['artifacts'] = {}
        state['artifacts']['config.yaml'] = {
            'checksum': compute_config_checksum(config),
            'updated_at': datetime.utcnow().isoformat()
        }
        save_state(state)
        
        print(f"  Saved updated config.yaml")
        print(f"  Updated state file with {len(report.violations)} derived statistics")
        print("\n  ✓ Config compliance fixed!")
        
        return 0
    elif report.violations:
        print("\n[3/3] Config has violations that require manual review.")
        print("  Run with --fix to automatically move derived statistics to state file.")
        return 1
    else:
        print("\n[3/3] Config is fully compliant.")
        return 0

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Verify config.yaml compliance')
    parser.add_argument('--fix', action='store_true', 
                       help='Automatically move derived statistics to state file')
    args = parser.parse_args()
    
    sys.exit(main(fix=args.fix))
