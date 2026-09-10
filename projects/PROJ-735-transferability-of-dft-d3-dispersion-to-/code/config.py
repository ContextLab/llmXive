"""
Environment configuration management for dataset paths and random seeds.

This module centralizes all configuration settings required for the research pipeline,
including dataset paths, random seeds for reproducibility, and environment variables.
"""

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
    Centralized configuration container for the DFT-D3 transferability study.

    Attributes:
        project_root (Path): Root directory of the project.
        data_root (Path): Root directory for all data files.
        raw_data_dir (Path): Directory containing raw input data.
        derived_data_dir (Path): Directory for processed/derived data.
        output_dir (Path): Directory for script outputs and reports.
        random_seed (int): Global random seed for reproducibility.
        n_jobs (int): Number of parallel jobs for computation.
        psi4_memory (str): Memory allocation for Psi4 calculations (e.g., '2GB').
        bootstrap_replicates (int): Number of bootstrap replicates for statistical analysis.
        checksum_file (Path): Path to the checksums validation file.
        synthetic_data_zip (Path): Path to the synthetic local fallback dataset.
        experimental_bulk_csv (Path): Path to experimental bulk properties CSV.
        raw_energies_csv (Path): Output path for raw energy results.
        scaling_results_json (Path): Output path for scaling factor results.
        correlation_results_json (Path): Output path for correlation analysis results.
        benchmark_report_md (Path): Output path for benchmark report.
        correlation_report_md (Path): Output path for correlation report.
    """
    project_root: Path
    data_root: Path
    raw_data_dir: Path
    derived_data_dir: Path
    output_dir: Path
    random_seed: int
    n_jobs: int = 1
    psi4_memory: str = "2GB"
    bootstrap_replicates: int = 1000
    checksum_file: Path = field(init=False)
    synthetic_data_zip: Path = field(init=False)
    experimental_bulk_csv: Path = field(init=False)
    raw_energies_csv: Path = field(init=False)
    scaling_results_json: Path = field(init=False)
    correlation_results_json: Path = field(init=False)
    benchmark_report_md: Path = field(init=False)
    correlation_report_md: Path = field(init=False)

    def __post_init__(self):
        """Initialize derived paths based on root directories."""
        self.checksum_file = self.raw_data_dir / "checksums.json"
        self.synthetic_data_zip = self.raw_data_dir / "IL-Benchmark-local.zip"
        self.experimental_bulk_csv = self.raw_data_dir / "experimental_bulk_properties.csv"
        self.raw_energies_csv = self.derived_data_dir / "raw_energies.csv"
        self.scaling_results_json = self.derived_data_dir / "scaling_results.json"
        self.correlation_results_json = self.derived_data_dir / "correlation_results.json"
        self.benchmark_report_md = self.output_dir / "benchmark_report.md"
        self.correlation_report_md = self.output_dir / "correlation_report.md"

        # Validate critical directories exist
        for dir_path in [self.raw_data_dir, self.derived_data_dir, self.output_dir]:
            if not dir_path.exists():
                warning(f"Directory does not exist: {dir_path}. Creating it now.")
                dir_path.mkdir(parents=True, exist_ok=True)


def load_config_from_env() -> Config:
    """
    Load configuration from environment variables with sensible defaults.

    Returns:
        Config: A populated configuration object.
    """
    project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
    data_root = Path(os.getenv("DATA_ROOT", project_root / "data"))
    raw_data_dir = Path(os.getenv("RAW_DATA_DIR", data_root / "raw"))
    derived_data_dir = Path(os.getenv("DERIVED_DATA_DIR", data_root / "derived"))
    output_dir = Path(os.getenv("OUTPUT_DIR", project_root / "data" / "output"))
    
    random_seed = int(os.getenv("RANDOM_SEED", "42"))
    n_jobs = int(os.getenv("N_JOBS", "1"))
    psi4_memory = os.getenv("PSI4_MEMORY", "2GB")
    bootstrap_replicates = int(os.getenv("BOOTSTRAP_REPLICATES", "1000"))

    logger.info(f"Loading configuration from environment. Project root: {project_root}")
    logger.info(f"Data root: {data_root}, Random seed: {random_seed}")

    return Config(
        project_root=project_root,
        data_root=data_root,
        raw_data_dir=raw_data_dir,
        derived_data_dir=derived_data_dir,
        output_dir=output_dir,
        random_seed=random_seed,
        n_jobs=n_jobs,
        psi4_memory=psi4_memory,
        bootstrap_replicates=bootstrap_replicates
    )


def save_config_to_json(config: Config, output_path: Optional[Path] = None) -> Path:
    """
    Save the current configuration to a JSON file for reproducibility.

    Args:
        config: The configuration object to save.
        output_path: Optional path to save the file. Defaults to project_root/config.json.

    Returns:
        Path: The path where the configuration was saved.
    """
    if output_path is None:
        output_path = config.project_root / "config.json"

    config_dict = {
        "project_root": str(config.project_root),
        "data_root": str(config.data_root),
        "raw_data_dir": str(config.raw_data_dir),
        "derived_data_dir": str(config.derived_data_dir),
        "output_dir": str(config.output_dir),
        "random_seed": config.random_seed,
        "n_jobs": config.n_jobs,
        "psi4_memory": config.psi4_memory,
        "bootstrap_replicates": config.bootstrap_replicates,
        "paths": {
            "checksum_file": str(config.checksum_file),
            "synthetic_data_zip": str(config.synthetic_data_zip),
            "experimental_bulk_csv": str(config.experimental_bulk_csv),
            "raw_energies_csv": str(config.raw_energies_csv),
            "scaling_results_json": str(config.scaling_results_json),
            "correlation_results_json": str(config.correlation_results_json),
            "benchmark_report_md": str(config.benchmark_report_md),
            "correlation_report_md": str(config.correlation_report_md),
        }
    }

    with open(output_path, 'w') as f:
        json.dump(config_dict, f, indent=2)

    info(f"Configuration saved to {output_path}")
    return output_path


def load_config_from_json(input_path: Path) -> Config:
    """
    Load configuration from a JSON file.

    Args:
        input_path: Path to the JSON configuration file.

    Returns:
        Config: The loaded configuration object.
    """
    if not input_path.exists():
        error(f"Configuration file not found: {input_path}")
        raise FileNotFoundError(f"Configuration file not found: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    # Reconstruct paths
    config = Config(
        project_root=Path(data["project_root"]),
        data_root=Path(data["data_root"]),
        raw_data_dir=Path(data["raw_data_dir"]),
        derived_data_dir=Path(data["derived_data_dir"]),
        output_dir=Path(data["output_dir"]),
        random_seed=data["random_seed"],
        n_jobs=data.get("n_jobs", 1),
        psi4_memory=data.get("psi4_memory", "2GB"),
        bootstrap_replicates=data.get("bootstrap_replicates", 1000)
    )

    info(f"Configuration loaded from {input_path}")
    return config


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance. Initializes it if not already set.

    Returns:
        Config: The global configuration object.
    """
    global _config
    if _config is None:
        _config = load_config_from_env()
    return _config


def set_config(config: Config) -> None:
    """
    Set the global configuration instance.

    Args:
        config: The configuration object to set as global.
    """
    global _config
    _config = config
    info("Global configuration updated.")


def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set the global random seed for reproducibility.
    Updates the global config if a seed is provided, otherwise uses the config's seed.

    Args:
        seed: Optional seed value. If None, uses the value from the global config.
    """
    import random
    import numpy as np

    if seed is None:
        seed = get_config().random_seed

    random.seed(seed)
    np.random.seed(seed)
    info(f"Random seed set to {seed}")


def main() -> None:
    """
    Main entry point to demonstrate configuration loading and saving.
    """
    config = load_config_from_env()
    info(f"Project Root: {config.project_root}")
    info(f"Data Root: {config.data_root}")
    info(f"Raw Data Dir: {config.raw_data_dir}")
    info(f"Derived Data Dir: {config.derived_data_dir}")
    info(f"Random Seed: {config.random_seed}")
    
    # Save configuration
    save_path = save_config_to_json(config)
    info(f"Configuration saved to: {save_path}")

    # Verify loading
    loaded_config = load_config_from_json(save_path)
    assert loaded_config.random_seed == config.random_seed
    assert str(loaded_config.raw_energies_csv) == str(config.raw_energies_csv)
    info("Configuration round-trip verification successful.")


if __name__ == "__main__":
    main()