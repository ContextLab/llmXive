import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Singleton instance holder
_config_instance: Optional["ProjectConfig"] = None

@dataclass
class ProjectConfig:
    """
    Centralized configuration for the Multi-LCB project.
    Handles paths, random seeds, model lists, and temperature settings.
    """
    # Project Root
    root_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    
    # Paths
    data_dir: Path = field(default_factory=lambda: Path("data"))
    results_dir: Path = field(default_factory=lambda: Path("results"))
    contracts_dir: Path = field(default_factory=lambda: Path("contracts"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    figures_dir: Path = field(default_factory=lambda: Path("figures"))
    code_dir: Path = field(default_factory=lambda: Path("code"))
    tests_dir: Path = field(default_factory=lambda: Path("tests"))
    docs_dir: Path = field(default_factory=lambda: Path("docs"))
    
    # Randomness
    seed: int = 42
    
    # Model Configuration
    models: List[str] = field(default_factory=lambda: [
        "gpt-4o",
        "claude-3-5-sonnet",
        "llama-3.1-70b",
        "mistral-large"
    ])
    
    # Temperature Settings
    temperatures: List[float] = field(default_factory=lambda: [0.2, 0.6, 1.0])
    
    # Execution Settings
    num_runs: int = 10
    timeout_seconds: int = 60
    
    def __post_init__(self):
        """Ensure directories exist relative to root_dir."""
        # Convert relative paths to absolute if they are not already
        if not self.root_dir.is_absolute():
            self.root_dir = self.root_dir.resolve()
        
        # Ensure directories exist
        self.data_dir = self.root_dir / self.data_dir
        self.results_dir = self.root_dir / self.results_dir
        self.contracts_dir = self.root_dir / self.contracts_dir
        self.logs_dir = self.root_dir / self.logs_dir
        self.figures_dir = self.root_dir / self.figures_dir
        self.code_dir = self.root_dir / self.code_dir
        self.tests_dir = self.root_dir / self.tests_dir
        self.docs_dir = self.root_dir / self.docs_dir
        
        for directory in [
            self.data_dir, 
            self.results_dir, 
            self.contracts_dir, 
            self.logs_dir, 
            self.figures_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)

def get_config() -> ProjectConfig:
    """
    Returns the singleton ProjectConfig instance.
    Creates it if it doesn't exist.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ProjectConfig()
    return _config_instance

def set_config(new_config: Optional[ProjectConfig] = None) -> ProjectConfig:
    """
    Sets the singleton ProjectConfig instance.
    If new_config is None, resets to a default instance.
    """
    global _config_instance
    if new_config is None:
        _config_instance = ProjectConfig()
    else:
        _config_instance = new_config
    return _config_instance

# Helper functions to retrieve specific configuration values
def get_data_path() -> Path:
    """Returns the absolute path to the data directory."""
    return get_config().data_dir

def get_results_path() -> Path:
    """Returns the absolute path to the results directory."""
    return get_config().results_dir

def get_contracts_path() -> Path:
    """Returns the absolute path to the contracts directory."""
    return get_config().contracts_dir

def get_logs_path() -> Path:
    """Returns the absolute path to the logs directory."""
    return get_config().logs_dir

def get_figures_path() -> Path:
    """Returns the absolute path to the figures directory."""
    return get_config().figures_dir

def get_models() -> List[str]:
    """Returns the list of configured models."""
    return get_config().models

def get_temperatures() -> List[float]:
    """Returns the list of configured temperatures."""
    return get_config().temperatures

def get_seed() -> int:
    """Returns the configured random seed."""
    return get_config().seed

if __name__ == "__main__":
    # Simple test to ensure configuration loads and paths exist
    cfg = get_config()
    print(f"Project Root: {cfg.root_dir}")
    print(f"Data Path: {cfg.data_dir}")
    print(f"Models: {cfg.models}")
    print(f"Temperatures: {cfg.temperatures}")
    print(f"Seed: {cfg.seed}")
    
    # Verify directories exist
    assert cfg.data_dir.exists(), "Data directory missing"
    assert cfg.results_dir.exists(), "Results directory missing"
    assert cfg.logs_dir.exists(), "Logs directory missing"
    print("Configuration verification passed.")