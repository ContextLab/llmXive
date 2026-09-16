import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from logger import get_logger, info, warning, error

logger = get_logger(__name__)

@dataclass
class Config:
    """
    Centralized environment configuration for dataset paths and random seeds.
    This class manages paths for raw data, derived data, and output artifacts,
    as well as the global random seed for reproducibility.
    """
    # Project Root
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    
    # Data Paths
    data_raw_dir: Path = field(default_factory=lambda: Path("data/raw"))
    data_derived_dir: Path = field(default_factory=lambda: Path("data/derived"))
    data_figures_dir: Path = field(default_factory=lambda: Path("figures"))
    
    # Specific Dataset Files (relative to project root)
    synthetic_data_zip: str = "IL-Benchmark-local.zip"
    experimental_csv: str = "experimental_bulk_properties.csv"
    
    # Output Paths
    raw_energies_csv: str = "data/derived/raw_energies.csv"
    scaling_results_file: str = "scaling_factor.txt"
    correlation_results_csv: str = "data/derived/correlation_results.csv"
    benchmark_report_md: str = "docs/benchmark_report.md"
    correlation_report_md: str = "docs/correlation_report.md"
    review_response_md: str = "docs/review_response.md"
    
    # Reproducibility
    random_seed: int = 42
    
    # Execution Settings
    psi4_threads: int = 2
    psi4_memory_gb: float = 4.0
    bootstrap_replicates: int = 1000
    
    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path string to an absolute Path object."""
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return self.project_root / path

    def ensure_directories(self) -> None:
        """Ensure all required data and output directories exist."""
        dirs_to_create = [
            self.project_root / self.data_raw_dir,
            self.project_root / self.data_derived_dir,
            self.project_root / self.data_figures_dir,
            self.project_root / "docs",
        ]
        for d in dirs_to_create:
            d.mkdir(parents=True, exist_ok=True)
            info(f"Ensured directory: {d}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to a dictionary for JSON export."""
        return {
            "project_root": str(self.project_root),
            "data_raw_dir": str(self.data_raw_dir),
            "data_derived_dir": str(self.data_derived_dir),
            "data_figures_dir": str(self.data_figures_dir),
            "synthetic_data_zip": self.synthetic_data_zip,
            "experimental_csv": self.experimental_csv,
            "raw_energies_csv": self.raw_energies_csv,
            "scaling_results_file": self.scaling_results_file,
            "correlation_results_csv": self.correlation_results_csv,
            "benchmark_report_md": self.benchmark_report_md,
            "correlation_report_md": self.correlation_report_md,
            "review_response_md": self.review_response_md,
            "random_seed": self.random_seed,
            "psi4_threads": self.psi4_threads,
            "psi4_memory_gb": self.psi4_memory_gb,
            "bootstrap_replicates": self.bootstrap_replicates,
        }

_config_instance: Optional[Config] = None

def load_config_from_env() -> Config:
    """
    Load configuration from environment variables, falling back to defaults.
    Expected env vars:
      - PROJ_DATA_RAW_DIR
      - PROJ_DATA_DERIVED_DIR
      - PROJ_RANDOM_SEED
      - PROJ_BOOTSTRAP_REPLICATES
    """
    global _config_instance
    if _config_instance is not None:
        return _config_instance

    cfg = Config()
    
    if os.getenv("PROJ_DATA_RAW_DIR"):
        cfg.data_raw_dir = Path(os.getenv("PROJ_DATA_RAW_DIR"))
    if os.getenv("PROJ_DATA_DERIVED_DIR"):
        cfg.data_derived_dir = Path(os.getenv("PROJ_DATA_DERIVED_DIR"))
    
    seed_str = os.getenv("PROJ_RANDOM_SEED")
    if seed_str:
        try:
            cfg.random_seed = int(seed_str)
        except ValueError:
            warning(f"Invalid PROJ_RANDOM_SEED '{seed_str}', using default {cfg.random_seed}")
    
    reps_str = os.getenv("PROJ_BOOTSTRAP_REPLICATES")
    if reps_str:
        try:
            cfg.bootstrap_replicates = int(reps_str)
        except ValueError:
            warning(f"Invalid PROJ_BOOTSTRAP_REPLICATES '{reps_str}', using default {cfg.bootstrap_replicates}")

    _config_instance = cfg
    info(f"Configuration loaded from environment. Seed: {cfg.random_seed}")
    return cfg

def save_config_to_json(config: Config, output_path: Optional[str] = None) -> Path:
    """Save the current configuration to a JSON file."""
    if output_path is None:
        output_path = str(config.project_root / "config_export.json")
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(config.to_dict(), f, indent=2)
    
    info(f"Configuration saved to {path}")
    return path

def load_config_from_json(input_path: str) -> Config:
    """Load configuration from a JSON file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    cfg = Config()
    # Basic restoration (ignoring complex Path logic for simplicity in reload)
    if "random_seed" in data:
        cfg.random_seed = data["random_seed"]
    if "bootstrap_replicates" in data:
        cfg.bootstrap_replicates = data["bootstrap_replicates"]
    
    # Re-construct paths if provided as strings, otherwise keep defaults
    # Note: This is a simplified loader. Full restoration requires project_root context.
    info(f"Configuration loaded from {path}")
    return cfg

def get_config() -> Config:
    """Get the singleton configuration instance, loading from env if necessary."""
    if _config_instance is None:
        return load_config_from_env()
    return _config_instance

def set_config(cfg: Config) -> None:
    """Set the global configuration instance."""
    global _config_instance
    _config_instance = cfg
    info("Configuration instance set manually.")

def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed in the global config and return it.
    If seed is None, uses the current config value.
    """
    cfg = get_config()
    if seed is not None:
        cfg.random_seed = seed
        info(f"Random seed set to {seed}")
    return cfg.random_seed

def main():
    """CLI entry point to print current configuration."""
    cfg = load_config_from_env()
    print("Current Configuration:")
    print(json.dumps(cfg.to_dict(), indent=2))
    cfg.ensure_directories()

if __name__ == "__main__":
    main()
