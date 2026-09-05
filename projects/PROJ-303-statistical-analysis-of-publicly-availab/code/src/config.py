import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import random

@dataclass
class Config:
    """
    Centralized configuration for the statistical analysis pipeline.
    Loads from environment variables, YAML files, or defaults.
    """
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    data_raw_dir: Path = field(init=False)
    data_processed_dir: Path = field(init=False)
    outputs_plots_dir: Path = field(init=False)
    outputs_metrics_dir: Path = field(init=False)
    state_dir: Path = field(init=False)
    specs_dir: Path = field(init=False)

    # Hyperparameters
    training_start_year: int = 2000
    training_end_year: int = 2015
    test_start_year: int = 2019
    test_end_year: int = 2020
    
    # Extreme Event Definition
    percentile_threshold: float = 95.0
    missing_ratio_threshold: float = 0.15
    max_contiguous_gap_days: int = 30
    
    # Model Parameters
    gpd_loc_param: float = 0.0
    gpd_scale_param: float = 1.0
    gpd_shape_param: float = 0.0
    
    # Compute Limits
    wall_clock_budget_seconds: int = 21600  # 6 hours default
    time_limit_check_interval_seconds: int = 300
    
    # Randomness
    seed: int = 42
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    def __post_init__(self):
        # Initialize derived paths relative to project root
        self.data_raw_dir = self.project_root / "data" / "raw"
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.outputs_plots_dir = self.project_root / "outputs" / "plots"
        self.outputs_metrics_dir = self.project_root / "outputs" / "metrics"
        self.state_dir = self.project_root / "state"
        self.specs_dir = self.project_root / "specs"

        # Ensure directories exist
        for p in [self.data_raw_dir, self.data_processed_dir, 
                  self.outputs_plots_dir, self.outputs_metrics_dir, 
                  self.state_dir, self.specs_dir]:
            p.mkdir(parents=True, exist_ok=True)

        # Apply environment overrides if present
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        """Override config values with environment variables if set."""
        if env_seed := os.getenv("PIPELINE_SEED"):
            self.seed = int(env_seed)
        if env_budget := os.getenv("PIPELINE_WALL_CLOCK_BUDGET_SECONDS"):
            self.wall_clock_budget_seconds = int(env_budget)
        if env_threshold := os.getenv("PIPELINE_PERCENTILE_THRESHOLD"):
            self.percentile_threshold = float(env_threshold)
        
        # Set random seeds
        random.seed(self.seed)
        np.random.seed(self.seed)

    def to_dict(self) -> Dict[str, Any]:
        """Export config to a dictionary."""
        return {
            "project_root": str(self.project_root),
            "training_years": f"{self.training_start_year}-{self.training_end_year}",
            "test_years": f"{self.test_start_year}-{self.test_end_year}",
            "percentile_threshold": self.percentile_threshold,
            "wall_clock_budget_seconds": self.wall_clock_budget_seconds,
            "seed": self.seed,
            "paths": {
                "data_raw": str(self.data_raw_dir),
                "data_processed": str(self.data_processed_dir),
                "outputs_plots": str(self.outputs_plots_dir),
                "outputs_metrics": str(self.outputs_metrics_dir),
                "state": str(self.state_dir)
            }
        }

    def save_yaml(self, path: Optional[Path] = None):
        """Save current configuration to a YAML file."""
        if path is None:
            path = self.state_dir / "config_snapshot.yaml"
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

    @classmethod
    def load_yaml(cls, path: Path) -> "Config":
        """Load configuration from a YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        # Map YAML keys to dataclass fields
        config = cls()
        if "training_years" in data:
            start, end = map(int, data["training_years"].split("-"))
            config.training_start_year = start
            config.training_end_year = end
        if "test_years" in data:
            start, end = map(int, data["test_years"].split("-"))
            config.test_start_year = start
            config.test_end_year = end
        
        if "percentile_threshold" in data:
            config.percentile_threshold = float(data["percentile_threshold"])
        if "wall_clock_budget_seconds" in data:
            config.wall_clock_budget_seconds = int(data["wall_clock_budget_seconds"])
        if "seed" in data:
            config.seed = int(data["seed"])
        
        config._apply_env_overrides()
        return config

# Global singleton instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the global configuration singleton.
    Creates it if it doesn't exist, or loads from existing state if available.
    """
    global _config_instance
    if _config_instance is None:
        state_config_path = Path(__file__).parent.parent.parent / "state" / "config_snapshot.yaml"
        if state_config_path.exists():
            _config_instance = Config.load_yaml(state_config_path)
        else:
            _config_instance = Config()
    return _config_instance

def set_config(config: Config):
    """Set the global configuration singleton (useful for testing)."""
    global _config_instance
    _config_instance = config

if __name__ == "__main__":
    # Simple test to ensure config loads and paths are valid
    cfg = get_config()
    print(f"Config loaded successfully.")
    print(f"Project Root: {cfg.project_root}")
    print(f"Data Raw Dir: {cfg.data_raw_dir}")
    print(f"Budget: {cfg.wall_clock_budget_seconds}s")
    print(f"Seed: {cfg.seed}")
    cfg.save_yaml()
    print("Config saved to state/config_snapshot.yaml")
