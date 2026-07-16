import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

# Default configuration paths
DEFAULT_CONFIG_PATH = Path("code/theory/config.yaml")
FALLBACK_CONFIG_PATH = Path("config.yaml")

@dataclass
class PipelineConfig:
    """
    Dataclass representing the pipeline configuration.
    """
    # Data paths
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    output_dir: str = "data/output"
    
    # Analysis parameters
    radius_uncertainty_threshold: float = 0.20
    period_uncertainty_threshold: float = 0.01
    min_bin_size: int = 30
    max_period_days: float = 100.0
    
    # GMM parameters
    gmm_max_components: int = 2
    gmm_max_iter: int = 100
    gmm_n_init: int = 10
    
    # Bootstrap parameters
    bootstrap_iterations: int = 1000
    bootstrap_confidence_level: float = 0.95
    
    # Regression parameters
    completeness_map_path: Optional[str] = None
    eiv_sigma_x: float = 0.01
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    
    # Runtime
    max_runtime_hours: int = 6
    
    # Theory comparison
    bonferroni_alpha: float = 0.025
    
    # Custom fields can be added dynamically
    custom: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """Create a PipelineConfig from a dictionary."""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                config.custom[key] = value
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary."""
        return {
            k: v for k, v in self.__dict__.items() 
            if not k.startswith('_') and k != 'custom'
        }

# Global configuration instance
_global_config: Optional[PipelineConfig] = None

def load_config(config_path: Optional[Path] = None) -> PipelineConfig:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. If None, tries default paths.
    
    Returns:
        A PipelineConfig instance.
    
    Raises:
        FileNotFoundError: If no config file is found.
    """
    global _global_config
    
    if _global_config is not None:
        return _global_config
    
    paths_to_try = []
    if config_path:
        paths_to_try.append(config_path)
    if DEFAULT_CONFIG_PATH.exists():
        paths_to_try.append(DEFAULT_CONFIG_PATH)
    if FALLBACK_CONFIG_PATH.exists():
        paths_to_try.append(FALLBACK_CONFIG_PATH)
    
    if not paths_to_try:
        # Return default config if no file found
        _global_config = PipelineConfig()
        return _global_config
    
    for path in paths_to_try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            _global_config = PipelineConfig.from_dict(data)
            return _global_config
    
    # Fallback to defaults
    _global_config = PipelineConfig()
    return _global_config

def get_config() -> PipelineConfig:
    """
    Get the global configuration instance.
    Loads it if not already loaded.
    
    Returns:
        The global PipelineConfig.
    """
    if _global_config is None:
        load_config()
    return _global_config

def reset_config() -> None:
    """Reset the global configuration to force a reload on next access."""
    global _global_config
    _global_config = None

def save_config(config: PipelineConfig, path: Path) -> None:
    """
    Save the configuration to a YAML file.
    
    Args:
        config: The config to save.
        path: Path to save the file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)

# Example usage and module initialization
if __name__ == "__main__":
    # Test loading config
    config = load_config()
    print(f"Loaded config: {config.to_dict()}")
    
    # Test saving config
    test_path = Path("test_config.yaml")
    save_config(config, test_path)
    print(f"Saved config to {test_path}")
    
    # Verify reload
    reset_config()
    reloaded = get_config()
    assert reloaded.to_dict() == config.to_dict()
    print("Config reload verification passed.")
    
    if test_path.exists():
        test_path.unlink()
        print("Cleaned up test file.")