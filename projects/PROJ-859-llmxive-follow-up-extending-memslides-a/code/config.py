"""
Configuration management for llmXive project.
All paths, seeds, and thresholds are defined here.

Defaults come from this module. A ``config.yaml`` file in the project
root (or, as a fallback, next to this module) may override seeds,
paths and thresholds for reproducibility on fresh runners
(Constitution Principle I). Environment variables of the form
``LLMXIVE_<SECTION>_<KEY>`` take the highest precedence.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Candidate locations for the override file (project root first).
CONFIG_YAML_CANDIDATES = [
    PROJECT_ROOT / 'config.yaml',
    Path(__file__).resolve().parent / 'config.yaml',
]

# Default paths relative to project root
DEFAULT_PATHS = {
    # Raw Data
    'raw_data_dir': PROJECT_ROOT / 'data' / 'raw',
    'training_dir': PROJECT_ROOT / 'data' / 'training',
    'held_out_dir': PROJECT_ROOT / 'data' / 'held_out',

    # Processed Data
    'processed_dir': PROJECT_ROOT / 'data' / 'processed',
    'feature_matrix': PROJECT_ROOT / 'data' / 'processed' / 'feature_matrix.csv',
    'rules_dir': PROJECT_ROOT / 'data' / 'processed' / 'rules',
    'global_rules': PROJECT_ROOT / 'data' / 'processed' / 'rules' / 'global_rules.json',

    # Benchmark & Evaluation
    'benchmark_results': PROJECT_ROOT / 'data' / 'processed' / 'benchmark_results.json',
    'accuracy_deltas': PROJECT_ROOT / 'data' / 'processed' / 'accuracy_deltas.csv',
    'statistical_analysis': PROJECT_ROOT / 'data' / 'processed' / 'statistical_analysis.json',
    'sweep_config': PROJECT_ROOT / 'data' / 'processed' / 'sweep_config.json',
    'sensitivity_sweep': PROJECT_ROOT / 'data' / 'processed' / 'sensitivity_sweep.csv',

    # Logs & State
    'state_file': PROJECT_ROOT / 'data' / 'state.json',
    'logs_dir': PROJECT_ROOT / 'logs',
}

# Default Seeds for Reproducibility
DEFAULT_SEEDS = {
    'random_seed': 42,
    'numpy_seed': 42,
    'torch_seed': 42,
    # Explicit constraint from T006 / tasks.md Phase 0
    'training_seed': 42,
    'holdout_seed': 43,
}

# Default Thresholds & Parameters
DEFAULT_THRESHOLDS = {
    # Explicit constraint from T006: FIDELITY_TOLERANCE = 0.90
    'fidelity_tolerance': 0.90,
    'fidelity_threshold': 0.90,
    'holdout_variance_multiplier': 1.5,
    'min_support': 0.05,
    'max_depth': 5,
    'rule_count_limit': 100,
}

# Model Parameters
DEFAULT_MODEL_PARAMS = {
    'max_depth': 5,
    'min_samples_split': 2,
    'min_samples_leaf': 1,
}

# Keys of config.yaml:paths that map onto DEFAULT_PATHS entries.
_PATH_KEY_ALIASES = {
    'data_raw': 'raw_data_dir',
    'data_processed': 'processed_dir',
    'data_held_out': 'held_out_dir',
    'rules_output': 'rules_dir',
    'training_dir': 'training_dir',
    'held_out_dir': 'held_out_dir',
    'contracts': 'contracts',
    'logs': 'logs_dir',
}

# Keys of config.yaml:rule_induction (and others) mapped onto thresholds.
_THRESHOLD_KEY_ALIASES = {
    'fidelity_threshold': 'fidelity_threshold',
    'fidelity_tolerance': 'fidelity_tolerance',
    'max_depth': 'max_depth',
    'min_support': 'min_support',
    'rule_count_limit': 'rule_count_limit',
    'variance_multiplier': 'holdout_variance_multiplier',
    'argument_variance_scale': 'holdout_variance_multiplier',
}

# Keys of config.yaml sections mapped onto seeds.
_SEED_KEY_ALIASES = {
    'random_seed': 'random_seed',
    'numpy_seed': 'numpy_seed',
    'torch_seed': 'torch_seed',
    'training_seed': 'training_seed',
    'holdout_seed': 'holdout_seed',
    'seed': 'random_seed',
}


def find_config_yaml() -> Optional[Path]:
    """Return the first existing config.yaml candidate, or None."""
    for candidate in CONFIG_YAML_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def load_yaml_overrides(yaml_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the raw YAML override mapping (empty dict if no file)."""
    path = yaml_path if yaml_path is not None else find_config_yaml()
    if path is None:
        return {}
    with open(path, 'r', encoding='utf-8') as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(
            f"config.yaml at {path} must contain a mapping at the top level, "
            f"got {type(data).__name__}"
        )
    return data


def _apply_yaml_overrides(
    paths: Dict[str, Path],
    seeds: Dict[str, int],
    thresholds: Dict[str, Any],
    yaml_data: Dict[str, Any],
) -> None:
    """Mutate the given dicts in place with values from config.yaml."""
    # --- paths ---
    yaml_paths = yaml_data.get('paths') or {}
    if not isinstance(yaml_paths, dict):
        raise ValueError("config.yaml 'paths' section must be a mapping")
    for yaml_key, value in yaml_paths.items():
        key = _PATH_KEY_ALIASES.get(yaml_key, yaml_key)
        if value is None:
            continue
        if isinstance(value, (str, Path)):
            p = Path(value)
            if not p.is_absolute():
                p = PROJECT_ROOT / p
            paths[key] = p
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                sub_p = Path(sub_value)
                if not sub_p.is_absolute():
                    sub_p = PROJECT_ROOT / sub_p
                paths[sub_key] = sub_p
        else:
            raise ValueError(
                f"config.yaml paths.{yaml_key} must be a string path, got "
                f"{type(value).__name__}"
            )

    # --- seeds ---
    project = yaml_data.get('project') or {}
    if not isinstance(project, dict):
        raise ValueError("config.yaml 'project' section must be a mapping")
    for yaml_key, value in project.items():
        if yaml_key in _SEED_KEY_ALIASES and isinstance(value, int):
            seeds[_SEED_KEY_ALIASES[yaml_key]] = value
    benchmark = yaml_data.get('benchmark') or {}
    if not isinstance(benchmark, dict):
        raise ValueError("config.yaml 'benchmark' section must be a mapping")
    if isinstance(benchmark.get('random_seed'), int):
        seeds['random_seed'] = benchmark['random_seed']
    generation = yaml_data.get('generation') or {}
    if not isinstance(generation, dict):
        raise ValueError("config.yaml 'generation' section must be a mapping")
    if isinstance(generation.get('seed'), int):
        seeds['random_seed'] = generation['seed']
    if isinstance(generation.get('training_seed'), int):
        seeds['training_seed'] = generation['training_seed']
    if isinstance(generation.get('holdout_seed'), int):
        seeds['holdout_seed'] = generation['holdout_seed']
    if isinstance(generation.get('variance_multiplier'), (int, float)):
        thresholds['holdout_variance_multiplier'] = float(
            generation['variance_multiplier']
        )

    # --- thresholds ---
    rule_induction = yaml_data.get('rule_induction') or {}
    if not isinstance(rule_induction, dict):
        raise ValueError("config.yaml 'rule_induction' section must be a mapping")
    for yaml_key, value in rule_induction.items():
        if yaml_key in _THRESHOLD_KEY_ALIASES and isinstance(value, (int, float)):
            thresholds[_THRESHOLD_KEY_ALIASES[yaml_key]] = value
    statistics = yaml_data.get('statistics') or {}
    if isinstance(statistics, dict) and isinstance(
        statistics.get('fidelity_tolerance'), (int, float)
    ):
        thresholds['fidelity_tolerance'] = float(statistics['fidelity_tolerance'])

def _apply_env_overrides(
    seeds: Dict[str, int],
    thresholds: Dict[str, Any],
) -> None:
    """Apply LLMXIVE_SEEDS_* and LLMXIVE_THRESHOLDS_* env overrides."""
    for env_key, value in os.environ.items():
        if not env_key.startswith('LLMXIVE_'):
            continue
        parts = env_key.split('_', 2)
        if len(parts) != 3:
            continue
        _, section, key = parts
        key = key.lower()
        if section == 'SEEDS':
            try:
                seeds[_SEED_KEY_ALIASES.get(key, key)] = int(value)
            except ValueError:
                raise ValueError(
                    f"Environment variable {env_key} must be an integer seed, "
                    f"got {value!r}"
                )
        elif section == 'THRESHOLDS':
            try:
                thresholds[_THRESHOLD_KEY_ALIASES.get(key, key)] = float(value)
            except ValueError:
                raise ValueError(
                    f"Environment variable {env_key} must be numeric, got {value!r}"
                )


class Config:
    """
    Configuration container with dict-like access.

    Precedence (lowest to highest):
    1. Defaults defined in this module.
    2. ``config.yaml`` in the project root (or ``code/config.yaml``).
    3. ``LLMXIVE_SEEDS_*`` / ``LLMXIVE_THRESHOLDS_*`` environment variables.
    """

    def __init__(
        self,
        paths: Optional[Dict[str, Path]] = None,
        seeds: Optional[Dict[str, int]] = None,
        thresholds: Optional[Dict[str, float]] = None,
        yaml_path: Optional[Path] = None,
    ):
        self._paths = dict(DEFAULT_PATHS)
        self._seeds = dict(DEFAULT_SEEDS)
        self._thresholds = dict(DEFAULT_THRESHOLDS)
        self.model_params = dict(DEFAULT_MODEL_PARAMS)

        # Explicit constructor arguments take precedence over YAML.
        self._yaml_path = yaml_path if yaml_path is not None else find_config_yaml()
        yaml_data: Dict[str, Any] = {}
        if self._yaml_path is not None and self._yaml_path.is_file():
            yaml_data = load_yaml_overrides(self._yaml_path)
        self._yaml_source = str(self._yaml_path) if yaml_data else None

        _apply_yaml_overrides(self._paths, self._seeds, self._thresholds, yaml_data)
        _apply_env_overrides(self._seeds, self._thresholds)

        # Explicit constructor arguments override everything.
        if paths:
            self._paths.update(paths)
        if seeds:
            self._seeds.update(seeds)
        if thresholds:
            self._thresholds.update(thresholds)

        self._all = {**self._paths, **self._seeds, **self._thresholds}

        # Ensure directories exist
        for path in self._paths.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)

    def __getitem__(self, key: str) -> Any:
        if key in self._all:
            return self._all[key]
        raise KeyError(f"Config key '{key}' not found.")

    def __contains__(self, key: str) -> bool:
        return key in self._all

    def get(self, key: str, default: Any = None) -> Any:
        return self._all.get(key, default)

    @property
    def paths(self) -> Dict[str, Path]:
        return self._paths

    @property
    def seeds(self) -> Dict[str, int]:
        return self._seeds

    @property
    def thresholds(self) -> Dict[str, Any]:
        return self._thresholds

    @property
    def yaml_source(self) -> Optional[str]:
        """Path of the config.yaml that supplied overrides, if any."""
        return self._yaml_source

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Singleton accessor for the global configuration.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config() -> None:
    """Reset the singleton instance (useful for testing)."""
    global _config_instance
    _config_instance = None
