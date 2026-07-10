import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class ProjectConfig:
    """
    Centralized configuration for project paths and parameters.
    Loads from environment variables or falls back to defaults.
    """
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    
    # Data directories
    data_raw: Path = field(default=Path("data/raw"))
    data_processed: Path = field(default=Path("data/processed"))
    data_compliance: Path = field(default=Path("data/compliance"))
    
    # Results directories
    results_dir: Path = field(default=Path("results"))
    figures_dir: Path = field(default=Path("figures"))
    
    # Configuration files
    config_file: Path = field(default=Path("config/project_config.json"))
    seed_file: Path = field(default=Path("config/seed_config.json"))
    
    # Parameters
    default_seed: int = field(default=42)
    bootstrap_resamples: int = field(default=10000)
    power_sim_iterations: int = field(default=1000)
    compliance_social_media_max_min: int = field(default=30)
    compliance_news_blocked: bool = field(default=True)
    
    def __post_init__(self):
        # Resolve paths relative to project root if they are relative
        if not self.project_root.is_absolute():
            self.project_root = Path.cwd() / self.project_root
        
        # Ensure data directories are absolute relative to project root
        if not self.data_raw.is_absolute():
            self.data_raw = self.project_root / self.data_raw
        if not self.data_processed.is_absolute():
            self.data_processed = self.project_root / self.data_processed
        if not self.data_compliance.is_absolute():
            self.data_compliance = self.project_root / self.data_compliance
        if not self.results_dir.is_absolute():
            self.results_dir = self.project_root / self.results_dir
        if not self.figures_dir.is_absolute():
            self.figures_dir = self.project_root / self.figures_dir
        if not self.config_file.is_absolute():
            self.config_file = self.project_root / self.config_file
        if not self.seed_file.is_absolute():
            self.seed_file = self.project_root / self.seed_file

_global_config: Optional[ProjectConfig] = None

def get_config() -> ProjectConfig:
    """
    Get the global project configuration, initializing it if necessary.
    """
    global _global_config
    if _global_config is None:
        _global_config = ProjectConfig()
        _load_from_env(_global_config)
    return _global_config

def _load_from_env(config: ProjectConfig) -> None:
    """
    Override configuration values from environment variables.
    """
    env_mappings = {
        'PROJECT_ROOT': 'project_root',
        'DATA_RAW': 'data_raw',
        'DATA_PROCESSED': 'data_processed',
        'DATA_COMPLIANCE': 'data_compliance',
        'RESULTS_DIR': 'results_dir',
        'FIGURES_DIR': 'figures_dir',
        'DEFAULT_SEED': 'default_seed',
        'BOOTSTRAP_RESAMPLES': 'bootstrap_resamples',
        'POWER_SIM_ITERATIONS': 'power_sim_iterations',
        'COMPLIANCE_SOCIAL_MEDIA_MAX_MIN': 'compliance_social_media_max_min',
        'COMPLIANCE_NEWS_BLOCKED': 'compliance_news_blocked',
    }

    for env_var, attr_name in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            attr_type = type(getattr(config, attr_name))
            try:
                if attr_type == bool:
                    setattr(config, attr_name, value.lower() in ('true', '1', 'yes'))
                elif attr_type == int:
                    setattr(config, attr_name, int(value))
                elif attr_type == Path:
                    setattr(config, attr_name, Path(value))
                else:
                    setattr(config, attr_name, value)
            except ValueError:
                print(f"Warning: Could not parse env var {env_var} for {attr_name}")

def get_path(key: str) -> Path:
    """
    Get a configuration path by key name.
    
    Args:
        key: One of 'data_raw', 'data_processed', 'data_compliance', 
             'results_dir', 'figures_dir', 'config_file', 'seed_file'
             
    Returns:
        The configured Path object.
    """
    config = get_config()
    path_map = {
        'data_raw': config.data_raw,
        'data_processed': config.data_processed,
        'data_compliance': config.data_compliance,
        'results_dir': config.results_dir,
        'figures_dir': config.figures_dir,
        'config_file': config.config_file,
        'seed_file': config.seed_file,
    }
    if key not in path_map:
        raise KeyError(f"Unknown path key: {key}")
    return path_map[key]

def get_param(key: str) -> Any:
    """
    Get a configuration parameter by key name.
    
    Args:
        key: One of 'default_seed', 'bootstrap_resamples', 'power_sim_iterations',
             'compliance_social_media_max_min', 'compliance_news_blocked'
             
    Returns:
        The configured parameter value.
    """
    config = get_config()
    param_map = {
        'default_seed': config.default_seed,
        'bootstrap_resamples': config.bootstrap_resamples,
        'power_sim_iterations': config.power_sim_iterations,
        'compliance_social_media_max_min': config.compliance_social_media_max_min,
        'compliance_news_blocked': config.compliance_news_blocked,
    }
    if key not in param_map:
        raise KeyError(f"Unknown parameter key: {key}")
    return param_map[key]

def reset_config() -> None:
    """
    Reset the global configuration to defaults (useful for testing).
    """
    global _global_config
    _global_config = None

def save_config(config: Optional[ProjectConfig] = None, path: Optional[Path] = None) -> None:
    """
    Save the current configuration to a JSON file.
    
    Args:
        config: Optional config to save. If None, uses the global config.
        path: Optional path to save to. If None, uses the configured config_file path.
    """
    if config is None:
        config = get_config()
    if path is None:
        path = config.config_file
        
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        # Convert Paths to strings for JSON serialization
        data = asdict(config)
        for k, v in data.items():
            if isinstance(v, Path):
                data[k] = str(v)
        json.dump(data, f, indent=2)

def load_config(path: Optional[Path] = None) -> ProjectConfig:
    """
    Load configuration from a JSON file.
    
    Args:
        path: Optional path to load from. If None, uses the configured config_file path.
             
    Returns:
        A ProjectConfig instance.
    """
    if path is None:
        config = get_config()
        path = config.config_file
        
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
        
    with open(path, 'r') as f:
        data = json.load(f)
        
    # Convert string paths back to Path objects
    for k, v in data.items():
        if isinstance(v, str) and k in ['project_root', 'data_raw', 'data_processed', 
                                         'data_compliance', 'results_dir', 'figures_dir', 
                                         'config_file', 'seed_file']:
            data[k] = Path(v)
            
    return ProjectConfig(**data)

def main():
    """
    Command-line entry point to display or save configuration.
    Usage:
        python -m code.config.env_config [--save]
    """
    import argparse
    parser = argparse.ArgumentParser(description="Manage project configuration")
    parser.add_argument('--save', action='store_true', help='Save current config to file')
    args = parser.parse_args()
    
    config = get_config()
    print("Current Project Configuration:")
    print("-" * 40)
    for attr, value in asdict(config).items():
        print(f"{attr}: {value}")
        
    if args.save:
        save_config(config)
        print(f"\nConfiguration saved to: {config.config_file}")

if __name__ == "__main__":
    main()
