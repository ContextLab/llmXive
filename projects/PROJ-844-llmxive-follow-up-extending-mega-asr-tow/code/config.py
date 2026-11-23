"""
Configuration management for llmXive project.
Handles paths, random seeds, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Singleton instance
_config_instance: Optional[Dict[str, Any]] = None

def get_default_paths() -> Dict[str, Path]:
    """Returns default directory paths relative to project root."""
    project_root = Path(__file__).resolve().parent.parent
    return {
        'root': project_root,
        'code': project_root / 'code',
        'data_raw': project_root / 'data' / 'raw',
        'data_derived': project_root / 'data' / 'derived',
        'data_validation': project_root / 'data' / 'validation',
        'tests': project_root / 'tests',
        'figures': project_root / 'figures',
        'docs': project_root / 'docs',
        'specs': project_root / 'specs',
    }

def get_default_hyperparameters() -> Dict[str, Any]:
    """Returns default hyperparameters for the experiment."""
    return {
        'random_seed': 42,
        'threshold_sss': 0.5,
        'threshold_wer_multiplier': 2.0,
        'k_hysteresis': 3,
        'distortion_snrs': [-5, 0, 5, 10, 15, 20],
        'distortion_rt60s': [0.1, 0.3, 0.5, 0.7, 0.9],
        'batch_size': 16,
        'max_workers': 4,
    }

# ----------------------------------------------------------------------
# Project‑wide constants required by T001
# ----------------------------------------------------------------------
SEED = 42
SAMPLE_SIZE = 50000

# SNR levels (9 values from -10 dB … 30 dB)
SNR_LEVELS = [-10, -5, 0, 5, 10, 15, 20, 25, 30]

# RT60 levels (6 values from 0.1 s … 0.6 s)
RT60_LEVELS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]

CCM_THRESHOLD = 0.5                     # Composite Collapse Metric threshold
SSS_ABSOLUTE_THRESHOLD = 0.5            # Absolute SSS threshold for universal collapse
WER_MULTIPLIER = 2.0                    # WER multiplier relative to baseline
FDR = 0.05                               # Benjamini‑Hochberg false discovery rate
R2_TARGET = 0.6                         # Desired R² for regression models

def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or return defaults.

    Args:
        config_path: Path to a custom config YAML file. If None, uses defaults.

    Returns:
        A dictionary containing the configuration.
    """
    global _config_instance

    if _config_instance is not None:
        return _config_instance

    paths = get_default_paths()
    hyperparams = get_default_hyperparameters()

    # Default config structure
    config = {
        'paths': {str(k): str(v) for k, v in paths.items()},
        'hyperparameters': hyperparams,
        'models': {
            'asr': ['whisper-tiny'],
            'embedding': ['all-MiniLM-L6-v2']
        },
        'datasets': {
            'librispeech': {
                'name': 'librispeech_asr',
                'subset': 'clean',
                'split': 'test.other',
                'streaming': True
            },
            'coraa': {
                'name': 'coraa',
                'subset': 'mupe_asr',
                'split': 'test',
                'streaming': True
            }
        }
    }

    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(path, 'r') as f:
            user_config = yaml.safe_load(f)
            # Merge user config into defaults
            if 'paths' in user_config:
                config['paths'].update(user_config['paths'])
            if 'hyperparameters' in user_config:
                config['hyperparameters'].update(user_config['hyperparameters'])
            if 'models' in user_config:
                config['models'].update(user_config['models'])
            if 'datasets' in user_config:
                config['datasets'].update(user_config['datasets'])

    _config_instance = config
    return config
